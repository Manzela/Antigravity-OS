# Rule 02: Fail Closed
1. **Build Integrity**: If the build fails, STOP. Do not force it.
2. **Linter Gate**: Code must pass strict linting rules.
3. **Validation**: UI must handle schema validation failures gracefully.
