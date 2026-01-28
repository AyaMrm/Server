"""
Script de test et création des tables MySQL
Lance ce script après avoir configuré db_config.py
"""

from database_sql import DatabaseSQL
from db_config import get_database_url
import sys

def test_mysql_connection():
    """Tester la connexion MySQL et créer les tables"""
    
    print("="*60)
    print("TEST DE CONNEXION MYSQL")
    print("="*60)
    
    try:
        # Afficher l'URL de connexion (sans le mot de passe)
        url = get_database_url()
        safe_url = url.replace(url.split(':')[2].split('@')[0], '***')
        print(f"\n[1] Tentative de connexion à: {safe_url}")
        
        # Créer la connexion et les tables
        print("[2] Initialisation de la base de données...")
        db = DatabaseSQL(get_database_url(), echo=True)
        
        print("\n" + "="*60)
        print("✅ SUCCÈS ! Les tables ont été créées")
        print("="*60)
        
        # Tester un enregistrement
        print("\n[3] Test d'insertion d'un client test...")
        success = db.register_client(
            client_id="test_client_001",
            system_info={
                "os": "Windows 10",
                "hostname": "TEST-PC",
                "user": "test_user"
            },
            ip_address="127.0.0.1"
        )
        
        if success:
            print("✅ Client test enregistré avec succès")
            
            # Récupérer le client
            print("\n[4] Test de lecture du client...")
            client = db.get_client("test_client_001")
            if client:
                print(f"✅ Client récupéré: {client['client_id']}")
                print(f"   - IP: {client['ip']}")
                print(f"   - OS: {client['system_info']['os']}")
            
            # Nettoyer le test
            print("\n[5] Nettoyage du client test...")
            db.cleanup_old_clients(0)  # Supprimer tous les clients
            print("✅ Nettoyage terminé")
        
        print("\n" + "="*60)
        print("🎉 CONFIGURATION MYSQL RÉUSSIE !")
        print("="*60)
        print("\nVous pouvez maintenant:")
        print("1. Ouvrir MySQL Workbench")
        print("2. Se connecter à votre base de données")
        print("3. Voir les 5 tables créées:")
        print("   - clients")
        print("   - commands")
        print("   - keylogs")
        print("   - screenshots")
        print("   - activity_log")
        print("\nPour démarrer le serveur:")
        print("   python server.py")
        
        db.close()
        return True
        
    except Exception as e:
        print("\n" + "="*60)
        print("❌ ERREUR DE CONNEXION")
        print("="*60)
        print(f"\nErreur: {e}")
        print("\n🔧 Vérifiez:")
        print("1. MySQL est démarré (net start MySQL)")
        print("2. db_config.py contient les bons credentials")
        print("3. La base de données existe")
        print("4. L'utilisateur a les permissions")
        print("\nCommandes MySQL pour créer la base:")
        print("   mysql -u root -p")
        print("   CREATE DATABASE c2_database;")
        print("   CREATE USER 'c2_user'@'localhost' IDENTIFIED BY 'VotreMotDePasse';")
        print("   GRANT ALL PRIVILEGES ON c2_database.* TO 'c2_user'@'localhost';")
        print("   FLUSH PRIVILEGES;")
        
        return False


if __name__ == "__main__":
    success = test_mysql_connection()
    sys.exit(0 if success else 1)
