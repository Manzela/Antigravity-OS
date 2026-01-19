# Rule 05: Flight Recorder Protocol
1. **State Persistence**: Every response must start with the JSON Flight Recorder block defined in `docs/Flight_Recorder_Schema.json`.
2. **Context Passing**: Read `trace_id` and `handover_manifest` from the previous turn.
