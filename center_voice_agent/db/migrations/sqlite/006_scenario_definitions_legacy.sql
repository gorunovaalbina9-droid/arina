-- Legacy: scenario_definitions из 001 не используется кодом (активна scenario_publish).
ALTER TABLE scenario_definitions RENAME TO scenario_definitions_legacy;
