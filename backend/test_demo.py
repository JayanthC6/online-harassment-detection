import urllib.request
import urllib.error
import json

base = "http://localhost:5000/demo/analyze"
headers = {"Content-Type": "application/json"}

def post(payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(base, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

# Test 1: arbitrary example_id
status, body = post({"example_id": "hack_attempt"})
print(f"TEST 1 (arbitrary example_id 'hack_attempt'):")
print(f"  HTTP {status}: {body}")

# Test 2: free text field instead of example_id
status, body = post({"text": "you are hacked"})
print(f"\nTEST 2 (free text 'text' field, no example_id):")
print(f"  HTTP {status}: {body}")

# Test 3: valid example_id — confirm it actually runs
status, body = post({"example_id": "threat_example"})
parsed = json.loads(body) if status == 200 else {}
print(f"\nTEST 3 (valid 'threat_example'):")
print(f"  HTTP {status}")
print(f"  primary_label: {parsed.get('primary_label')}")
print(f"  severity: {parsed.get('severity')}")
print(f"  guidance_snippet: {parsed.get('guidance_snippet')}")
print(f"  actor_id logged: {parsed.get('actor_id')} (should be DemoVisitor, NOT written to DB)")
