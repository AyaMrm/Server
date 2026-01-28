# 🗄️ Configuration SGBD - Guide Complet

## Vue d'ensemble

Votre serveur C2 peut maintenant utiliser différents SGBD :
- ✅ **SQLite** (par défaut, aucune config)
- ✅ **MySQL/MariaDB** 
- ✅ **PostgreSQL**

## Configuration Rapide

### 1. Choisir votre SGBD

Modifiez `db_config.py` :

```python
# Changer cette ligne
DB_TYPE = "mysql"  # ou "postgresql" ou "sqlite"
```

### 2. Installer les dépendances

```bash
# Pour MySQL
pip install pymysql cryptography sqlalchemy

# Pour PostgreSQL
pip install psycopg2-binary sqlalchemy

# Pour SQLite (déjà inclus)
pip install sqlalchemy
```

## Configuration MySQL

### Étape 1 : Installer MySQL

**Windows:**
```bash
# Télécharger depuis mysql.com
# Ou avec Chocolatey:
choco install mysql
```

**Linux:**
```bash
sudo apt update
sudo apt install mysql-server
```

### Étape 2 : Créer la base de données

```sql
# Se connecter à MySQL
mysql -u root -p

# Créer la base
CREATE DATABASE c2_database CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Créer un utilisateur
CREATE USER 'c2_user'@'localhost' IDENTIFIED BY 'VotreMotDePasse123!';

# Donner les permissions
GRANT ALL PRIVILEGES ON c2_database.* TO 'c2_user'@'localhost';
FLUSH PRIVILEGES;

# Quitter
EXIT;
```

### Étape 3 : Configurer db_config.py

```python
DB_TYPE = "mysql"

MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'database': 'c2_database',
    'user': 'c2_user',
    'password': 'VotreMotDePasse123!'
}
```

### Étape 4 : Modifier server.py

```python
# Remplacer
from database import Database
db = Database()

# Par
from database_sql import DatabaseSQL
from db_config import get_database_url
db = DatabaseSQL(get_database_url())
```

## Configuration PostgreSQL

### Étape 1 : Installer PostgreSQL

**Windows:**
```bash
# Télécharger depuis postgresql.org
# Ou avec Chocolatey:
choco install postgresql
```

**Linux:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

### Étape 2 : Créer la base de données

```sql
# Se connecter
sudo -u postgres psql

# Créer la base
CREATE DATABASE c2_database;

# Créer un utilisateur
CREATE USER c2_user WITH PASSWORD 'VotreMotDePasse123!';

# Donner les permissions
GRANT ALL PRIVILEGES ON DATABASE c2_database TO c2_user;

# Quitter
\q
```

### Étape 3 : Configurer db_config.py

```python
DB_TYPE = "postgresql"

POSTGRESQL_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'c2_database',
    'user': 'c2_user',
    'password': 'VotreMotDePasse123!'
}
```

### Étape 4 : Modifier server.py

Même chose que pour MySQL.

## Migration depuis SQLite

Si vous avez déjà des données dans SQLite :

### Option 1 : Export/Import manuel

```bash
# Exporter depuis SQLite
python db_manager.py --export backup.json

# Configurer le nouveau SGBD
# Puis importer les données manuellement
```

### Option 2 : Script de migration

```python
# migration.py
from database import Database as SQLiteDB
from database_sql import DatabaseSQL
from db_config import get_database_url

# Source
sqlite_db = SQLiteDB("c2_server.db")

# Destination
new_db = DatabaseSQL(get_database_url())

# Migrer les clients
clients = sqlite_db.get_all_clients()
for client in clients:
    new_db.register_client(
        client['client_id'],
        client['system_info'],
        client['ip']
    )

print(f"Migré {len(clients)} clients")
```

## Vérification

### Tester la connexion

```python
python db_config.py
```

### Tester avec le serveur

```python
python server.py
```

Vous devriez voir :
```
[DB] Base de données initialisée: mysql://c2_user:***@localhost/c2_database
```

## Gestion des SGBD

### MySQL

```bash
# Démarrer le service
# Windows
net start MySQL

# Linux
sudo systemctl start mysql

# Vérifier le statut
# Windows
sc query MySQL

# Linux
sudo systemctl status mysql
```

### PostgreSQL

```bash
# Démarrer le service
# Windows
net start postgresql-x64-13

# Linux
sudo systemctl start postgresql

# Vérifier le statut
# Windows
sc query postgresql-x64-13

# Linux
sudo systemctl status postgresql
```

## Accès aux données

### MySQL Workbench
1. Télécharger depuis mysql.com
2. Se connecter à localhost:3306
3. Explorer les tables visuellement

### pgAdmin (PostgreSQL)
1. Télécharger depuis pgadmin.org
2. Se connecter à localhost:5432
3. Explorer les tables visuellement

### DBeaver (Universel)
1. Télécharger depuis dbeaver.io
2. Supporte MySQL, PostgreSQL, SQLite
3. Interface unifiée

## Performances

### MySQL - Optimisations

```sql
-- Ajouter des index si nécessaire
CREATE INDEX idx_clients_online ON clients(last_seen);
CREATE INDEX idx_commands_status ON commands(client_id, status);
```

### PostgreSQL - Optimisations

```sql
-- Vacuum régulier
VACUUM ANALYZE;

-- Index concurrents
CREATE INDEX CONCURRENTLY idx_keylogs_timestamp ON keylogs(created_at);
```

## Sécurité

### MySQL

```sql
-- Changer le mot de passe
ALTER USER 'c2_user'@'localhost' IDENTIFIED BY 'NouveauMotDePasse!';

-- Limiter l'accès à localhost seulement
REVOKE ALL PRIVILEGES ON *.* FROM 'c2_user'@'%';
```

### PostgreSQL

```bash
# Modifier pg_hba.conf pour limiter les connexions
# /etc/postgresql/13/main/pg_hba.conf
# Ajouter:
host    c2_database    c2_user    127.0.0.1/32    md5
```

## Sauvegarde

### MySQL

```bash
# Backup
mysqldump -u c2_user -p c2_database > backup.sql

# Restaurer
mysql -u c2_user -p c2_database < backup.sql
```

### PostgreSQL

```bash
# Backup
pg_dump -U c2_user c2_database > backup.sql

# Restaurer
psql -U c2_user c2_database < backup.sql
```

## Dépannage

### Erreur : "Can't connect to server"

**MySQL:**
```bash
# Vérifier que MySQL tourne
netstat -an | findstr 3306  # Windows
sudo netstat -tulpn | grep 3306  # Linux
```

**PostgreSQL:**
```bash
# Vérifier que PostgreSQL tourne
netstat -an | findstr 5432  # Windows
sudo netstat -tulpn | grep 5432  # Linux
```

### Erreur : "Access denied"

Vérifier les credentials dans `db_config.py`

### Erreur : "Database does not exist"

Créer la base de données avec les commandes SQL ci-dessus

## Comparaison des SGBD

| Caractéristique | SQLite | MySQL | PostgreSQL |
|----------------|--------|-------|------------|
| **Installation** | Aucune | Moyenne | Moyenne |
| **Configuration** | Aucune | Facile | Moyenne |
| **Performance (petite)** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Performance (grande)** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Concurrent Users** | Limité | Excellent | Excellent |
| **Outils visuels** | Basique | Excellent | Excellent |
| **Sauvegarde** | Simple | Facile | Facile |

## Recommandations

- **< 10 clients** : SQLite suffit
- **10-100 clients** : MySQL recommandé
- **100+ clients** : PostgreSQL ou MySQL
- **Production** : MySQL ou PostgreSQL avec réplication

---

Votre système est maintenant prêt pour un SGBD professionnel ! 🚀
