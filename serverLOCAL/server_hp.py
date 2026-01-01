# honeypot_server.py
"""
Serveur honeypot avec page d'accueil contenant des liens vers fichiers pièges
Capture détaillée des bots et sauvegarde des logs en fin de session
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import socket
import json
from datetime import datetime
import time
import threading
from collections import defaultdict
import os

# Configuration
PORT = 8080
LOG_FILE = "bot_capture_log.txt"
SESSION_LOG = "session_summary.json"

# Liste des fichiers pièges (à adapter selon tes fichiers réels)
FAKE_FILES = [
    {"name": "📁 backup_database.zip", "path": "/backup.zip", "desc": "Archive de sauvegarde complète"},
    {"name": "🔑 config_server.php", "path": "/config.php", "desc": "Configuration du serveur"},
    {"name": "🗄️  database_dump.sql", "path": "/database.sql", "desc": "Export SQL de la base de données"},
    {"name": "🔐 env_secrets.env", "path": "/.env", "desc": "Variables d'environnement sensibles"},
    {"name": "👑 admin_panel.php", "path": "/admin.php", "desc": "Panneau d'administration"},
    {"name": "🔧 api_config.json", "path": "/api.json", "desc": "Configuration des API"},
    {"name": "📊 logs_application.log", "path": "/app.log", "desc": "Logs d'application"},
    {"name": "💾 users_export.csv", "path": "/users.csv", "desc": "Export des utilisateurs"},
]

class HoneypotHandler(BaseHTTPRequestHandler):
    """Handler pour piéger et analyser les bots"""
    
    # Stockage en mémoire des données de session
    session_data = {
        "start_time": datetime.now().isoformat(),
        "total_requests": 0,
        "unique_ips": set(),
        "bot_ips": defaultdict(list),
        "file_access": defaultdict(int),
        "user_agents": defaultdict(int),
        "suspicious_activity": []
    }
    
    def detect_bot_type(self, user_agent, path, client_ip):
        """Détecte le type de bot basé sur l'User-Agent et le comportement"""
        ua = user_agent.lower()
        path_lower = path.lower()
        
        bot_info = {
            "type": "Human",
            "confidence": 0,
            "tools": [],
            "intent": "Unknown"
        }
        
        # Détection par User-Agent
        if any(keyword in ua for keyword in ['bot', 'crawler', 'spider']):
            bot_info["type"] = "WebCrawler"
            bot_info["confidence"] = 80
            bot_info["tools"].append("GenericCrawler")
        
        if 'python' in ua or 'requests' in ua:
            bot_info["type"] = "ScriptPython"
            bot_info["confidence"] = 90
            bot_info["tools"].append("PythonRequests")
            
        if 'curl' in ua:
            bot_info["type"] = "CLI_Tool"
            bot_info["confidence"] = 85
            bot_info["tools"].append("curl")
            
        if 'wget' in ua:
            bot_info["type"] = "CLI_Tool"
            bot_info["confidence"] = 85
            bot_info["tools"].append("wget")
            
        if 'nmap' in ua or 'nikto' in ua or 'nessus' in ua:
            bot_info["type"] = "SecurityScanner"
            bot_info["confidence"] = 95
            bot_info["tools"].append("SecurityScanner")
            bot_info["intent"] = "VulnerabilityScan"
            
        if 'sqlmap' in ua:
            bot_info["type"] = "AttackTool"
            bot_info["confidence"] = 99
            bot_info["tools"].append("sqlmap")
            bot_info["intent"] = "SQLInjection"
            
        if 'dirb' in ua or 'gobuster' in ua or 'dirsearch' in ua:
            bot_info["type"] = "DirectoryScanner"
            bot_info["confidence"] = 90
            bot_info["tools"].append("DirectoryBuster")
            bot_info["intent"] = "DirectoryDiscovery"
        
        # Détection par comportement (chemin accédé)
        suspicious_paths = ['admin', 'login', 'config', '.env', '.git', 'wp-', 'backup', 'sql']
        if any(keyword in path_lower for keyword in suspicious_paths):
            if bot_info["type"] == "Human":
                bot_info["type"] = "SuspiciousScanner"
                bot_info["confidence"] = 70
                bot_info["intent"] = "ResourceDiscovery"
            else:
                bot_info["intent"] = "TargetedScan"
                
        return bot_info
    
    def log_bot_activity(self, client_ip, user_agent, path, bot_info):
        """Loggue l'activité du bot dans la console et en mémoire"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Mise à jour des statistiques de session
        self.session_data["total_requests"] += 1
        self.session_data["unique_ips"].add(client_ip)
        
        # Suivi par IP
        activity_entry = {
            "timestamp": timestamp,
            "path": path,
            "user_agent": user_agent[:150],
            "bot_type": bot_info["type"],
            "confidence": bot_info["confidence"],
            "tools": bot_info["tools"],
            "intent": bot_info["intent"]
        }
        
        self.session_data["bot_ips"][client_ip].append(activity_entry)
        
        # Suivi des fichiers accédés
        for file_info in FAKE_FILES:
            if file_info["path"] == path:
                self.session_data["file_access"][file_info["name"]] += 1
                break
        
        # Comptage des user-agents
        self.session_data["user_agents"][user_agent[:100]] += 1
        
        # Log dans la console
        emoji = {
            "WebCrawler": "🕷️",
            "ScriptPython": "🐍",
            "CLI_Tool": "💻",
            "SecurityScanner": "🔍",
            "AttackTool": "⚔️",
            "DirectoryScanner": "📁",
            "SuspiciousScanner": "👁️",
            "Human": "👤"
        }.get(bot_info["type"], "❓")
        
        print(f"\n{emoji} [{timestamp}] {bot_info['type']} ({bot_info['confidence']}%)")
        print(f"   IP: {client_ip}")
        print(f"   Path: {path}")
        print(f"   Tools: {', '.join(bot_info['tools'])}")
        print(f"   Intent: {bot_info['intent']}")
        print(f"   UA: {user_agent[:80]}...")
        
        # Log détaillé dans fichier
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"IP: {client_ip}\n")
            f.write(f"Bot Type: {bot_info['type']}\n")
            f.write(f"Confidence: {bot_info['confidence']}%\n")
            f.write(f"Path: {path}\n")
            f.write(f"User-Agent: {user_agent}\n")
            f.write(f"Detected Tools: {', '.join(bot_info['tools'])}\n")
            f.write(f"Intent: {bot_info['intent']}\n")
            f.write(f"{'='*60}\n")
        
        # Marquer comme suspect si nécessaire
        if bot_info["type"] != "Human" and bot_info["confidence"] > 80:
            suspicious_entry = {
                "ip": client_ip,
                "timestamp": timestamp,
                "bot_type": bot_info["type"],
                "path": path,
                "intent": bot_info["intent"]
            }
            self.session_data["suspicious_activity"].append(suspicious_entry)
            
            # Alerte spéciale pour les outils d'attaque
            if bot_info["type"] == "AttackTool":
                print(f"   ⚠️  ALERTE: Outil d'attaque détecté!")
    
    def do_GET(self):
        """Gère toutes les requêtes GET"""
        client_ip = self.client_address[0]
        user_agent = self.headers.get('User-Agent', 'Unknown')
        path = self.path
        
        # Détection du type de bot
        bot_info = self.detect_bot_type(user_agent, path, client_ip)
        
        # Log de l'activité
        self.log_bot_activity(client_ip, user_agent, path, bot_info)
        
        # Réponse selon le chemin
        if path == "/":
            # Page d'accueil principale
            self.serve_welcome_page(client_ip)
        elif path == "/_log":
            # Endpoint de tracking invisible
            self.send_response(200)
            self.end_headers()
        elif any(file_info["path"] == path for file_info in FAKE_FILES):
            # Accès à un fichier piège
            self.serve_honey_file(path)
        else:
            # Page non trouvée (piège supplémentaire)
            self.serve_404_trap(path)
    
    def serve_welcome_page(self, client_ip):
        """Sert la page d'accueil avec liens vers fichiers pièges"""
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Réseau Local - Serveur de Fichiers</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Segoe UI', system-ui, sans-serif;
                    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                    color: #e6e6e6;
                    min-height: 100vh;
                    padding: 20px;
                }}
                
                .container {{
                    max-width: 1000px;
                    margin: 0 auto;
                    background: rgba(255, 255, 255, 0.05);
                    backdrop-filter: blur(10px);
                    border-radius: 20px;
                    padding: 40px;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
                }}
                
                header {{
                    text-align: center;
                    margin-bottom: 40px;
                    padding-bottom: 20px;
                    border-bottom: 2px solid rgba(255, 255, 255, 0.1);
                }}
                
                h1 {{
                    color: #64ffda;
                    font-size: 2.5em;
                    margin-bottom: 10px;
                    background: linear-gradient(45deg, #64ffda, #00bcd4);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }}
                
                .subtitle {{
                    color: #b2becd;
                    font-size: 1.1em;
                    opacity: 0.8;
                }}
                
                .ip-display {{
                    background: rgba(0, 0, 0, 0.3);
                    padding: 12px 24px;
                    border-radius: 12px;
                    font-family: 'Courier New', monospace;
                    margin: 20px auto;
                    display: inline-block;
                    border: 1px solid rgba(100, 255, 218, 0.3);
                }}
                
                .section {{
                    margin: 30px 0;
                }}
                
                .section-title {{
                    color: #bb86fc;
                    font-size: 1.4em;
                    margin-bottom: 15px;
                    padding-bottom: 8px;
                    border-bottom: 1px solid rgba(187, 134, 252, 0.3);
                }}
                
                .files-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                    gap: 20px;
                    margin-top: 20px;
                }}
                
                .file-card {{
                    background: rgba(30, 30, 46, 0.7);
                    border-radius: 12px;
                    padding: 20px;
                    transition: all 0.3s ease;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                }}
                
                .file-card:hover {{
                    transform: translateY(-5px);
                    border-color: #64ffda;
                    box-shadow: 0 10px 30px rgba(100, 255, 218, 0.2);
                }}
                
                .file-name {{
                    color: #ffffff;
                    font-weight: 600;
                    font-size: 1.1em;
                    margin-bottom: 8px;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }}
                
                .file-desc {{
                    color: #b2becd;
                    font-size: 0.9em;
                    margin-bottom: 15px;
                    line-height: 1.5;
                }}
                
                .download-btn {{
                    display: inline-block;
                    background: linear-gradient(135deg, #6200ea, #bb86fc);
                    color: white;
                    padding: 10px 20px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: 600;
                    transition: all 0.3s;
                    border: none;
                    cursor: pointer;
                    width: 100%;
                    text-align: center;
                }}
                
                .download-btn:hover {{
                    background: linear-gradient(135deg, #3700b3, #985eff);
                    transform: scale(1.02);
                }}
                
                .warning-box {{
                    background: rgba(255, 193, 7, 0.1);
                    border: 1px solid rgba(255, 193, 7, 0.3);
                    border-radius: 12px;
                    padding: 20px;
                    margin: 30px 0;
                }}
                
                .warning-title {{
                    color: #ffc107;
                    font-weight: 600;
                    margin-bottom: 10px;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }}
                
                .stats {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-top: 30px;
                }}
                
                .stat-card {{
                    background: rgba(255, 255, 255, 0.05);
                    padding: 20px;
                    border-radius: 12px;
                    text-align: center;
                }}
                
                .stat-value {{
                    font-size: 2em;
                    font-weight: bold;
                    color: #64ffda;
                    margin-bottom: 5px;
                }}
                
                .stat-label {{
                    color: #b2becd;
                    font-size: 0.9em;
                }}
                
                footer {{
                    margin-top: 40px;
                    text-align: center;
                    color: #888;
                    font-size: 0.9em;
                    padding-top: 20px;
                    border-top: 1px solid rgba(255, 255, 255, 0.1);
                }}
                
                @media (max-width: 768px) {{
                    .container {{
                        padding: 20px;
                    }}
                    
                    .files-grid {{
                        grid-template-columns: 1fr;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <header>
                    <h1>📡 Serveur de Fichiers Local</h1>
                    <p class="subtitle">Accès aux ressources partagées sur le réseau</p>
                    <div class="ip-display">
                        🔗 Connecté depuis: {client_ip}
                    </div>
                </header>
                
                <div class="warning-box">
                    <div class="warning-title">⚠️ Attention</div>
                    <p>Ce serveur contient des fichiers sensibles. Assurez-vous d'avoir les autorisations nécessaires avant d'accéder à ces ressources.</p>
                </div>
                
                <div class="section">
                    <h2 class="section-title">📂 Fichiers Disponibles</h2>
                    <p>Voici la liste des fichiers partagés sur ce serveur :</p>
                    
                    <div class="files-grid">
        '''
        
        # Ajout des cartes de fichiers
        for file_info in FAKE_FILES:
            html += f'''
                        <div class="file-card">
                            <div class="file-name">
                                {file_info["name"].split(" ", 1)[0]} {file_info["name"].split(" ", 1)[1] if " " in file_info["name"] else ""}
                            </div>
                            <p class="file-desc">{file_info["desc"]}</p>
                            <a href="{file_info["path"]}" class="download-btn" download>
                                ⬇️ Télécharger
                            </a>
                        </div>
            '''
        
        html += f'''
                    </div>
                </div>
                
                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-value">{len(FAKE_FILES)}</div>
                        <div class="stat-label">Fichiers disponibles</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{datetime.now().strftime("%H:%M")}</div>
                        <div class="stat-label">Heure serveur</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">Local</div>
                        <div class="stat-label">Réseau</div>
                    </div>
                </div>
                
                <footer>
                    <p>Serveur local • {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</p>
                    <p style="margin-top: 10px; font-size: 0.8em; opacity: 0.6;">
                        Toutes les activités sur ce serveur sont journalisées.
                    </p>
                </footer>
            </div>
        </body>
        </html>
        '''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_honey_file(self, path):
        """Sert un fichier piège avec contenu factice"""
        # Détermine le type de fichier
        content_type = "text/plain"
        if path.endswith(".php"):
            content_type = "application/x-httpd-php"
        elif path.endswith(".json"):
            content_type = "application/json"
        elif path.endswith(".sql"):
            content_type = "application/sql"
        elif path.endswith(".zip"):
            content_type = "application/zip"
        
        # Contenu factice selon le type
        if path == "/config.php":
            content = """<?php
// === CONFIGURATION SERVEUR ===
define('DB_HOST', 'localhost');
define('DB_USER', 'admin');
define('DB_PASS', 'SuperSecretPassword123!');
define('DB_NAME', 'production_database');

// API Keys
$stripe_secret = 'sk_live_51KjT6zKjT6zKjT6zKjT6zKjT6';
$aws_access_key = 'AKIAIOSFODNN7EXAMPLE';
$aws_secret_key = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY';

// JWT Secret
$jwt_secret = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9';

// Admin credentials (hashed)
$admin_users = [
    'admin' => '$2y$10$EixZaYVk1WGbH8C8O5W0u8jXDWYVk1WGbH8C8O5W0u8jXDWYVk1WGbH8C8O5W0u8jXD',
    'root' => '$2y$10$EixZaYVk1WGbH8C8O5W0u8jXDWYVk1WGbH8C8O5W0u8jXDWYVk1WGbH8C8O5W0u8jXD'
];

// Debug mode (DEV ONLY)
$debug_mode = true;
$error_logging = true;

// Email configuration
$smtp_host = 'smtp.gmail.com';
$smtp_user = 'admin@company.com';
$smtp_pass = 'EmailPassword123!';
?>
"""
        elif path == "/.env":
            content = """# === ENVIRONMENT VARIABLES ===
NODE_ENV=production
DATABASE_URL=mysql://admin:SuperSecret123!@localhost:3306/prod_db
REDIS_URL=redis://:redis_password@localhost:6379
SESSION_SECRET=this-is-a-very-secret-session-key-123456
JWT_SECRET=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9

# API Keys
STRIPE_SECRET_KEY=sk_live_51KjT6zKjT6zKjT6zKjT6zKjT6
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
GITHUB_TOKEN=ghp_abcdef1234567890
SLACK_WEBHOOK=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=admin@company.com
SMTP_PASS=EmailPassword123!

# Debug
DEBUG=false
LOG_LEVEL=info
"""
        elif path == "/database.sql":
            content = """-- === DATABASE DUMP - PRODUCTION ===
-- Generated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """

CREATE DATABASE IF NOT EXISTS `production_db`;
USE `production_db`;

-- Users table
CREATE TABLE `users` (
    `id` INT PRIMARY KEY AUTO_INCREMENT,
    `username` VARCHAR(50) UNIQUE NOT NULL,
    `password_hash` VARCHAR(255) NOT NULL,
    `email` VARCHAR(100) UNIQUE NOT NULL,
    `role` ENUM('admin', 'user', 'moderator') DEFAULT 'user',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample users
INSERT INTO `users` (`username`, `password_hash`, `email`, `role`) VALUES
('admin', '$2y$10$EixZaYVk1WGbH8C8O5W0u8jXDWYVk1WGbH8C8O5W0u8jXDWYVk1WGbH8C8O5W0u8jXD', 'admin@company.com', 'admin'),
('john_doe', '$2y$10$EixZaYVk1WGbH8C8O5W0u8jXDWYVk1WGbH8C8O5W0u8jXDWYVk1WGbH8C8O5W0u8jXD', 'john@example.com', 'user'),
('jane_smith', '$2y$10$EixZaYVk1WGbH8C8O5W0u8jXDWYVk1WGbH8C8O5W0u8jXDWYVk1WGbH8C8O5W0u8jXD', 'jane@example.com', 'moderator');

-- API keys table
CREATE TABLE `api_keys` (
    `id` INT PRIMARY KEY AUTO_INCREMENT,
    `key` VARCHAR(64) UNIQUE NOT NULL,
    `user_id` INT,
    `permissions` TEXT,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
);

INSERT INTO `api_keys` (`key`, `user_id`, `permissions`) VALUES
('sk_live_1234567890abcdef', 1, 'read,write,admin'),
('sk_test_abcdef1234567890', 2, 'read');
"""
        else:
            # Contenu générique pour les autres fichiers
            content = f"""This is a fake {path} file for honeypot purposes.
Generated at: {datetime.now().isoformat()}
File path: {path}
Server: Local Honeypot Server
Purpose: Security research and bot detection

NOTE: This is not a real file. It's part of a security research honeypot.
All access is logged and monitored.

If you're seeing this, your IP and activity have been recorded for analysis.
"""
        
        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.send_header('Content-Disposition', f'attachment; filename="{path.split("/")[-1]}"')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))
    
    def serve_404_trap(self, path):
        """Page 404 qui sert aussi de piège"""
        html = f'''<!DOCTYPE html>
<html><head><title>404 Not Found</title></head>
<body>
<h1>404 - File Not Found</h1>
<p>The requested URL {path} was not found on this server.</p>
<hr>
<address>Local Honeypot Server</address>
<!-- Debug info: Path attempted: {path} -->
</body></html>'''
        
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Désactive les logs par défaut"""
        pass

def save_session_summary():
    """Sauvegarde le résumé de session lors de l'arrêt"""
    handler = HoneypotHandler
    session_data = handler.session_data.copy()
    
    # Convertir les sets en listes pour JSON
    session_data["unique_ips"] = list(session_data["unique_ips"])
    
    # Calculer des statistiques supplémentaires
    session_data["end_time"] = datetime.now().isoformat()
    session_data["duration_seconds"] = (datetime.fromisoformat(session_data["end_time"]) - 
                                       datetime.fromisoformat(session_data["start_time"])).total_seconds()
    
    # Top 5 des fichiers les plus accédés
    session_data["top_files"] = dict(sorted(
        session_data["file_access"].items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:5])
    
    # Top 5 des user-agents
    session_data["top_user_agents"] = dict(sorted(
        session_data["user_agents"].items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:5])
    
    # Distribution des types de bots
    bot_types = {}
    for ip_activities in session_data["bot_ips"].values():
        for activity in ip_activities:
            bot_type = activity.get("bot_type", "Unknown")
            bot_types[bot_type] = bot_types.get(bot_type, 0) + 1
    session_data["bot_type_distribution"] = bot_types
    
    # Sauvegarde JSON
    with open(SESSION_LOG, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2, default=str)
    
    print(f"\n💾 Résumé de session sauvegardé dans: {SESSION_LOG}")

def print_final_summary():
    """Affiche un résumé final dans la console"""
    handler = HoneypotHandler
    data = handler.session_data
    
    print("\n" + "="*70)
    print("📊 RÉSUMÉ FINAL DE LA SESSION HONEYPOT")
    print("="*70)
    print(f"⏱️  Durée: {data.get('duration_seconds', 0):.0f} secondes")
    print(f"📨 Requêtes totales: {data.get('total_requests', 0)}")
    print(f"🌐 IPs uniques: {len(data.get('unique_ips', []))}")
    
    if data.get('bot_type_distribution'):
        print(f"\n🤖 DISTRIBUTION DES BOTS:")
        for bot_type, count in data["bot_type_distribution"].items():
            percentage = (count / data["total_requests"] * 100) if data["total_requests"] > 0 else 0
            print(f"   • {bot_type}: {count} ({percentage:.1f}%)")
    
    if data.get('top_files'):
        print(f"\n📁 FICHIERS LES PLUS ACCÉDÉS:")
        for file_name, count in data["top_files"].items():
            print(f"   • {file_name}: {count} accès")
    
    if data.get('suspicious_activity'):
        print(f"\n🚨 ACTIVITÉS SUSPECTES: {len(data['suspicious_activity'])}")
        for activity in data["suspicious_activity"][-5:]:  # 5 dernières
            print(f"   • {activity['timestamp']} - {activity['ip']} - {activity['bot_type']}")
    
    print(f"\n📄 Logs détaillés: {LOG_FILE}")
    print(f"📊 Résumé JSON: {SESSION_LOG}")
    print("="*70)

def start_honeypot_server():
    """Démarre le serveur honeypot"""
    
    # Initialisation des fichiers de log
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"HONEYPOT SERVER LOGS\n")
        f.write(f"Started at: {datetime.now().isoformat()}\n")
        f.write("="*60 + "\n")
    
    local_ip = socket.gethostbyname(socket.gethostname())
    
    print("\n" + "="*70)
    print("🍯 HONEYPOT SERVER - PIÈGE À BOTS")
    print("="*70)
    print(f"📍 Adresse: http://{local_ip}:{PORT}")
    print(f"📍 Local: http://localhost:{PORT}")
    print(f"\n📂 {len(FAKE_FILES)} fichiers pièges disponibles:")
    for file_info in FAKE_FILES:
        print(f"   • {file_info['name']} → {file_info['path']}")
    
    print(f"\n📊 Logs:")
    print(f"   • {LOG_FILE} - Logs détaillés des bots")
    print(f"   • {SESSION_LOG} - Résumé de session (après arrêt)")
    print(f"\n🎯 Détection automatique des:")
    print(f"   • Web crawlers, Security scanners, Outils d'attaque")
    print(f"   • Scripts Python, CLI tools, Directory busters")
    print(f"\n✅ Serveur actif - En attente de connexions...")
    print("🛑 Ctrl+C pour arrêter et générer le rapport")
    print("="*70 + "\n")
    
    try:
        server = HTTPServer(('0.0.0.0', PORT), HoneypotHandler)
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt du serveur honeypot...")
        save_session_summary()
        print_final_summary()
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")

if __name__ == "__main__":
    start_honeypot_server()