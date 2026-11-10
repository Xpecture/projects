# stimulate.py
import time, random, requests, argparse

URL = "http://127.0.0.1:5000/score"

def make_flow(label):
    return {
        "flow_id": f"{label}-{int(time.time()*1000)}",
        "src": f"10.0.0.{random.randint(2,250)}",
        "dst": "192.168.1.1",
        "dport": random.choice([22,80,443,8080]),
        "proto": "TCP",
        "score": round(random.uniform(0.8, 0.99) if label!="normal" else random.uniform(0.0,0.4), 2),
        "prediction": label,
        "origin": "simulator"
    }

def main(mode="random", rate=1.0, duration=0):
    stop = time.time() + duration if duration > 0 else None
    print("Simulator running mode:", mode, "rate:", rate)
    while True:
        if stop and time.time() > stop:
            break
        if mode == "random":
            r = random.random()
            label = "normal" if r < 0.7 else ("probe" if r < 0.9 else "dos")
        else:
            label = mode
        try:
            requests.post(URL, json=make_flow(label), timeout=1)
        except Exception as e:
            print("post error", e)
        time.sleep(1.0 / max(0.1, rate))

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--mode", default="random", choices=["random","normal","probe","dos"])
    p.add_argument("--rate", type=float, default=1.0)
    p.add_argument("--duration", type=float, default=0.0)
    args = p.parse_args()
    main(args.mode, args.rate, args.duration)



