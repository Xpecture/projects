

 🚀 About the Project

Cyber attacks are happening every second, and detecting them quickly is one of the biggest challenges in network security. This project is an **Intrusion Detection System (IDS)** that watches network traffic and uses a **Random Forest machine learning model** to decide whether each connection is **normal** or an **attack**.

Because real DoS and probe attacks cannot be safely launched on a live network, this project uses a **safe demo setup**: a local **demo server** acts as the target website, attack traffic is **simulated** against it, and the system **sniffs** that traffic, classifies it, and shows the results on a **live dashboard with charts**.

> 💡 **In short:** simulate an attack on the demo server, let the AI detect it, and watch the DoS and Probe counts rise on the dashboard.

---

✨ Key Features

- 🤖 **Random Forest classifier** trained on the NSL-KDD dataset
- 🔍 **Detects 3 types of traffic:** Normal, DoS and Probe (anything that is not an attack is treated as normal by default)
- 🧪 **Safe testing** with a local demo server and simulated attacks
- 📡 **Automatic packet sniffing**: starts together with the dashboard, no extra step needed
- 📊 **Live dashboard** with charts, attack counts and a history of simulated attacks
- 💾 **Alert history** stored in a local SQLite database

---

## 🧠 How It Works

| Step | What happens | File |
|:----:|--------------|------|
| **1** | The **Random Forest model is trained** on the NSL-KDD dataset | `train_model.py` |
| **2** | The **demo server** (the target website) is opened in the browser | demo server file |
| **3** | The **dashboard starts** and the packet sniffer starts automatically | `app.py` |
| **4** | **DoS and Probe attacks are simulated** against the demo server | `stimulate_dos.py`, `stimulate_probe.py` |
| **5** | The model classifies the sniffed traffic and the **charts update live** | Dashboard |

```
 stimulate_dos.py    ───►  Demo server  ◄───  Packet sniffer + Random Forest
 stimulate_probe.py        (own port)          (starts automatically with app.py)
                                                        │
                                                        ▼
                                           📊 Dashboard (charts + history)
```

---

## 📁 Project Structure

| File | Purpose |
|------|---------|
| `train_model.py` | Trains the Random Forest model and saves the `.pkl` files |
| `akash.py` | Loads the NSL-KDD dataset and assigns the feature names |
| `app.py` | Dashboard (Flask) with charts, the `/score` API and alert storage. Also starts the sniffer |
| `live_detector.py` | Packet sniffer and detector, **started automatically by `app.py`** |
| `inject.py` | Helper that sends flows to the dashboard, **used automatically** |
| `stimulate_dos.py` | Simulates a DoS attack on the demo server |
| `stimulate_probe.py` | Simulates a probe attack on the demo server |
| `ids_model.pkl` | Trained Random Forest model |
| `scaler.pkl`, `encoders.pkl`, `label_encoder.pkl`, `protocol_encoder.pkl`, `service_encoder.pkl`, `flag_encoder.pkl` | Saved preprocessing objects |
| `ids_settings.json` | Dashboard settings |
| `result.html`, `static/style.css` | Dashboard web pages |

---

## 🛠️ Requirements

- 🐍 Python 3.9 or newer
- 📡 A packet-sniffing application installed on the computer (for example Npcap on Windows)
- 📦 Python libraries: `flask`, `requests`, `pandas`, `numpy`, `scikit-learn`, `joblib`, `scapy`

```bash
pip install flask requests pandas numpy scikit-learn joblib scapy
```

---

## 📥 Dataset

The **NSL-KDD dataset** is not included in this repository because of its size.

1. Download it from the Canadian Institute for Cybersecurity or Kaggle.
2. Place `KDDTrain+.txt` and `KDDTest+.txt` in the project folder.

---

## ⚙️ Installation

```bash
git clone https://github.com/Xpecture/projects.git
cd projects
python -m venv venv
venv\Scripts\activate
pip install flask requests pandas numpy scikit-learn joblib scapy
```

---

## ▶️ How to Run

> ⚠️ **Order matters.** Use a separate terminal for each step and keep them running.

**Step 1: Train the model** (only needed once)
```bash
python train_model.py
```

**Step 2: Start the demo server**
```bash
python YOUR_DEMO_SERVER_FILE.py
```
Open **http://127.0.0.1:YOUR_DEMO_PORT** in your browser to see the demo website. This is the target that the attacks will hit.

**Step 3: Start the dashboard**
```bash
python app.py
```
Open **http://127.0.0.1:5000** in your browser. The packet sniffer starts automatically, so there is no need to run `live_detector.py` or `inject.py` yourself.

**Step 4: Simulate the attacks on the demo server**
```bash
python stimulate_dos.py      # simulates a DoS attack
python stimulate_probe.py    # simulates a probe attack
```

**Step 5: Watch the dashboard** 🎉
The charts show how many **DoS** and **Probe** attacks were detected, along with a **history** of every attack simulated against the demo server. Normal traffic needs no simulation, because anything that is not an attack is shown as normal.

---

## 📝 Notes

- Alerts are stored in a local `alerts.db` file that is created automatically and is not uploaded to GitHub.
- Log files, packet captures (`.pcap`) and datasets are excluded with `.gitignore` to keep sensitive and large data out of the repository.
- The simulation uses only local and made-up IP addresses. Only test on networks you own or have permission to use.
- Run the terminal as **Administrator** if the sniffer needs permission to capture packets.

---

## 🎯 Future Improvements

- Detect more attack types (R2L, U2R)
- Email or SMS alerts for detected attacks
- Compare Random Forest with other models
- Deploy the dashboard online

---

## ⚠️ Disclaimer

This project is built for **educational purposes** and is not a replacement for a production-grade IDS.

