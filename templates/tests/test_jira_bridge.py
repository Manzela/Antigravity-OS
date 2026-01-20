import unittest
import sys
import os
import json

# Add path to find jira_bridge in templates/observability
current_dir = os.path.dirname(os.path.abspath(__file__))
bridge_path = os.path.abspath(os.path.join(current_dir, "../observability"))
sys.path.append(bridge_path)

try:
    import jira_bridge
except ImportError:
    # Fallback if running from different context
    sys.path.append(os.path.abspath("templates/observability"))
    import jira_bridge

class TestJiraBridge(unittest.TestCase):
    def test_construct_flight_recorder_payload(self):
        """Test R 6.5 Schema Compliance"""
        trace_id = "test-trace-123"
        git_hash = "abc1234"
        logs = "Critical failure in engine"
        owner = "jane.doe@example.com"
        
        payload = jira_bridge.construct_flight_recorder_payload(
            trace_id, git_hash, logs, owner, status_code="Critical"
        )
        
        # Level 1: Key Existence
        self.assertIn("trace_id", payload)
        self.assertIn("span_id", payload)
        self.assertIn("resource", payload)
        self.assertIn("logs", payload)
        
        # Level 2: Value Correctness
        self.assertEqual(payload["trace_id"], trace_id)
        self.assertEqual(payload["status"]["code"], "Critical")
        self.assertEqual(payload["resource"]["vcs.revision.id"], git_hash)
        self.assertEqual(payload["attributes"]["owner"], owner)
        
        # Level 3: Structure
        self.assertIsInstance(payload["logs"], list)
        self.assertEqual(payload["logs"][0]["body"], logs)
        self.assertEqual(payload["logs"][0]["severity"], "ERROR")

if __name__ == "__main__":
    unittest.main()
