#!/usr/bin/env python3
# ftp_honeypot_monitor.py - Détecte les intrusions sur ton serveur FTP via un honeypot
# Usage: python ftp_honeypot_monitor.py

import os
import sys
import json
import time
import hashlib
from datetime import datetime
import ftplib
import socket
import logging
from pathlib import Path

# ================= CONFIGURATION =================
CONFIG = {
    # Tes infos FTP
    'ftp_host': '192.168.1.00',      # IP de ton téléphone
    'ftp_port': 2221,              # Port FTP
    'ftp_user': 'android',             # Change si différent
    'ftp_pass': 'servertest',              # Change si différent
    
    # Fichier piège (honeypot)
    'honeypot_filename': 'photos_backup.zip',  # Nom attrayant
    'honeypot_content': 'Ceci est un fichier piège. Accès non autorisé détecté.',
    
    # Surveillance
    'check_interval': 30,            # Secondes entre chaque vérification
    'log_file': 'ftp_intrusions.json',
    'alert_file': 'alerts.txt',
    
    # Ton réseau autorisé
    'allowed_ips': ['192.168.1.'],   # Commence par (ton réseau)
    'allowed_macs': [],              # MAC addresses autorisées
}

# ================= HONEYPOT =================
class HoneyPot:
    def __init__(self, config):
        self.config = config
        self.ftp = None
        self.honeypot_path = config['honeypot_filename']
        self.setup_logging()
        
    def setup_logging(self):
        """Configure les logs"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('ftp_monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def connect_ftp(self):
        """Connection au FTP"""
        try:
            self.ftp = ftplib.FTP()
            self.ftp.connect(self.config['ftp_host'], self.config['ftp_port'])
            self.ftp.login(self.config['ftp_user'], self.config['ftp_pass'])
            self.logger.info(f"✅ Connecté à FTP: {self.config['ftp_host']}:{self.config['ftp_port']}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Erreur connexion FTP: {e}")
            return False
    
    def create_honeypot(self):
        """Crée le fichier piège"""
        try:
            # Vérifie si existe déjà
            files = []
            self.ftp.retrlines('LIST', files.append)
            
            honeypot_exists = any(self.config['honeypot_filename'] in f for f in files)
            
            if not honeypot_exists:
                # Crée un fichier texte "piège"
                temp_file = 'temp_honeypot.txt'
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(self.config['honeypot_content'])
                    f.write(f"\n\n--- Détection d'intrusion ---\n")
                    f.write(f"Créé le: {datetime.now()}\n")
                    f.write(f"Serveur: {self.config['ftp_host']}\n")
                
                # Upload sur FTP
                with open(temp_file, 'rb') as f:
                    self.ftp.storbinary(f'STOR {self.config["honeypot_filename"]}', f)
                
                os.remove(temp_file)
                self.logger.info(f"✅ Honeypot créé: {self.config['honeypot_filename']}")
            
            # Récupère hash pour comparaison future
            temp_file = 'temp_dl.txt'
            with open(temp_file, 'wb') as f:
                self.ftp.retrbinary(f'RETR {self.config["honeypot_filename"]}', f.write)
            
            with open(temp_file, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            
            os.remove(temp_file)
            
            # Sauvegarde le hash
            self.save_tracking('honeypot_created', {
                'filename': self.config['honeypot_filename'],
                'hash': file_hash,
                'created_at': datetime.now().isoformat()
            })
            
            return file_hash
            
        except Exception as e:
            self.logger.error(f"❌ Erreur création honeypot: {e}")
            return None
    
    def check_honeypot(self, original_hash):
        """Vérifie si le honeypot a été touché"""
        try:
            # Télécharge le fichier
            temp_file = 'temp_check.txt'
            with open(temp_file, 'wb') as f:
                self.ftp.retrbinary(f'RETR {self.config["honeypot_filename"]}', f.write)
            
            # Calcule le hash
            with open(temp_file, 'rb') as f:
                current_hash = hashlib.md5(f.read()).hexdigest()
            
            # Lit le contenu pour voir si modifié
            with open(temp_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            os.remove(temp_file)
            
            # Vérifie si changé
            if current_hash != original_hash:
                self.logger.critical(f"🚨 HONEYPOT MODIFIÉ! Ancien hash: {original_hash[:8]}, Nouveau: {current_hash[:8]}")
                
                # Analyse les changements
                self.analyze_intrusion(content)
                return False, current_hash
            
            # Vérifie si fichier déplacé/supprimé
            files = []
            self.ftp.retrlines('LIST', files.append)
            honeypot_found = any(self.config['honeypot_filename'] in f for f in files)
            
            if not honeypot_found:
                self.logger.critical(f"🚨 HONEYPOT SUPPRIMÉ!")
                self.save_tracking('honeypot_deleted', {
                    'filename': self.config['honeypot_filename'],
                    'deleted_at': datetime.now().isoformat()
                })
                return False, None
            
            return True, current_hash
            
        except Exception as e:
            self.logger.error(f"❌ Erreur vérification honeypot: {e}")
            return False, None
    
    def monitor_ftp_activity(self):
        """Surveille l'activité FTP"""
        try:
            # 1. Liste les fichiers
            files_before = []
            self.ftp.retrlines('LIST', files_before.append)
            
            # 2. Récupère les logs système si disponibles
            system_info = self.get_system_info()
            
            # 3. Vérifie les connexions actives
            connections = self.check_active_connections()
            
            # Log l'activité
            activity = {
                'timestamp': datetime.now().isoformat(),
                'files_count': len(files_before),
                'files': [f.split()[-1] for f in files_before[-5:]],  # 5 derniers fichiers
                'connections': connections,
                'system': system_info
            }
            
            self.save_tracking('ftp_activity', activity)
            
            # Vérifie activité suspecte
            self.detect_suspicious_activity(files_before, connections)
            
        except Exception as e:
            self.logger.error(f"❌ Erreur monitoring: {e}")
    
    def get_system_info(self):
        """Récupère des infos système"""
        try:
            # Sur certains FTP, on peut avoir des infos
            welcome_msg = self.ftp.getwelcome()
            system_type = self.ftp.sendcmd('SYST')
            
            return {
                'welcome': welcome_msg[:100],
                'system': system_type,
                'host': self.config['ftp_host']
            }
        except:
            return {'host': self.config['ftp_host']}
    
    def check_active_connections(self):
        """Vérifie les connexions actives au serveur"""
        # Méthode 1: Scan réseau
        connections = []
        
        # Méthode 2: Vérifie si notre fichier est accédé
        try:
            # Modifie légèrement le honeypot pour timestamp d'accès
            temp_file = 'temp_access.txt'
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(f"Dernier accès: {datetime.now()}")
            
            with open(temp_file, 'rb') as f:
                self.ftp.storbinary(f'STOR .access_log.txt', f)
            
            os.remove(temp_file)
            
        except:
            pass
        
        return connections
    
    def detect_suspicious_activity(self, files_list, connections):
        """Détecte activité suspecte"""
        suspicious_patterns = [
            '.exe', '.bat', '.sh', '.php', '.py',  # Fichiers exécutables
            'password', 'passwd', 'config', '.env', # Fichiers sensibles
            'miner', 'crypto', 'xmr',               # Minage
        ]
        
        for file_info in files_list:
            filename = file_info.split()[-1] if len(file_info.split()) > 0 else ""
            
            for pattern in suspicious_patterns:
                if pattern in filename.lower():
                    self.logger.warning(f"⚠️  Fichier suspect: {filename}")
                    
                    self.save_tracking('suspicious_file', {
                        'filename': filename,
                        'pattern': pattern,
                        'detected_at': datetime.now().isoformat(),
                        'full_info': file_info
                    })
    
    def analyze_intrusion(self, honeypot_content):
        """Analyse l'intrusion détectée"""
        timestamp = datetime.now()
        
        # Extrait des infos du contenu
        lines = honeypot_content.split('\n')
        intrusion_data = {
            'timestamp': timestamp.isoformat(),
            'content_length': len(honeypot_content),
            'lines_count': len(lines),
            'sample_content': honeypot_content[:500],
            'possible_attacker_ip': self.get_client_ip(),
            'ftp_server': f"{self.config['ftp_host']}:{self.config['ftp_port']}"
        }
        
        # Sauvegarde l'alerte
        self.save_tracking('intrusion_detected', intrusion_data)
        
        # Crée un fichier d'alerte
        alert_msg = f"""
        ╔══════════════════════════════════════════════════════════╗
        ║                    ALERTE INTRUSION FTP                  ║
        ╚══════════════════════════════════════════════════════════╝
        
        Date: {timestamp}
        Serveur: {self.config['ftp_host']}:{self.config['ftp_port']}
        Fichier piège: {self.config['honeypot_filename']}
        
        📋 Données collectées:
        - Taille contenu: {len(honeypot_content)} caractères
        - IP possible: {self.get_client_ip()}
        
        🚨 Actions recommandées:
        1. Déconnecter le serveur FTP immédiatement
        2. Changer tous les mots de passe
        3. Scanner ton réseau avec le security_desk.py
        4. Vérifier les logs de connexion
        
        Contenu modifié:
        {honeypot_content[:300]}...
        """
        
        with open(self.config['alert_file'], 'a', encoding='utf-8') as f:
            f.write(alert_msg)
            f.write('\n' + '='*80 + '\n\n')
        
        self.logger.critical(f"🚨 ALERTE SAUVEGARDÉE DANS: {self.config['alert_file']}")
    
    def get_client_ip(self):
        """Essaie de déterminer l'IP du client"""
        try:
            # Méthode simple : ton IP locale
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            return local_ip
        except:
            return "Inconnue"
    
    def save_tracking(self, event_type, data):
        """Sauvegarde les données de tracking"""
        try:
            # Charge les données existantes
            if os.path.exists(self.config['log_file']):
                with open(self.config['log_file'], 'r', encoding='utf-8') as f:
                    try:
                        all_data = json.load(f)
                    except:
                        all_data = []
            else:
                all_data = []
            
            # Ajoute le nouvel événement
            event = {
                'event': event_type,
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            all_data.append(event)
            
            # Sauvegarde
            with open(self.config['log_file'], 'w', encoding='utf-8') as f:
                json.dump(all_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"📝 Événement enregistré: {event_type}")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur sauvegarde logs: {e}")
    
    def generate_report(self):
        """Génère un rapport de sécurité"""
        if not os.path.exists(self.config['log_file']):
            return
        
        with open(self.config['log_file'], 'r', encoding='utf-8') as f:
            logs = json.load(f)
        
        report_file = f"security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"RAPPORT DE SÉCURITÉ FTP\n")
            f.write(f"Généré le: {datetime.now()}\n")
            f.write(f"Période: {logs[0]['timestamp'] if logs else 'N/A'} à maintenant\n")
            f.write("="*60 + "\n\n")
            
            # Résumé
            intrusions = [l for l in logs if l['event'] == 'intrusion_detected']
            suspicious = [l for l in logs if l['event'] == 'suspicious_file']
            
            f.write(f"📊 STATISTIQUES:\n")
            f.write(f"  • Total événements: {len(logs)}\n")
            f.write(f"  • Intrusions détectées: {len(intrusions)}\n")
            f.write(f"  • Fichiers suspects: {len(suspicious)}\n\n")
            
            # Dernières alertes
            f.write(f"🚨 DERNIÈRES ALERTES:\n")
            for log in logs[-5:]:
                f.write(f"  [{log['timestamp']}] {log['event']}\n")
        
        self.logger.info(f"📄 Rapport généré: {report_file}")
        return report_file
    
    def run(self):
        """Lance la surveillance"""
        self.logger.info("🚀 Démarrage surveillance FTP...")
        
        if not self.connect_ftp():
            return
        
        # Crée le honeypot
        original_hash = self.create_honeypot()
        if not original_hash:
            self.logger.error("❌ Impossible de créer le honeypot")
            return
        
        self.logger.info("✅ Surveillance active. Ctrl+C pour arrêter.")
        
        check_count = 0
        try:
            while True:
                check_count += 1
                
                # Vérifie honeypot
                is_ok, new_hash = self.check_honeypot(original_hash)
                
                if not is_ok:
                    # Intrusion détectée
                    self.logger.critical("🚨 INTRUSION - Arrêt de la surveillance")
                    break
                
                # Surveille activité générale
                self.monitor_ftp_activity()
                
                # Rapport périodique
                if check_count % 10 == 0:  # Toutes les 10 vérifications
                    self.generate_report()
                    self.logger.info(f"✅ Vérification #{check_count} - Tout est normal")
                
                # Attend avant prochaine vérification
                time.sleep(self.config['check_interval'])
                
        except KeyboardInterrupt:
            self.logger.info("⏹️  Surveillance arrêtée par l'utilisateur")
        except Exception as e:
            self.logger.error(f"❌ Erreur surveillance: {e}")
        finally:
            if self.ftp:
                self.ftp.quit()
            
            # Génère un rapport final
            self.generate_report()
            self.logger.info("👋 Surveillance terminée")

# ================= LANCEUR =================
if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                 HONEYPOT FTP MONITOR                     ║
    ║            Détection d'intrusion sur serveur FTP         ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Vérifie la config
    print(f"📍 Configuration:")
    print(f"  • Serveur FTP: {CONFIG['ftp_host']}:{CONFIG['ftp_port']}")
    print(f"  • Fichier piège: {CONFIG['honeypot_filename']}")
    print(f"  • Vérification toutes les: {CONFIG['check_interval']}s")
    print(f"  • Logs: {CONFIG['log_file']}")
    print()
    
    # Demande confirmation
    response = input("Démarrer la surveillance? (o/n): ")
    if response.lower() != 'o':
        print("❌ Annulé")
        sys.exit(0)
    
    # Lance
    honeypot = HoneyPot(CONFIG)
    honeypot.run()