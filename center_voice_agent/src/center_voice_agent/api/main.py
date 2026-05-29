"""Запуск: uvicorn center_voice_agent.api.app:app --reload"""

from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="HTTP API center_voice_agent")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    try:
        import uvicorn
    except ImportError as e:
        raise SystemExit(
            'Установите API-зависимости: pip install -e ".[api]"'
        ) from e
    uvicorn.run(
        "center_voice_agent.api.app:app",
        host=args.host,
        port=args.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
