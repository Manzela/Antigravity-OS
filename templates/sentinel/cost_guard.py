import os
import sys
import argparse
import json
import time

# Antigravity Cost Guard (Rule 08)
# Blocks execution if solvency is not guaranteed.
# Implements Requirements R 1.1, R 1.2, R 1.3, R 1.4

MONTHLY_CAP = 50.00
CURRENT_SPEND = 12.50 # Default fail-safe

TIER_PRICING = {
    "standard_cpu": 1.00, # Base unit price (treated as $1/unit for simplify if just passing dollar amount)
    "nvidia_l4": 2.50,
    "nvidia_a100": 8.00
}

CONFIG_PATH = os.path.expanduser("~/.antigravity/config")

def load_global_config():
    """R 1.4 Persistent Reconciliation: Load config from ~/.antigravity/config"""
    global MONTHLY_CAP, CURRENT_SPEND
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
                MONTHLY_CAP = config.get("monthly_cap", MONTHLY_CAP)
                CURRENT_SPEND = config.get("current_spend", CURRENT_SPEND)
                print(f"[INFO] Loaded Global Config: Cap=${MONTHLY_CAP}, Spend=${CURRENT_SPEND}")
        except Exception as e:
            print(f"[WARN] Failed to load config: {e}")
    else:
        print("[INFO] No Global Config found. Using Defaults.")

class MockRedis:
    """R 1.3 Budget Lease Model: Mock interface for Redis"""
    def __init__(self):
        print("[INFO] Connecting to Redis (Mock)...")
        self.connected = True
    
    def set(self, key, value, ex=None):
        print(f"[REDIS] SET {key} = {value} (EX={ex})")
        return True

def check_solvency(projected_cost_units, tier):
    """R 1.1 + R 1.2: Hardware-Aware Solvency Check"""
    load_global_config()
    
    # If using 'standard_cpu', we assume the input is effectively usage units or raw dollars if priced at 1.0
    # The requirement asks for distinction.
    # In the CI workflow, we pass "15.00". If we consider that "Units", then the Cost = 15.00 * Price.
    rate = TIER_PRICING.get(tier)
    if not rate:
        print(f"[ERROR] Invalid Hardware Tier: {tier}. Available: {list(TIER_PRICING.keys())}")
        sys.exit(1)
        
    projected_cost = float(projected_cost_units) * rate
    total = CURRENT_SPEND + projected_cost
    
    print(f"[AUDIT] Tier: {tier} (${rate}/unit) * {projected_cost_units} units = ${projected_cost:.2f}")
    
    if total > MONTHLY_CAP:
        print(f"[BLOCK] Insolvency Triggered! Total ${total:.2f} > Cap ${MONTHLY_CAP:.2f}")
        print("Protocol: Request Override or Optimize Plan.")
        sys.exit(1)
    else:
        print(f"[PASS] Solvency Validated. Margin: ${MONTHLY_CAP - total:.2f}")
        
        # R 1.3: Acquire Lease
        r = MockRedis()
        lease_id = "lg-" + os.urandom(4).hex()
        r.set(f"lease:{lease_id}", projected_cost, ex=3600)
        print(f"LEASE_TOKEN: {lease_id}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Antigravity Cost Guard")
    parser.add_argument("units", type=float, help="Projected units (hours/ops) or raw cost")
    parser.add_argument("--tier", default="standard_cpu", choices=TIER_PRICING.keys(), help="Hardware Tier")
    
    args = parser.parse_args()
    
    check_solvency(args.units, args.tier)
