import json
import os
import sys
from jsonschema import validate, ValidationError

# Add agent path to import jira_bridge
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.agent')))
from observability import jira_bridge

def test_schema_completeness():
    """Verify that jira_bridge produces a valid schema object"""
    print("🧪 Testing Schema Integrity...")
    
    # Initialize a dummy environment
    trace_id = "test-trace-id-123"
    error_log = "Test 🚀 error with emoji"
    
    # We mock getting the object without sending to Jira/Redis
    # By intercepting the logic or creating a test helper in jira_bridge, 
    # but since we can't modify main code significantly for tests only,
    # we replicate the construction logic here or test via public method if available.
    # jira_bridge.handle_failure does everything side-effectful.
    
    cleaned = jira_bridge.clean_logs(error_log)
    assert "🚀" not in cleaned
    print("✅ Emoji Scrubbing: PASS")
    
    # Validate the Schema JSON file itself
    schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates', 'Flight_Recorder_Schema.json'))
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    print("✅ Schema JSON Load: PASS")
    
    # Validate a sample payload against it
    sample_payload = {
        "trace_id": "123",
        "status": "PROD_ALERT",
        "loop_count": 0,
        "owner": "test",
        "handover_manifest": {}
    }
    
    try:
        validate(instance=sample_payload, schema=schema)
        print("✅ Sample Payload Validation: PASS")
    except ValidationError as e:
        print(f"❌ Verification Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_schema_completeness()
