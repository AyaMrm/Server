"""
Encrypteur simple pour les communications
"""
from cryptography.fernet import Fernet
import base64

class Encryptor:
    def __init__(self, key):
        """Initialiser avec une clé de chiffrement"""
        if isinstance(key, bytes) and len(key) == 32:
            # Encoder en base64 pour Fernet
            self.key = base64.urlsafe_b64encode(key)
        else:
            self.key = key
        
        self.cipher = Fernet(self.key)
    
    def encrypt(self, data):
        """Chiffrer les données"""
        if isinstance(data, str):
            data = data.encode()
        return self.cipher.encrypt(data)
    
    def decrypt(self, encrypted_data):
        """Déchiffrer les données"""
        return self.cipher.decrypt(encrypted_data)
