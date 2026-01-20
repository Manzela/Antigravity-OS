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
        """Test R 6.5 Schema Compliance (Flight Recorder)"""
        trace_id = "test-trace-123"
        git_hash = "abc1234"
        logs = "Critical failure in engine"
        owner = "jane.doe@example.com"
        
        payload = jira_bridge.construct_flight_recorder_payload(
            trace_id, git_hash, logs, owner, status_code="Critical"
        )
        
        # Level 1: Key Existence
        self.assertIn("trace_id", payload)
        self.assertIn("resource", payload)
        self.assertIn("logs", payload)
        
        # Level 2: Value Correctness
        self.assertEqual(payload["trace_id"], trace_id)
        self.assertEqual(payload["status"]["code"], "Critical")
        self.assertEqual(payload["resource"]["vcs.revision.id"], git_hash)

    def test_create_rich_description_adf_compliance(self):
        """Test 2026 Governance Standards: ADF Tables & Interactive Checklists"""
        
        # Mock Context Data
        summary = "Fix Critical Build Failure"
        description = "Blocking the release pipeline."
        log_content = "SyntaxError: invalid syntax"
        owner_name = "DevOps Lead"
        owner_email = "lead@example.com"
        fingerprint = "a1b2c3d4"
        gcs_link = "https://storage.cloud.google.com/logs/trace.json"
        
        env_info = {
            "OS": "Linux 5.4.0",
            "Python": "3.10.1",
            "Git Branch": "main",
            "Git Commit": "ff0022",
            "CI Context": "Local"
        }
        repro_cmd = "git checkout ff0022 && ./run_tests.sh"

        # Execute
        doc = jira_bridge.create_rich_description(
            summary, description, log_content, owner_name, owner_email, 
            fingerprint, gcs_link, env_info, repro_cmd
        )

        # --- Verification ---

        # 1. Root Document Structure
        self.assertEqual(doc["type"], "doc")
        self.assertEqual(doc["version"], 1)
        self.assertIsInstance(doc["content"], list)

        # 2. Extract Content Types for Analysis
        content_nodes = [node["type"] for node in doc["content"]]

        # 3. Governance Metadata Table (Must be present)
        # We expect at least two tables: Governance & Environment
        self.assertIn("table", content_nodes)
        table_count = content_nodes.count("table")
        self.assertTrue(table_count >= 2, f"Expected at least 2 tables (Gov + Env), found {table_count}")

        # 4. Interactive Acceptance Criteria (Must be a TaskList)
        self.assertIn("taskList", content_nodes)
        
        # 5. Reproduction Command (Must be a CodeBlock)
        self.assertIn("codeBlock", content_nodes)

        # 6. Safety Check: Verify JSON Serialization
        # Jira API will reject the request if this fails
        try:
            json_str = json.dumps(doc)
            self.assertTrue(len(json_str) > 0)
        except Exception as e:
            self.fail(f"ADF Document failed JSON serialization: {e}")

if __name__ == "__main__":
    unittest.main()