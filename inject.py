# inject.py
import requests, time, random
URL = "http://127.0.0.1:5000/score"
flow = {
    "flow_id": f"manual-{int(time.time()*1000)}",
    "src": "10.0.0.5",
    "dst": "192.168.1.1",
    "dport": 80,
    "proto": "TCP",
    "score": 0.95,
    "prediction": "dos",
}
print(requests.post(URL, json=flow).text)
