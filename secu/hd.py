# - Terminal de surveillance système -
# 📜 CORRESPONDANCE COMMANDES / FONCTIONS :

# Dans ce tool |	Équivalent en CMD/PowerShell	                           |    Ce que ça évite de faire manuellement
# scan	        tasklist /v | findstr /i "cpu memory" + tri + calcul	        Voir CPU% et RAM% de CHAQUE processus, trier, chercher les gourmands
# kill chrome	taskkill /f /im chrome.exe	                                    OK celle-là est simple, mais avec PID c'est chiant
# kill 1234	    taskkill /f /pid 1234	                                        Trouver le bon PID dans tasklist d'abord
# net	        netstat -ano | findstr ESTABLISHED + tasklist pour chaque PID	Croiser PID avec noms de processus, chercher ports suspects
# disk	        wmic logicaldisk get size,freespace,caption + calcul Go	        Convertir bytes en Go, calculer pourcentages
# info	        systeminfo + wmic cpu get + wmic memorychip get	                Extraire infos pertinentes dans 50 lignes
# full	        TOUTES les commandes ci-dessus + analyse automatique	        5 minutes de copier-coller dans 3 fenêtres

import os
import sys
import psutil
import platform
import socket
import subprocess
import time
from datetime import datetime
import threading
from collections import defaultdict
import json

# ================= CONFIGURATION COULEURS =================
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# ================= UTILITAIRES =================
def clear_screen():
    """Efface l'écran"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Affiche l'en-tête stylé"""
    clear_screen()
    print(f"""{Colors.CYAN}
╔══════════════════════════════════════════════════════════════╗
║                   SECURITY DESK v1.0                         ║
║               Terminal de surveillance système               ║
╚══════════════════════════════════════════════════════════════╝{Colors.END}
""")

def print_menu():
    """Affiche le menu principal"""
    print(f"""
{Colors.BOLD}MENU PRINCIPAL:{Colors.END}
{Colors.GREEN}[1]{Colors.END} Scan système complet
{Colors.GREEN}[2]{Colors.END} Scanner les processus
{Colors.GREEN}[3]{Colors.END} Scanner le réseau
{Colors.GREEN}[4]{Colors.END} Scanner les disques
{Colors.GREEN}[5]{Colors.END} Informations système
{Colors.GREEN}[6]{Colors.END} Surveiller en temps réel
{Colors.GREEN}[7]{Colors.END} Quitter

{Colors.YELLOW}Commandes directes:{Colors.END}
• {Colors.CYAN}scan-all{Colors.END}     : Scan complet
• {Colors.CYAN}scan-proc{Colors.END}    : Scanner processus
• {Colors.CYAN}scan-net{Colors.END}     : Scanner réseau
• {Colors.CYAN}scan-disk{Colors.END}    : Scanner disques
• {Colors.CYAN}kill NOM{Colors.END}     : Tuer un processus
• {Colors.CYAN}info{Colors.END}         : Infos système
• {Colors.CYAN}help{Colors.END}         : Aide
• {Colors.CYAN}quit{Colors.END}         : Quitter
""")

# ================= FONCTIONS DE SCAN =================
class SystemScanner:
    def __init__(self):
        self.alerts = []
        self.suspect_processes = []
        
    def add_alert(self, level, message):
        """Ajoute une alerte avec niveau de sévérité"""
        colors = {
            'HIGH': Colors.RED,
            'MEDIUM': Colors.YELLOW,
            'LOW': Colors.CYAN,
            'INFO': Colors.GREEN
        }
        self.alerts.append({
            'level': level,
            'message': message,
            'color': colors.get(level, Colors.END),
            'time': datetime.now().strftime('%H:%M:%S')
        })
    
    def scan_processes(self, detailed=False):
        """Scan les processus avec détection de comportements suspects"""
        print(f"\n{Colors.BOLD}🔍 SCAN DES PROCESSUS{Colors.END}")
        print(f"{Colors.CYAN}{'='*80}{Colors.END}")
        
        suspect_keywords = [
            'miner', 'coin', 'xmr', 'monero', 'bitcoin',
            'atiesrxx', 'svchost', 'java', 'python', 'powershell',
            'cmd', 'wscript', 'cscript', 'update', 'service'
        ]
        
        high_cpu_processes = []
        high_memory_processes = []
        hidden_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'exe', 'username']):
            try:
                pinfo = proc.info
                
                # Détection CPU élevé
                if pinfo['cpu_percent'] > 50:
                    high_cpu_processes.append(pinfo)
                    self.add_alert('HIGH', 
                        f"Processus gourmand CPU: {pinfo['name']} ({pinfo['pid']}) - {pinfo['cpu_percent']}% CPU")
                
                # Détection mémoire élevée
                if pinfo['memory_percent'] > 10:
                    high_memory_processes.append(pinfo)
                    self.add_alert('MEDIUM',
                        f"Processus gourmand mémoire: {pinfo['name']} - {pinfo['memory_percent']:.1f}% RAM")
                
                # Détection de noms suspects
                proc_name_lower = pinfo['name'].lower()
                for keyword in suspect_keywords:
                    if keyword in proc_name_lower:
                        self.add_alert('HIGH',
                            f"Processus suspect détecté: {pinfo['name']} (contient '{keyword}')")
                        self.suspect_processes.append(pinfo)
                        break
                
                # Chemin suspect
                if pinfo['exe']:
                    suspicious_paths = ['temp', 'appdata', 'roaming', 'downloads']
                    exe_lower = pinfo['exe'].lower()
                    if any(path in exe_lower for path in suspicious_paths):
                        self.add_alert('MEDIUM',
                            f"Processus dans dossier suspect: {pinfo['name']} -> {pinfo['exe']}")
                
                if detailed:
                    status = f"{Colors.RED}⚠️ SUSPECT{Colors.END}" if pinfo in self.suspect_processes else f"{Colors.GREEN}✓ NORMAL{Colors.END}"
                    print(f"{pinfo['name']:30} PID:{pinfo['pid']:6} CPU:{pinfo['cpu_percent']:5.1f}% "
                          f"MEM:{pinfo['memory_percent']:5.1f}% USER:{pinfo['username']:15} {status}")
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Résumé
        print(f"\n{Colors.BOLD}📊 RÉSUMÉ:{Colors.END}")
        print(f"  • Processus analysés: {len(list(psutil.process_iter()))}")
        print(f"  • Processus gourmands CPU: {len(high_cpu_processes)}")
        print(f"  • Processus gourmands mémoire: {len(high_memory_processes)}")
        print(f"  • Processus suspects: {len(self.suspect_processes)}")
        
        return self.suspect_processes
    
    def scan_network(self):
        """Scan les connexions réseau"""
        print(f"\n{Colors.BOLD}🌐 SCAN RÉSEAU{Colors.END}")
        print(f"{Colors.CYAN}{'='*80}{Colors.END}")
        
        suspicious_ports = [3333, 4444, 5555, 6666, 7777, 8080, 8333, 9333, 9999]
        mining_pools = ['xmr', 'monero', 'nanopool', 'minexmr', 'supportxmr']
        
        connections = []
        for conn in psutil.net_connections(kind='inet'):
            try:
                if conn.status == 'ESTABLISHED' and conn.raddr:
                    ip, port = conn.raddr
                    
                    # Détection ports suspects
                    if port in suspicious_ports:
                        self.add_alert('HIGH',
                            f"Connexion sur port suspect {port} vers {ip}")
                    
                    # Trouver le processus associé
                    proc_name = "Inconnu"
                    if conn.pid:
                        try:
                            proc = psutil.Process(conn.pid)
                            proc_name = proc.name()
                        except:
                            pass
                    
                    connections.append({
                        'proto': 'TCP',
                        'local': f"{conn.laddr.ip}:{conn.laddr.port}",
                        'remote': f"{ip}:{port}",
                        'status': conn.status,
                        'pid': conn.pid,
                        'process': proc_name
                    })
                    
                    print(f"{proc_name:25} {ip:20}:{port:<6} {conn.status:12}")
                    
            except (AttributeError, IndexError):
                continue
        
        # Infos réseau système
        print(f"\n{Colors.BOLD}📡 INFOS RÉSEAU SYSTÈME:{Colors.END}")
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            print(f"  • Hostname: {hostname}")
            print(f"  • IP locale: {local_ip}")
            
            # IP publique (si connecté)
            try:
                import urllib.request
                external_ip = urllib.request.urlopen('https://api.ipify.org').read().decode('utf8')
                print(f"  • IP publique: {external_ip}")
            except:
                print(f"  • IP publique: {Colors.YELLOW}Non disponible{Colors.END}")
                
        except Exception as e:
            print(f"  • Erreur: {e}")
        
        return connections
    
    def scan_disks(self):
        """Scan l'utilisation des disques"""
        print(f"\n{Colors.BOLD}💾 SCAN DES DISQUES{Colors.END}")
        print(f"{Colors.CYAN}{'='*80}{Colors.END}")
        
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                
                # Alertes si espace faible
                if usage.percent > 90:
                    self.add_alert('HIGH',
                        f"Disque presque plein: {partition.device} ({usage.percent}%)")
                elif usage.percent > 80:
                    self.add_alert('MEDIUM',
                        f"Disque rempli à {usage.percent}%: {partition.device}")
                
                # Affichage
                color = Colors.RED if usage.percent > 90 else Colors.YELLOW if usage.percent > 80 else Colors.GREEN
                print(f"{partition.device:20} {partition.mountpoint:15} "
                      f"{color}{usage.percent:6.1f}%{Colors.END} "
                      f"Libre: {usage.free / (1024**3):.1f}Go / {usage.total / (1024**3):.1f}Go")
                
            except PermissionError:
                print(f"{partition.device:20} {partition.mountpoint:15} {Colors.RED}ACCÈS REFUSÉ{Colors.END}")
    
    def scan_system_info(self):
        """Affiche les informations système"""
        print(f"\n{Colors.BOLD}🖥️  INFORMATIONS SYSTÈME{Colors.END}")
        print(f"{Colors.CYAN}{'='*80}{Colors.END}")
        
        # CPU
        print(f"{Colors.BOLD}CPU:{Colors.END}")
        print(f"  • Cores: {psutil.cpu_count(logical=True)}")
        print(f"  • Fréquence: {psutil.cpu_freq().current:.0f} MHz")
        print(f"  • Utilisation: {psutil.cpu_percent(interval=1)}%")
        
        # Mémoire
        mem = psutil.virtual_memory()
        print(f"\n{Colors.BOLD}MÉMOIRE:{Colors.END}")
        print(f"  • Totale: {mem.total / (1024**3):.1f} Go")
        print(f"  • Disponible: {mem.available / (1024**3):.1f} Go")
        print(f"  • Utilisée: {mem.percent}%")
        
        # Système
        print(f"\n{Colors.BOLD}SYSTÈME:{Colors.END}")
        print(f"  • OS: {platform.system()} {platform.release()}")
        print(f"  • Version: {platform.version()}")
        print(f"  • Machine: {platform.machine()}")
        print(f"  • Processeur: {platform.processor()}")
        
        # Boot
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        print(f"  • Démarré le: {boot_time.strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"  • Uptime: {uptime}")
    
    def full_scan(self):
        """Scan complet du système"""
        print(f"\n{Colors.BOLD}🚀 SCAN COMPLET DU SYSTÈME{Colors.END}")
        print(f"{Colors.CYAN}{'='*80}{Colors.END}")
        
        print(f"{Colors.YELLOW}⏳ Démarrage du scan...{Colors.END}")
        
        # Scanner dans l'ordre
        self.scan_system_info()
        self.scan_processes(detailed=False)
        self.scan_network()
        self.scan_disks()
        
        # Afficher les alertes
        self.show_alerts()
        
        return self.alerts
    
    def show_alerts(self):
        """Affiche toutes les alertes"""
        if not self.alerts:
            print(f"\n{Colors.GREEN}✅ Aucune alerte détectée{Colors.END}")
            return
        
        print(f"\n{Colors.BOLD}🚨 ALERTES DÉTECTÉES ({len(self.alerts)}){Colors.END}")
        print(f"{Colors.CYAN}{'='*80}{Colors.END}")
        
        for alert in self.alerts:
            print(f"[{alert['time']}] {alert['color']}[{alert['level']}]{Colors.END} {alert['message']}")
    
    def kill_process(self, process_name):
        """Tue un processus par nom"""
        killed = 0
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                if proc.info['name'].lower() == process_name.lower():
                    proc.kill()
                    print(f"{Colors.GREEN}✅ Processus tué: {proc.info['name']} (PID: {proc.info['pid']}){Colors.END}")
                    killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if killed == 0:
            print(f"{Colors.YELLOW}⚠️  Aucun processus trouvé avec le nom: {process_name}{Colors.END}")
        return killed
    
    def real_time_monitor(self, duration=30):
        """Surveillance en temps réel"""
        print(f"\n{Colors.BOLD}📊 SURVEILLANCE TEMPS RÉEL ({duration}s){Colors.END}")
        print(f"{Colors.CYAN}{'='*80}{Colors.END}")
        print("Appuyez sur Ctrl+C pour arrêter\n")
        
        end_time = time.time() + duration
        try:
            while time.time() < end_time:
                clear_screen()
                print_header()
                
                # CPU
                cpu_percent = psutil.cpu_percent(interval=1)
                cpu_color = Colors.RED if cpu_percent > 80 else Colors.YELLOW if cpu_percent > 50 else Colors.GREEN
                print(f"{Colors.BOLD}CPU:{Colors.END} {cpu_color}{'█' * int(cpu_percent/2)}{'░' * (50 - int(cpu_percent/2))} {cpu_percent:.1f}%{Colors.END}")
                
                # Mémoire
                mem = psutil.virtual_memory()
                mem_color = Colors.RED if mem.percent > 80 else Colors.YELLOW if mem.percent > 50 else Colors.GREEN
                print(f"{Colors.BOLD}RAM:{Colors.END} {mem_color}{'█' * int(mem.percent/2)}{'░' * (50 - int(mem.percent/2))} {mem.percent:.1f}%{Colors.END}")
                
                # Top 5 processus CPU
                print(f"\n{Colors.BOLD}TOP 5 PROCESSUS (CPU):{Colors.END}")
                for proc in sorted(psutil.process_iter(['name', 'cpu_percent']), 
                                 key=lambda p: p.info['cpu_percent'], reverse=True)[:5]:
                    if proc.info['cpu_percent'] > 0:
                        print(f"  {proc.info['name']:25} {proc.info['cpu_percent']:5.1f}%")
                
                # Connexions réseau
                conn_count = len(psutil.net_connections(kind='inet'))
                print(f"\n{Colors.BOLD}CONNEXIONS:{Colors.END} {conn_count} actives")
                
                time.sleep(2)
                
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}⏹️  Surveillance arrêtée{Colors.END}")

# ================= INTERFACE UTILISATEUR =================
def main():
    scanner = SystemScanner()
    
    while True:
        print_header()
        print_menu()
        
        try:
            choice = input(f"\n{Colors.BOLD}security-desk>{Colors.END} ").strip().lower()
            
            if choice in ['7', 'quit', 'exit', 'q']:
                print(f"\n{Colors.GREEN}👋 Au revoir !{Colors.END}")
                break
            
            elif choice in ['1', 'scan-all']:
                scanner.full_scan()
                
            elif choice in ['2', 'scan-proc']:
                scanner.scan_processes(detailed=True)
                
            elif choice in ['3', 'scan-net']:
                scanner.scan_network()
                
            elif choice in ['4', 'scan-disk']:
                scanner.scan_disks()
                
            elif choice in ['5', 'info']:
                scanner.scan_system_info()
                
            elif choice in ['6', 'monitor']:
                scanner.real_time_monitor(duration=30)
            
            elif choice.startswith('kill '):
                proc_name = choice[5:].strip()
                if proc_name:
                    scanner.kill_process(proc_name)
                else:
                    print(f"{Colors.YELLOW}Usage: kill NOM_PROCESSUS{Colors.END}")
            
            elif choice == 'help':
                print_menu()
            
            elif choice == 'clear':
                clear_screen()
                continue
                
            else:
                print(f"{Colors.YELLOW}Commande non reconnue. Tapez 'help' pour la liste.{Colors.END}")
            
            # Pause pour lire les résultats
            input(f"\n{Colors.CYAN}Appuyez sur Entrée pour continuer...{Colors.END}")
            
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}\n⚠️  Interrompu. Tapez 'quit' pour quitter.{Colors.END}")
            time.sleep(1)
        except Exception as e:
            print(f"{Colors.RED}❌ Erreur: {e}{Colors.END}")
            time.sleep(2)

# ================= INSTALLATION =================
def check_dependencies():
    """Vérifie et installe les dépendances"""
    try:
        import psutil
    except ImportError:
        print(f"{Colors.YELLOW}Installation de psutil...{Colors.END}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
        print(f"{Colors.GREEN}✅ psutil installé{Colors.END}")

# ================= POINT D'ENTRÉE =================
if __name__ == "__main__":
    try:
        check_dependencies()
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.GREEN}👋 Au revoir !{Colors.END}")
    except Exception as e:
        print(f"{Colors.RED}❌ Erreur critique: {e}{Colors.END}")
        import traceback
        traceback.print_exc()