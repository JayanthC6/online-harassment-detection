import json
from app import app

def post(payload):
    client = app.test_client()
    response = client.post('/demo/analyze', json=payload)
    return response.status_code, response.get_data(as_text=True)

# Test 1: arbitrary example_id
status, body = post({"example_id": "hack_attempt"})
print(f"TEST 1 (arbitrary example_id 'hack_attempt'):")
print(f"  HTTP {status}: {body}")

# Test 2: free text field instead of example_id
status, body = post({"text": "you are hacked"})
print(f"\nTEST 2 (free text 'text' field, no example_id):")
print(f"  HTTP {status}: {body}")

# Test 3: valid example_id — confirm it actually runs
with app.app_context():
    status, body = post({"example_id": "threat_example"})
    parsed = json.loads(body) if status == 200 else {}
    print(f"\nTEST 3 (valid 'threat_example'):")
    print(f"  HTTP {status}")
    print(f"  primary_label: {parsed.get('primary_label')}")
    print(f"  severity: {parsed.get('severity')}")
    print(f"  guidance_snippet: {parsed.get('guidance_snippet')}")
    print(f"  actor_id logged: {parsed.get('actor_id')} (should be DemoVisitor, NOT written to DB)")

