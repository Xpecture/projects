# app.py
import os, json, sqlite3, subprocess, sys, time
from datetime import datetime
from flask import Flask, jsonify, render_template, request

app = Flask(__name__, template_folder="templates", static_folder="static")

DB_FILE = "alerts.db"
SETTINGS_FILE = "ids_settings.json"
SNIFFER = None       # subprocess handle for live_detector.py

# ---------------- Settings ----------------
DEFAULT_SETTINGS = {
    "theme": "light",               # "light" | "dark"
    "iface": "",                    # e.g. r"\\Device\\NPF_{...}" or "lo"
    "mode": "classify",             # "baseline" (always normal) | "classify"
    "refresh_interval": 1000,       # ms
    "auto_start": False,
    "clear_on_start": True          # clear table when user presses Start
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE,"r",encoding="utf-8") as f:
                s = json.load(f)
                return {**DEFAULT_SETTINGS, **s}
        except:
            pass
    return DEFAULT_SETTINGS.copy()

def save_settings(s):
    with open(SETTINGS_FILE,"w",encoding="utf-8") as f:
        json.dump(s,f,indent=2)

# ---------------- DB ----------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        flow_id TEXT,
        src TEXT,
        dst TEXT,
        dport INTEGER,
        proto TEXT,
        score REAL,
        prediction TEXT,
        ts TEXT
    );
    """)
    conn.commit()
    conn.close()

def clear_alerts():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("DELETE FROM alerts")
    conn.commit()
    conn.close()

def insert_alert(flow_id, src, dst, dport, proto, score, prediction):
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "INSERT INTO alerts (flow_id,src,dst,dport,proto,score,prediction,ts) VALUES (?,?,?,?,?,?,?,?)",
        (flow_id, src, dst, dport, proto, score, prediction, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

def fetch_alerts(limit=500):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id,flow_id,src,dst,dport,proto,score,prediction,ts FROM alerts ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    cols = ["id","flow_id","src","dst","dport","proto","score","prediction","ts"]
    return [dict(zip(cols,r)) for r in rows]

# ---------------- Sniffer process ----------------
def sniffer_running():
    global SNIFFER
    return SNIFFER is not None and SNIFFER.poll() is None

def start_sniffer():
    """Launch live_detector.py with current settings."""
    global SNIFFER
    if sniffer_running():
        return False, "already running"

    s = load_settings()
    script = os.path.join(os.getcwd(), "live_detector.py")
    if not os.path.exists(script):
        return False, "live_detector.py missing"

    args = [
        sys.executable, script,
        "--post-url", "http://127.0.0.1:5000/score",
        "--mode", s.get("mode","classify"),
    ]
    iface = (s.get("iface") or "").strip()
    if iface:
        args += ["--iface", iface]

    # Optional: write stdout/stderr to files (helpful for debugging)
    stdout = open("sniffer_out.log","a",encoding="utf-8")
    stderr = open("sniffer_err.log","a",encoding="utf-8")

    creationflags = 0
    if os.name == "nt":
        # Keep a background process without stealing focus (no console popping)
        CREATE_NO_WINDOW = 0x08000000
        DETACHED_PROCESS = 0x00000008
        creationflags = CREATE_NO_WINDOW | DETACHED_PROCESS

    SNIFFER = subprocess.Popen(
        args,
        stdout=stdout, stderr=stderr,
        creationflags=creationflags
    )
    return True, f"pid={SNIFFER.pid}"

def stop_sniffer():
    global SNIFFER
    if not sniffer_running():
        SNIFFER = None
        return False, "not running"
    SNIFFER.terminate()
    try:
        SNIFFER.wait(timeout=3)
    except subprocess.TimeoutExpired:
        SNIFFER.kill()
    SNIFFER = None
    return True, "stopped"

# ---------------- Flask routes ----------------
@app.route("/")
def home():
    s = load_settings()
    return render_template("index.html", theme=s["theme"])

@app.route("/score", methods=["POST"])
def score():
    # live_detector.py / stimulators post flows here
    data = request.get_json(force=True)
    flows = data if isinstance(data, list) else [data]
    for f in flows:
        # If user chooses "baseline", force everything to normal
        if load_settings().get("mode") == "baseline":
            pred = "normal"; score = 0.0
        else:
            pred = f.get("prediction","normal")
            score = float(f.get("score",0.0))

        insert_alert(
            f.get("flow_id", f"id-{int(time.time()*1000)}"),
            f.get("src","0.0.0.0"),
            f.get("dst","0.0.0.0"),
            int(f.get("dport",0) or 0),
            f.get("proto","TCP"),
            score,
            pred
        )
    return jsonify({"ok": True})

@app.route("/alerts")
def alerts():
    limit = int(request.args.get("limit", 500))
    return jsonify(fetch_alerts(limit))

@app.route("/stats")
def stats():
    rows = fetch_alerts(1000)
    counts = {}
    for r in rows:
        p = r["prediction"]
        counts[p] = counts.get(p,0)+1
    latest = rows[0] if rows else None
    return jsonify({
        "total": len(rows),
        "by_prediction": counts,
        "latest_pred": latest["prediction"] if latest else None
    })

@app.route("/sniffer/start", methods=["POST"])
def api_start():
    s = load_settings()
    if bool(s.get("clear_on_start", True)):
        clear_alerts()
    ok, msg = start_sniffer()
    return jsonify({"started": ok, "msg": msg})

@app.route("/sniffer/stop", methods=["POST"])
def api_stop():
    ok, msg = stop_sniffer()
    return jsonify({"stopped": ok, "msg": msg})

@app.route("/sniffer/status")
def api_status():
    return jsonify({"running": sniffer_running()})

@app.route("/clear_alerts", methods=["POST"])
def api_clear():
    clear_alerts()
    return jsonify({"cleared": True})

@app.route("/settings", methods=["GET","POST"])
def api_settings():
    if request.method == "GET":
        return jsonify(load_settings())

    s = load_settings()
    incoming = request.get_json(force=True)
    # sanitize
    s["theme"] = incoming.get("theme", s["theme"]) in ("dark","light") and incoming["theme"] or s["theme"]
    s["iface"] = (incoming.get("iface") or "").strip()
    s["mode"]  = incoming.get("mode", s["mode"])
    s["refresh_interval"] = max(200, int(incoming.get("refresh_interval", s["refresh_interval"]) or 1000))
    s["auto_start"]   = bool(incoming.get("auto_start", False))
    s["clear_on_start"] = bool(incoming.get("clear_on_start", True))
    save_settings(s)
    return jsonify(s)

# ---------------- Entry ----------------
if __name__ == "__main__":
    init_db()
    s = load_settings()
    if s.get("auto_start"):
        start_sniffer()
    print("✅ IDS running at http://127.0.0.1:5000")
    # Use reloader=False so we don’t spawn duplicate sniffer processes
    app.run(debug=True, use_reloader=False)
