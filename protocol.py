"""
Protocole de communication pour le C2
"""
import time

class Protocol:
    # Types de messages
    MSG_REGISTER = "register"
    MSG_HEARTBEAT = "heartbeat"
    MSG_COMMAND = "command"
    MSG_RESULT = "result"
    MSG_KEYLOG = "keylog"
    MSG_SCREENSHOT = "screenshot"
    
    @staticmethod
    def create_message(msg_type, data):
        """Créer un message protocole"""
        return {
            'type': msg_type,
            'data': data,
            'timestamp': time.time()
        }
    
    @staticmethod
    def parse_message(message):
        """Parser un message protocole"""
        return message.get('type'), message.get('data')
