import time, random, requests

URL = "http://127.0.0.1:5000/score"

def fake_flow():
    return {
        "flow_id": f"dos-{int(time.time()*1000)}",
        "src": f"10.0.0.{random.randint(2,250)}",
        "dst": "192.168.1.1",
        "dport": random.choice([80,443,8080,22]),
        "proto": "TCP",
        "score": round(random.uniform(0.8,1.0),2),
        "prediction": "dos"
    }

print("DoS simulator started (local, safe). Ctrl+C to stop.")
try:
    while True:
        for _ in range(5):  # burst
            try: requests.post(URL, json=fake_flow(), timeout=1)
            except: pass
        time.sleep(0.4)
except KeyboardInterrupt:
    print("DoS simulator stopped.")