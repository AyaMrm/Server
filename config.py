# Configuration du serveur C2

# Clé de chiffrement Fernet (32 bytes url-safe base64)
ENCRYPTION_KEY = b'VotreCleDeChiffrementSecure3210='

# Configuration du serveur
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 5000
DEBUG_MODE = True

# Configuration des timeouts
CLIENT_TIMEOUT = 3600  # 1 heure
COMMAND_TIMEOUT = 3600  # 1 heure
KEYLOG_RETENTION = 24 * 3600  # 24 heures
