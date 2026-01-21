package antigravity.governance
default allow = false
default skip_gates = false

# PROTOCOL F: False Positive Mitigation
# Skip gates if the commit touches ONLY documentation.
skip_gates if {
    count(input.files) > 0
    every file in input.files {
        is_safe(file)
    }
}
is_safe(path) if { startswith(path, "docs/") }
is_safe(path) if { endswith(path, ".md") }

# --- NEW: IMMUTABLE KERNEL PROTECTION ---
# Deny any change to the Flight Recorder Schema or Bridge Code
deny[msg] {
    some file in input.files
    is_immutable_kernel(file)
    msg := sprintf("⛔ BLOCK: Attempted to modify Immutable Kernel file: %v. This file is READ-ONLY.", [file])
}

# Define the list of "Untouchable" files
is_immutable_kernel(path) { endswith(path, "Flight_Recorder_Schema.json") }
is_immutable_kernel(path) { contains(path, "observability/jira_bridge.py") }
is_immutable_kernel(path) { startswith(path, ".agent/rules/") }
is_immutable_kernel(path) { startswith(path, ".agent/policies/") }
