# Rule 08: The Invariant Solvency Gate (Cost Guard)
1. **Blocking Gate**: You strictly CANNOT proceed from PLAN_APPROVED to BUILDING without a passed `cost_validation` check.
2. **Budget Cap**: If (Projected Cost + Current Spend) > Monthly Cap, STOP and trigger Insolvency Protocol.
3. **Lease Model**: You must acquire a logical "Budget Lease" from the Redis instance before spinning up resources.
4. **Resolution**: If blocked, you must either (A) Optimize the plan (lower tier) or (B) Request Human Override via Jira.
