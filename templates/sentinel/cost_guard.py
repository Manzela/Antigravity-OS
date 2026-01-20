import os
import sys

# Antigravity Cost Guard (Rule 08)
# Blocks execution if solvency is not guaranteed.

MONTHLY_CAP = 50.00
CURRENT_SPEND = 12.50 # Mock value, ideally fetched from GCP Billing

def check_solvency(projected_cost):
    total = CURRENT_SPEND + projected_cost
    if total > MONTHLY_CAP:
        print(f"[BLOCK] Insolvency Triggered! Total ${total} > Cap ${MONTHLY_CAP}")
        print("Protocol: Request Override or Optimize Plan.")
        sys.exit(1)
    else:
        print(f"[PASS] Solvency Validated. Margin: ${MONTHLY_CAP - total}")
        # Generate Lease Token
        print("LEASE_TOKEN: " + "lg-" + os.urandom(4).hex())

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cost_guard.py <projected_cost>")
        sys.exit(1)
    
    check_solvency(float(sys.argv[1]))
