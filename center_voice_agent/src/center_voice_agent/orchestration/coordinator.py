from __future__ import annotations

from typing import Optional

import structlog

from center_voice_agent.agent.gateway import AgentGateway, AgentTurnResult
from center_voice_agent.context.short_term import ShortTermMemory
from center_voice_agent.context.short_term_factory import persist_turn_messages
from center_voice_agent.logging_setup import log_security_incident
from center_voice_agent.modes.commands import load_mode_commands, try_parse_mode_switch
from center_voice_agent.modes.registry import ModeRegistry
from center_voice_agent.security.moderation import check_input_blocked, check_output_blocked
from center_voice_agent.security.rate_limit import RateLimiter, get_default_rate_limiter
from center_voice_agent.scenarios.graph_engine import ScenarioRuntime
from center_voice_agent.scenarios.loader import load_scenario_graph_unified
from center_voice_agent.scenarios.phrases import load_scenario_commands, try_parse_scenario_reset
from center_voice_agent.session.repo import SessionRow
from center_voice_agent.settings import Settings, get_settings

log = structlog.get_logger(__name__)


class SessionCoordinator:
    """
    Слой над шлюзом: сессия в БД, смена режима по фразам, сценарий из БД + YAML,
    сброс сценария по фразам из config/voice/scenario_commands.yaml.
    """

    def __init__(
        self,
        gateway: AgentGateway,
        *,
        settings: Optional[Settings] = None,
        mode_registry: Optional[ModeRegistry] = None,
        rate_limiter: Optional[RateLimiter] = None,
    ) -> None:
        self.gateway = gateway
        self.settings = settings or get_settings()
        self._modes = mode_registry or gateway.modes
        self._rate_limiter = rate_limiter or get_default_rate_limiter()
        self._commands_path = self.settings.voice_commands_path
        self._scenario_commands_path = self.settings.scenario_commands_path

    def _voice_alias_map(self) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for mid, mode in self._modes.get_all().items():
            if mode.voice_aliases:
                out[mid] = list(mode.voice_aliases)
        return out

    def _allowed(self, current: str, target: str) -> bool:
        if current == target:
            return False
        mode = self._modes.get(current)
        if not mode.allowed_transitions:
            return target in self._modes.list_ids()
        return target in mode.allowed_transitions

    def _resolve_scenario_runtime(
        self,
        *,
        scenario: Optional[ScenarioRuntime],
        row: SessionRow,
    ) -> Optional[ScenarioRuntime]:
        if scenario is not None:
            return scenario
        if row.scenario_id:
            graph = load_scenario_graph_unified(
                self.settings.scenarios_dir,
                row.scenario_id,
                database_url=self.settings.database_url,
                scenarios_source=self.settings.scenarios_source,
                scenarios_center_id=self.settings.scenarios_center_id,
            )
            return ScenarioRuntime.resume(graph, row.scenario_node_id)
        return None

    async def _persist_short_term_turn(
        self,
        session_id: str,
        user_text: str,
        assistant_text: str,
    ) -> None:
        await persist_turn_messages(
            session_id,
            user_text,
            assistant_text,
            settings=self.settings,
            messages_repo=self.gateway.session_messages_repository,
        )

    async def _persist_scenario_pointer(
        self,
        session_id: str,
        scenario_rt: Optional[ScenarioRuntime],
    ) -> None:
        if scenario_rt is None:
            return
        await self.gateway.session_repository.update_scenario_pointer(
            session_id,
            scenario_id=scenario_rt.graph.id,
            scenario_node_id=scenario_rt.current_node_id,
        )

    async def handle_user_turn(
        self,
        *,
        session_id: str,
        child_profile_id: str,
        user_text: str,
        short_term: ShortTermMemory,
        scenario: Optional[ScenarioRuntime] = None,
        long_term_summary: Optional[str] = None,
        age_band: Optional[str] = None,
    ) -> AgentTurnResult:
        repo = self.gateway.session_repository
        default_mode = self.settings.default_mode_id
        await repo.ensure(session_id, child_profile_id, default_mode_id=default_mode)
        await self.gateway.memory_repository.ensure_child_profile(child_profile_id)
        row = await repo.get(session_id)
        assert row is not None
        current = row.mode_id

        if self.settings.rate_limit_enabled:
            rl = self._rate_limiter.check(
                session_id,
                per_minute=self.settings.rate_limit_per_minute,
                per_hour=self.settings.rate_limit_per_hour,
            )
            if rl:
                log_security_incident(
                    reason=rl,
                    session_id=session_id,
                    child_profile_id=child_profile_id,
                    direction="rate_limit",
                )
                msg = "Подожди немного — слишком много сообщений подряд. Попробуй через минуту."
                short_term.append_user(user_text)
                short_term.append_assistant(msg)
                await self._persist_short_term_turn(session_id, user_text, msg)
                return AgentTurnResult(
                    text=msg,
                    reply_spoken=msg,
                    mode_id=current,
                    scenario_id=row.scenario_id,
                    scenario_node_id=row.scenario_node_id,
                    tool_calls=[],
                )

        blocked_in = self.settings.moderation_blocked_input_substrings
        blocked_out = self.settings.moderation_blocked_output_substrings
        if self.settings.moderation_enabled:
            blocked = check_input_blocked(user_text, blocked=blocked_in)
            if blocked:
                log_security_incident(
                    reason=blocked,
                    session_id=session_id,
                    child_profile_id=child_profile_id,
                    direction="input",
                )
                msg = "Давай поговорим о чём-нибудь другом — я не могу ответить на такой запрос."
                short_term.append_user(user_text)
                short_term.append_assistant(msg)
                await self._persist_short_term_turn(session_id, user_text, msg)
                return AgentTurnResult(
                    text=msg,
                    reply_spoken=msg,
                    mode_id=current,
                    scenario_id=row.scenario_id,
                    scenario_node_id=row.scenario_node_id,
                    tool_calls=[],
                )

        scenario_rt = self._resolve_scenario_runtime(scenario=scenario, row=row)
        scen_cmds = load_scenario_commands(self._scenario_commands_path)

        cmds = load_mode_commands(self._commands_path)
        target = try_parse_mode_switch(user_text, commands=cmds, voice_aliases=self._voice_alias_map())
        if target == current:
            target = None

        if target is not None:
            if not self._allowed(current, target):
                log.info(
                    "mode_switch_denied",
                    session_id=session_id,
                    from_mode=current,
                    to_mode=target,
                )
                cur_name = self._modes.get(current).display_name
                tgt_name = self._modes.get(target).display_name
                msg = (
                    f"Сейчас нельзя перейти в «{tgt_name}» из режима «{cur_name}». "
                    "Давай продолжим здесь — просто скажи, что хочешь."
                )
                short_term.append_user(user_text)
                short_term.append_assistant(msg)
                await self._persist_short_term_turn(session_id, user_text, msg)
                await self._persist_scenario_pointer(session_id, scenario_rt)
                return AgentTurnResult(
                    text=msg,
                    reply_spoken=msg,
                    mode_id=current,
                    scenario_id=row.scenario_id,
                    scenario_node_id=row.scenario_node_id,
                    tool_calls=[],
                )

            prev = current
            await repo.set_mode(session_id, target)
            new_mode = self._modes.get(target)
            msg = f"Переключилась в режим «{new_mode.display_name}». Можешь говорить дальше."
            log.info(
                "mode_changed",
                session_id=session_id,
                previous_mode_id=prev,
                mode_id=target,
            )
            short_term.append_user(user_text)
            short_term.append_assistant(msg)
            await self._persist_short_term_turn(session_id, user_text, msg)
            await self._persist_scenario_pointer(session_id, scenario_rt)
            return AgentTurnResult(
                text=msg,
                reply_spoken=msg,
                mode_id=target,
                scenario_id=scenario_rt.graph.id if scenario_rt else None,
                scenario_node_id=scenario_rt.current_node_id if scenario_rt else None,
                tool_calls=[],
                mode_changed=True,
                previous_mode_id=prev,
            )

        skip_advance = False
        if scenario_rt is not None and try_parse_scenario_reset(user_text, commands=scen_cmds):
            scenario_rt.apply_interrupt()
            await self._persist_scenario_pointer(session_id, scenario_rt)
            skip_advance = True

        if scenario_rt is not None and not skip_advance:
            if scenario_rt.advance_on_user_text(user_text):
                await self._persist_scenario_pointer(session_id, scenario_rt)

        out = await self.gateway.run_turn(
            session_id=session_id,
            child_profile_id=child_profile_id,
            mode_id=current,
            user_text=user_text,
            short_term=short_term,
            scenario=scenario_rt,
            long_term_summary=long_term_summary,
            age_band=age_band,
            skip_scenario_advance=skip_advance,
        )
        await self._persist_scenario_pointer(session_id, scenario_rt)
        if self.settings.moderation_enabled:
            ob = check_output_blocked(out.text, blocked=blocked_out)
            if ob:
                log_security_incident(
                    reason=ob,
                    session_id=session_id,
                    child_profile_id=child_profile_id,
                    direction="output",
                )
                safe = "Извини, я не могу так ответить. Давай сменим тему."
                out = AgentTurnResult(
                    text=safe,
                    reply_spoken=safe,
                    mode_id=out.mode_id,
                    scenario_id=out.scenario_id,
                    scenario_node_id=out.scenario_node_id,
                    tool_calls=out.tool_calls,
                    mode_changed=out.mode_changed,
                    previous_mode_id=out.previous_mode_id,
                )
        reply = (out.reply_spoken or out.text or "").strip()
        await self._persist_short_term_turn(session_id, user_text, reply)
        return out
