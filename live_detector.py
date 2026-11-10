# live_detector.py
"""
Capture packets using Scapy and POST compact flow summaries to /score.
The server decides whether to force 'normal' (baseline) or use the model.

Usage examples:
  python live_detector.py --mode classify --iface "\\Device\\NPF_{...}"
  python live_detector.py --mode classify --iface lo
"""
import argparse, time, random, requests, os
from datetime import datetime

try:
    from scapy.all import sniff, IP, TCP, UDP, Raw
except Exception as e:
    print("Scapy import failed:", e)
    raise

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--post-url", default="http://127.0.0.1:5000/score")
    p.add_argument("--iface", default=None, help="Exact iface string from scapy get_if_list() or 'lo'")
    p.add_argument("--mode", default="classify", choices=["classify","baseline"])
    p.add_argument("--quiet", action="store_true")
    return p.parse_args()

POST_URL = None
MODE = "classify"
QUIET = False

def flow_from_pkt(pkt):
    proto = "TCP" if TCP in pkt else ("UDP" if UDP in pkt else "IP")
    dport = 0
    if TCP in pkt: dport = int(pkt[TCP].dport)
    elif UDP in pkt: dport = int(pkt[UDP].dport)

    src = pkt[IP].src if IP in pkt else "0.0.0.0"
    dst = pkt[IP].dst if IP in pkt else "0.0.0.0"

    # score/prediction — in a real pipeline you'd call your trained model.
    # Here we keep it minimal: label = "normal" unless our simulators create obvious patterns.
    label = "normal"; score = 0.01
    # If someone runs the demo stimulators (they spray many packets quickly),
    # you typically see higher port variety/rates. To keep this self-contained,
    # we conservatively set 'normal' here; your server can enforce 'baseline'.
    # You can insert your model call and set label/score accordingly.

    flow = {
        "flow_id": f"{int(time.time()*1000)}",
        "src": src, "dst": dst, "dport": dport,
        "proto": proto,
        "score": score,
        "prediction": label,
    }
    return flow

def on_pkt(pkt):
    if IP not in pkt: return
    f = flow_from_pkt(pkt)
    try:
        requests.post(POST_URL, json=f, timeout=1.0)
        if not QUIET:
            print("posted", f["prediction"], f["src"], "->", f["dst"])
    except Exception as e:
        if not QUIET: print("post failed:", e)

def main():
    global POST_URL, MODE, QUIET
    args = parse_args()
    POST_URL = args.post_url
    MODE = args.mode
    QUIET = args.quiet

    print("Loaded. Mode:", MODE, "Iface:", args.iface or "(default)")
    print("Starting sniff... Ctrl+C to stop.")
    sniff(prn=on_pkt, store=False, iface=args.iface)  # admin may be required on Windows

if __name__ == "__main__":
    main()
