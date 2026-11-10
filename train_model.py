# train_model.py
"""
Train a RandomForest on the 8 features the Flask app uses:
  ['duration','protocol_type','service','flag','src_bytes','dst_bytes','count','srv_count']

Usage:
  python train_model.py

Dataset expected: "KDDTrain+.txt" (NSL-KDD dataset).
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
import joblib
import os

DATA_FILE = "KDDTrain+.txt"
HAS_HEADER = False

# ✅ 43 columns (41 features + label + difficulty)
COLUMNS = [
 'duration','protocol_type','service','flag','src_bytes','dst_bytes','land','wrong_fragment',
 'urgent','hot','num_failed_logins','logged_in','num_compromised','root_shell','su_attempted',
 'num_root','num_file_creations','num_shells','num_access_files','num_outbound_cmds',
 'is_host_login','is_guest_login','count','srv_count','serror_rate','srv_serror_rate',
 'rerror_rate','srv_rerror_rate','same_srv_rate','diff_srv_rate','srv_diff_host_rate',
 'dst_host_count','dst_host_srv_count','dst_host_same_srv_rate','dst_host_diff_srv_rate',
 'dst_host_same_src_port_rate','dst_host_srv_diff_host_rate','dst_host_serror_rate',
 'dst_host_srv_serror_rate','dst_host_rerror_rate','dst_host_srv_rerror_rate',
 'label','difficulty'
]

if not os.path.exists(DATA_FILE):
    raise SystemExit(f"❌ Dataset not found: {DATA_FILE}")

print(f"✅ Loading dataset: {DATA_FILE}")
df = pd.read_csv(DATA_FILE, names=COLUMNS, header=None if not HAS_HEADER else 0)
print("📊 Dataset shape:", df.shape)

# Drop difficulty col
df = df.drop(columns=['difficulty'])

# Normalize text cols
df['protocol_type'] = df['protocol_type'].astype(str).str.strip().str.lower()
df['service'] = df['service'].astype(str).str.strip().str.lower()
df['flag'] = df['flag'].astype(str).str.strip()

# Forced mappings
FORCED_SERVICES = ["http","ftp","smtp","domain_u","ssh","telnet","dns","finger","ntp_u","eco_i","other"]
proto_map = {"tcp":0,"udp":1,"icmp":2}
svc_map = {s:i for i,s in enumerate(FORCED_SERVICES)}
flag_map = {"SF":0,"S0":1,"REJ":2,"RSTR":3,"RSTO":4,"SH":5,"OTH":6}

# Map unknown services to 'other'
df['service'] = df['service'].apply(lambda s: s if s in svc_map else 'other')

# Attack label mapping
attack_map = {
    'normal':'normal',
    # DoS
    'back':'dos','land':'dos','neptune':'dos','pod':'dos','smurf':'dos','teardrop':'dos',
    'apache2':'dos','udpstorm':'dos','processtable':'dos','mailbomb':'dos',
    # Probe
    'satan':'probe','ipsweep':'probe','nmap':'probe','portsweep':'probe','mscan':'probe','saint':'probe',
    # R2L
    'ftp_write':'r2l','guess_passwd':'r2l','imap':'r2l','multihop':'r2l','phf':'r2l',
    'spy':'r2l','warezclient':'r2l','warezmaster':'r2l','sendmail':'r2l','named':'r2l','snmpgetattack':'r2l',
    # U2R
    'buffer_overflow':'u2r','loadmodule':'u2r','perl':'u2r','rootkit':'u2r','sqlattack':'u2r','xterm':'u2r'
}

def safe_map_label(x):
    s = str(x).strip().lower()
    if s.endswith('.'):
        s = s[:-1]  # remove trailing dot
    return attack_map.get(s, 'other')

df['label_cat'] = df['label'].apply(safe_map_label)

print("\n📌 Label counts after mapping:")
print(df['label_cat'].value_counts())

# Build 8 features
def encode_row(r):
    return [
        float(r['duration']),
        proto_map.get(str(r['protocol_type']).lower(), 0),
        svc_map.get(str(r['service']).lower(), svc_map['other']),
        flag_map.get(str(r['flag']).upper(), flag_map['SF']),
        float(r['src_bytes']),
        float(r['dst_bytes']),
        float(r['count']),
        float(r['srv_count'])
    ]

print("\n⚙ Encoding features...")
X = np.array([encode_row(row) for _, row in df.iterrows()], dtype=float)
y_raw = df['label_cat'].values
print("✅ Feature matrix shape:", X.shape)

# Encode labels
label_encoder = LabelEncoder()
y = label_encoder.fit_transform(y_raw)
print("🎯 Classes:", list(label_encoder.classes_))

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2,
                                                    random_state=42, stratify=y)

# Scale
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train model
print("\n🚀 Training RandomForest...")
model = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
model.fit(X_train_scaled, y_train)

# Evaluate
print(f"\n✅ Train accuracy: {model.score(X_train_scaled, y_train):.4f}")
print(f"✅ Test accuracy : {model.score(X_test_scaled, y_test):.4f}")

# Save
joblib.dump(model, "ids_model.pkl")
joblib.dump(scaler, "scaler.pkl")
joblib.dump(label_encoder, "label_encoder.pkl")

print("\n💾 Saved ids_model.pkl, scaler.pkl, label_encoder.pkl")