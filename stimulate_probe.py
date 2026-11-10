# stimulate_probe.py
import time, random, requests
URL = "http://127.0.0.1:5000/score"

def fake_flow():
    return {
        "flow_id": f"probe-{int(time.time()*1000)}",
        "src": f"10.0.0.{random.randint(2,250)}",
        "dst": "192.168.1.1",
        "dport": random.randint(1,1024),
        "proto": "UDP",
        "score": round(random.uniform(0.6,0.9),2),
        "prediction": "probe"
    }

print("Probe simulator started (local, safe). Ctrl+C to stop.")
try:
    while True:
        try: requests.post(URL, json=fake_flow(), timeout=1)
        except: pass
        time.sleep(0.15)
except KeyboardInterrupt:
    print("Probe simulator stopped.")
