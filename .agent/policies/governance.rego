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
