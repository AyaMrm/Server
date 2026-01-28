"""
Configuration de la base de données
Choisissez votre SGBD ici
"""

# ==================== CONFIGURATION SGBD ====================

# Choisir le type de base de données
DB_TYPE = "mysql"  # Options: "sqlite", "mysql", "postgresql"

# ==================== SQLITE (Par défaut) ====================
SQLITE_DB_PATH = "c2_server.db"

# ==================== MYSQL ====================
MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'database': 'c2_database',
    'user': 'root',
    'password': ''  # WAMP par défaut : root sans mot de passe
}

# ==================== FONCTIONS HELPER ====================

def get_database_url():
    """Obtenir l'URL de connexion selon la configuration"""
    
    if DB_TYPE == "sqlite":
        return f"sqlite:///{SQLITE_DB_PATH}"
    
    elif DB_TYPE == "mysql":
        return (
            f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}"
            f"@{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['database']}"
        )
    
    elif DB_TYPE == "postgresql":
        return (
            f"postgresql://{POSTGRESQL_CONFIG['user']}:{POSTGRESQL_CONFIG['password']}"
            f"@{POSTGRESQL_CONFIG['host']}:{POSTGRESQL_CONFIG['port']}/{POSTGRESQL_CONFIG['database']}"
        )
    
    else:
        raise ValueError(f"Type de BD non supporté: {DB_TYPE}")


def get_required_packages():
    """Obtenir les packages Python requis selon le SGBD"""
    packages = {
        "sqlite": [],  # Inclus avec Python
        "mysql": ["pymysql", "cryptography"],
        "postgresql": ["psycopg2-binary"]
    }
    return packages.get(DB_TYPE, [])


# ==================== INSTRUCTIONS ====================

SETUP_INSTRUCTIONS = {
    "mysql": """
    Installation MySQL:
    1. pip install pymysql cryptography
    2. Créer la base de données:
       mysql -u root -p
       CREATE DATABASE c2_database CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
       CREATE USER 'c2_user'@'localhost' IDENTIFIED BY 'votre_mot_de_passe';
       GRANT ALL PRIVILEGES ON c2_database.* TO 'c2_user'@'localhost';
       FLUSH PRIVILEGES;
    3. Mettre à jour MYSQL_CONFIG dans db_config.py
    """,
    
    "postgresql": """
    Installation PostgreSQL:
    1. pip install psycopg2-binary
    2. Créer la base de données:
       psql -U postgres
       CREATE DATABASE c2_database;
       CREATE USER c2_user WITH PASSWORD 'votre_mot_de_passe';
       GRANT ALL PRIVILEGES ON DATABASE c2_database TO c2_user;
    3. Mettre à jour POSTGRESQL_CONFIG dans db_config.py
    """,
    
    "sqlite": """
    SQLite est déjà configuré et prêt à l'emploi.
    Aucune configuration supplémentaire nécessaire.
    """
}


if __name__ == "__main__":
    print(f"Configuration actuelle: {DB_TYPE}")
    print(f"URL de connexion: {get_database_url()}")
    print(f"\nPackages requis: {get_required_packages() or 'Aucun (inclus avec Python)'}")
    print(f"\nInstructions de configuration:")
    print(SETUP_INSTRUCTIONS[DB_TYPE])
