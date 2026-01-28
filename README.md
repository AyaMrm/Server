# RAT (Remote Access Tool) - Advanced Programming Project

## ⚠️ AVERTISSEMENT LÉGAL

Ce projet est **UNIQUEMENT** à des fins éducatives dans le cadre d'un cours universitaire de programmation avancée et de cybersécurité. 

**USAGE STRICTEMENT INTERDIT :**
- Sur des systèmes sans autorisation explicite écrite
- À des fins malveillantes ou illégales
- En violation des lois locales, nationales ou internationales

L'utilisation non autorisée de ce logiciel peut entraîner des poursuites pénales.

---

## 📋 Description du Projet

Système client-serveur (C2 - Command & Control) avec **base de données PostgreSQL complète** démontrant les concepts de :
- Communication client-serveur chiffrée
- Architecture de base de données relationnelle (5 tables)
- API RESTful complète
- Dashboard web en temps réel
- Gestion de processus système
- Collecte d'informations système
- Surveillance (keylogger, screenshots)
- Gestion de fichiers à distance
- Persistence des données cloud-ready

## 🗄️ Architecture de Base de Données

### 5 Tables PostgreSQL
1. **`clients`** - Informations des clients connectés
2. **`keylogs`** - Données du keylogger
3. **`commands`** - Historique des commandes envoyées
4. **`command_results`** - Résultats des commandes
5. **`screenshots`** - Métadonnées et images capturées

### Fonctionnalités
- ✅ Auto-initialisation des tables au démarrage
- ✅ Relations avec clés étrangères (FOREIGN KEY)
- ✅ Indexes pour performance optimale
- ✅ UPSERT pour éviter les doublons
- ✅ Support PostgreSQL (production) + fichiers (local)
- ✅ Détection automatique de l'environnement

---

## 🏗️ Architecture du Système

### Composants Principaux

1. **Server (`server.py`)** - Serveur Flask C2 avec base de données
   - Gestion des clients connectés
   - File de commandes avec persistence
   - Stockage des résultats en BDD
   - API REST complète (16+ endpoints)
   - Auto-initialisation PostgreSQL

2. **Client (`client.py`)** - Agent déployé
   - Enregistrement auprès du serveur
   - Heartbeats réguliers
   - Exécution de commandes
   - Collecte d'informations système

3. **Controller (`controller.py`)** - Interface d'administration
   - Gestion des clients
   - Envoi de commandes
   - Visualisation des résultats

4. **Database Dashboard (`database_dashboard.html`)** - Interface web
   - 6 onglets (Stats, Clients, Keylogs, Commands, Results, Screenshots)
   - Auto-refresh toutes les 30 secondes
   - API JavaScript intégrée
   - Design responsive

### Modules Fonctionnels

- **Encryption (`encryptor.py`)** - Chiffrement XOR + Base64
- **Protocol (`protocol.py`)** - Format des messages
- **File Manager (`file_manager.py`)** - Opérations sur fichiers
- **Process Manager (`process_manager.py`)** - Gestion processus
- **Keylogger (`keylogger.py`)** - Capture clavier
- **Screenshot Manager (`screenshotManager.py`)** - Captures d'écran
- **System Info** - Collecte informations (OS, réseau, utilisateur, etc.)

## 🚀 Installation & Démarrage Rapide

### Prérequis
- Python 3.8+
- Pip
- (Optionnel) PostgreSQL pour persistence en base de données

### Installation des dépendances

```bash
pip install -r requirements.txt
```

### Configuration

Éditer `config.py` :
```python
HOST = "http://votre-serveur:5000"  # URL du serveur C2
ENCRYPTION_KEY = "votre_clé_secrète"  # Clé de chiffrement
```

### Configuration Base de Données (Optionnel)

Pour utiliser PostgreSQL au lieu du stockage fichier :
```bash
export DATABASE_URL="postgresql://user:password@host:5432/database"
```

Sans cette variable, le système utilise automatiquement le stockage fichier.

## 💻 Utilisation

### 1. Démarrer le Serveur C2

```bash
python server.py
```

Vous devriez voir :
```
[DATABASE] Using PostgreSQL database  # ou "Using file-based storage"
[DATABASE] ✅ Database initialized with 5 tables
[SERVER] Starting C2 server on port 5000
```

Le serveur démarre sur le port 5000 (configurable via variable d'environnement PORT).

### 2. Accéder aux Dashboards

- **Dashboard Principal** : http://localhost:5000/dashboard
- **Dashboard Base de Données** : http://localhost:5000/database

Le nouveau dashboard offre :
- 📊 Statistiques en temps réel
- 👥 Liste des clients avec statut online/offline
- ⌨️ Visualisation des keylogs
- 🔧 Historique des commandes
- 📄 Résultats des commandes
- 📸 Métadonnées des screenshots

### 3. Démarrer le Controller

```bash
python controller.py
```

Menu interactif pour :
- Voir les clients connectés
- Gérer les processus
- Naviguer dans les fichiers
- Gérer le keylogger
- Prendre des screenshots

### 4. Déployer le Client

```bash
python client.py
```

Le client :
1. S'enregistre auprès du serveur
2. Données sauvegardées dans la table `clients`
3. Tente d'installer la persistence
4. Envoie des heartbeats réguliers
5. Attend et exécute les commandes

## 🌐 API REST Endpoints

### Endpoints Client
```
POST /register              - Enregistrement du client
POST /heartbeat             - Heartbeat régulier
POST /commands              - Récupération des commandes
POST /commands_result       - Envoi des résultats
POST /keylog_data           - Envoi des keylogs
```

### Endpoints Admin
```
POST /admin/process/<id>    - Envoi commande processus
POST /admin/file/<id>       - Envoi commande fichier
GET  /admin/command_result/<cmd_id> - Récupération résultat
```

### Endpoints Database API (NOUVEAU)
```
GET /api/database/clients               - Liste tous les clients
GET /api/database/keylogs              - Récupère les keylogs
GET /api/database/commands             - Récupère les commandes
GET /api/database/command_results      - Récupère les résultats
GET /api/database/screenshots          - Récupère les screenshots
GET /api/database/stats                - Statistiques globales
```

**Paramètres supportés :**
- `client_id` - Filtrer par client spécifique
- `command_id` - Filtrer par commande spécifique
- `limit` - Limiter le nombre de résultats
- `include_data` - Inclure les données Base64 (screenshots)

**Exemple d'utilisation :**
```bash
# Récupérer tous les clients
curl https://your-server.com/api/database/clients

# Récupérer les keylogs d'un client spécifique
curl "https://your-server.com/api/database/keylogs?client_id=DESKTOP-ABC123&limit=50"

# Récupérer les statistiques
curl https://your-server.com/api/database/stats
```

## 📦 Fonctionnalités

### Gestion de Processus
- Liste tous les processus
- Arbre des processus
- Détails d'un processus
- Terminer un processus
- Démarrer un processus
- Exécuter des commandes système

### Gestion de Fichiers
- Navigation dans les répertoires
- Recherche de fichiers
- Download/Upload de fichiers
- Suppression de fichiers
- Création de répertoires

### Collecte d'Informations
- Système d'exploitation
- Architecture matérielle
- Informations réseau
- Informations utilisateur
- Privilèges

### Surveillance
- **Keylogger** : Capture des frappes clavier (sauvegardées en BDD)
- **Screenshots** : Captures d'écran configurables (métadonnées + data en BDD)

### Base de Données
- **Persistence complète** : Toutes les données en PostgreSQL
- **5 tables relationnelles** : clients, keylogs, commands, command_results, screenshots
- **Relations avec clés étrangères** : Intégrité référentielle
- **Indexes optimisés** : Requêtes performantes
- **Auto-initialisation** : Tables créées au démarrage
- **Cloud-ready** : Compatible Render.com, Heroku, etc.

### Persistence
- **Windows** : Registre (HKCU\Software\Microsoft\Windows\CurrentVersion\Run)
- **Linux** : Service systemd (user ou system)

## 🔧 Structure des Fichiers

```
├── server.py                 # Serveur C2
├── client.py                 # Agent client
├── controller.py             # Interface administrateur
├── config.py                 # Configuration
├── encryptor.py             # Chiffrement
├── protocol.py              # Protocole de communication
├── file_manager.py          # Gestion fichiers
├── process_manager.py       # Gestion processus
├── keylogger.py             # Keylogger
├── screenshotManager.py     # Screenshots
├── persistence.py           # Persistence
├── client_identity_manager.py  # Identité client
├── System_info.py           # Informations système
├── Network_info.py          # Informations réseau
├── Os_info.py               # Informations OS
├── User_info.py             # Informations utilisateur
├── Architecture_info.py     # Informations architecture
├── Privileges_info.py       # Informations privilèges
├── windows_pers.py          # Persistence Windows
├── windows_proc.py          # Processus Windows
├── linux_pers.py            # Persistence Linux
├── linux_proc.py            # Processus Linux
├── compile.py               # Compilation en exécutable
├── requirements.txt         # Dépendances Python
├── dashboard.html           # Dashboard web principal
├── database_dashboard.html  # Dashboard base de données (NOUVEAU)
├── DATABASE_ARCHITECTURE.md # Documentation BDD complète (NOUVEAU)
├── QUICK_START.md          # Guide de démarrage rapide (NOUVEAU)
└── DATABASE_IMPLEMENTATION_SUMMARY.md  # Résumé implémentation (NOUVEAU)
```

## 🗄️ Documentation de la Base de Données

Pour une documentation complète de l'architecture de base de données, consultez :

### 📘 [DATABASE_ARCHITECTURE.md](DATABASE_ARCHITECTURE.md)
- Schéma complet des 5 tables
- Définitions SQL
- Diagramme des relations
- Guide des opérations CRUD
- Documentation des endpoints API
- Considérations de sécurité
- Guide de performance et tuning

### 🚀 [QUICK_START.md](QUICK_START.md)
- Installation pas-à-pas
- Configuration locale et cloud
- Guide de déploiement Render
- Exemples d'utilisation de l'API
- Troubleshooting complet
- Features du dashboard

### ✅ [DATABASE_IMPLEMENTATION_SUMMARY.md](DATABASE_IMPLEMENTATION_SUMMARY.md)
- Résumé de l'implémentation
- Changements de code
- Checklist de test
- Critères de succès

## 🔒 Sécurité

### Chiffrement
- Tous les échanges client-serveur sont chiffrés (XOR + Base64)
- Clé partagée configurée dans `config.py`

### Base de Données
- ✅ Requêtes paramétrées (protection SQL injection)
- ✅ Clés étrangères (intégrité référentielle)
- ✅ Cascade delete (nettoyage automatique)
- ✅ Connexion via variable d'environnement (pas de credentials hardcodés)

### Limitations Actuelles
- Chiffrement XOR simple (non sécurisé pour production)
- Pas d'authentification forte sur les API endpoints
- Pas de rate limiting

### Améliorations Possibles
- Utiliser AES-256 pour le chiffrement
- Implémenter authentification mutuelle (certificats)
- Ajouter JWT pour les API endpoints
- Rate limiting sur les endpoints
- Logs sécurisés avec rotation

## 📊 Protocole de Communication

### Messages
- `register` : Enregistrement client (→ sauvegarde table `clients`)
- `heartbeat` : Signal de vie (→ update `last_seen`)
- `get_commands` : Récupération des commandes (→ query table `commands`)
- `command_result` : Résultat d'exécution (→ insert table `command_results`)
- `keylog_data` : Données du keylogger (→ insert table `keylogs`)

### Format
```json
{
  "type": "message_type",
  "client_id": "uuid",
  "data": {},
  "timestamp": 1234567890
}
```

## 🧪 Tests et Développement

### Environnement de Test
Utiliser uniquement dans un environnement isolé :
- Machines virtuelles
- Conteneurs Docker
- Réseau local isolé

### Compilation en Exécutable

```bash
python compile.py
```

Crée un exécutable autonome avec PyInstaller.

## 📝 Notes de Développement

### Points Forts
✅ Architecture modulaire et extensible  
✅ Support multi-plateforme (Windows/Linux)  
✅ Chiffrement des communications  
✅ Gestion d'erreurs robuste  
✅ Fonctionnalités complètes  
✅ **Base de données PostgreSQL avec 5 tables**  
✅ **API REST complète (16+ endpoints)**  
✅ **Dashboard web temps réel avec auto-refresh**  
✅ **Persistence complète des données**  
✅ **Cloud-ready (Render, Heroku compatible)**  
✅ **Documentation professionnelle**  

### Points d'Amélioration
⚠️ Tests unitaires à ajouter  
⚠️ Chiffrement simple (production nécessite AES-256)  
⚠️ Authentification API à renforcer (JWT recommandé)  
⚠️ Rate limiting à implémenter  
⚠️ Logs structurés à améliorer  

## 🌟 Nouvelles Fonctionnalités Database

### 🗄️ Architecture PostgreSQL
- **5 tables relationnelles** : clients, keylogs, commands, command_results, screenshots
- **Clés étrangères** : Intégrité référentielle automatique
- **Indexes optimisés** : Performance maximale
- **UPSERT logic** : Évite les doublons
- **Cascade delete** : Nettoyage automatique

### 📊 Dashboard Database
Accessible sur `/database` :
- **Statistics Tab** : Métriques globales (clients online/offline, total keylogs, commandes, etc.)
- **Clients Tab** : Liste complète avec IP, OS, hostname, status
- **Keylogs Tab** : Historique complet des frappes clavier
- **Commands Tab** : Toutes les commandes avec status (pending/completed)
- **Results Tab** : Résultats d'exécution en JSON
- **Screenshots Tab** : Métadonnées des captures (avec option d'afficher Base64)

### 🌐 API RESTful
6 nouveaux endpoints :
```
GET /api/database/clients        - Liste tous les clients
GET /api/database/keylogs        - Récupère les keylogs
GET /api/database/commands       - Récupère les commandes
GET /api/database/command_results - Récupère les résultats
GET /api/database/screenshots    - Récupère les screenshots
GET /api/database/stats          - Statistiques complètes
```

Tous les endpoints supportent :
- Filtrage par `client_id` ou `command_id`
- Pagination avec `limit`
- Réponses JSON structurées

### 🚀 Déploiement Cloud
- **Auto-détection** : Utilise PostgreSQL si `DATABASE_URL` est défini
- **Fallback** : Stockage fichier si pas de base de données
- **Render.com ready** : Configuration automatique
- **Heroku compatible** : Variable d'environnement standard
- **Zero downtime** : Migrations automatiques au démarrage

### 📈 Performance
- **Connection pooling** : psycopg2.pool.SimpleConnectionPool
- **Indexes multiples** : Sur foreign keys et champs fréquents
- **Requêtes optimisées** : LIMIT par défaut pour éviter surcharge
- **Batch operations** : Insertion multiple de keylogs

## 🎓 Objectifs Pédagogiques

Ce projet démontre :
1. **Programmation réseau** : Sockets, HTTP, REST API
2. **Bases de données** : PostgreSQL, relations, indexes, CRUD
3. **Sécurité** : Chiffrement, persistence, requêtes paramétrées
4. **Architecture logicielle** : Modularité, séparation des responsabilités
5. **Programmation système** : Processus, fichiers, privilèges
6. **Multi-threading** : Gestion asynchrone
7. **Cross-platform** : Compatibilité Windows/Linux
8. **Cloud deployment** : Production-ready architecture
9. **API Design** : RESTful best practices
10. **Frontend/Backend** : Full-stack development

## 📚 Références

- [Flask Documentation](https://flask.palletsprojects.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [psycopg2 Documentation](https://www.psycopg.org/docs/)
- [psutil Documentation](https://psutil.readthedocs.io/)
- [Render Deployment Guide](https://render.com/docs)

## 👨‍💻 Auteur

Projet universitaire - Advanced Programming Course  
**Mise à jour majeure** : Implémentation complète de la base de données PostgreSQL avec dashboard web

## 📄 Licence

Ce projet est fourni **UNIQUEMENT** à des fins éducatives.  
Aucune garantie n'est fournie. L'auteur décline toute responsabilité pour une utilisation abusive.

---

**RAPPEL IMPORTANT** : L'utilisation non autorisée de ce logiciel sur des systèmes tiers est **ILLÉGALE** et peut entraîner des poursuites judiciaires. Utilisez ce code de manière responsable et éthique.

---

## 🎯 Quick Links

- 📖 [Database Architecture Documentation](DATABASE_ARCHITECTURE.md)
- 🚀 [Quick Start Guide](QUICK_START.md)
- ✅ [Implementation Summary](DATABASE_IMPLEMENTATION_SUMMARY.md)
- 📊 [Technical Documentation](DOCUMENTATION_TECHNIQUE.md)
- 🌐 [Render Deployment Guide](RENDER_DEPLOYMENT.md)
