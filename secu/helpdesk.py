# - Terminal de surveillance système HELP DESK PRO -
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
import signal
import getpass
import ctypes
from typing import List, Dict, Any
import warnings
warnings.filterwarnings('ignore')

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
    
    # Couleurs de statut
    CRITICAL = '\033[41m'  # Fond rouge
    WARNING = '\033[43m\033[30m'  # Fond jaune, texte noir
    INFO = '\033[44m'  # Fond bleu

# ================= HISTORIQUE =================
class CommandHistory:
    def __init__(self, max_size=50):
        self.history = []
        self.max_size = max_size
        self.current_index = -1
        
    def add(self, command: str):
        """Ajoute une commande à l'historique"""
        if command and (not self.history or command != self.history[-1]):
            self.history.append(command)
            if len(self.history) > self.max_size:
                self.history.pop(0)
        self.current_index = len(self.history)
    
    def get_previous(self):
        """Récupère la commande précédente"""
        if not self.history:
            return ""
        self.current_index = max(0, self.current_index - 1)
        return self.history[self.current_index]
    
    def get_next(self):
        """Récupère la commande suivante"""
        if not self.history:
            return ""
        self.current_index = min(len(self.history), self.current_index + 1)
        if self.current_index >= len(self.history):
            return ""
        return self.history[self.current_index]

# ================= UTILITAIRES =================
def clear_screen():
    """Efface l'écran"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Affiche l'en-tête stylé"""
    print(f"""{Colors.CYAN}
╔══════════════════════════════════════════════════════════════════════════╗
║                   HELP DESK PRO - Terminal de surveillance               ║
║                 Historique conservé | Pas de clear intempestif           ║
╚══════════════════════════════════════════════════════════════════════════╝{Colors.END}
""")

def print_status_bar(scanner):
    """Affiche une barre de statut en haut avec les infos critiques"""
    mem = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=0.1)
    
    # Couleurs selon l'utilisation
    cpu_color = Colors.RED if cpu_percent > 80 else Colors.YELLOW if cpu_percent > 60 else Colors.GREEN
    mem_color = Colors.RED if mem.percent > 80 else Colors.YELLOW if mem.percent > 60 else Colors.GREEN
    
    alerts_count = len([a for a in scanner.alerts if a['level'] in ['HIGH', 'CRITICAL']])
    alert_color = Colors.RED if alerts_count > 0 else Colors.GREEN
    
    status = f"{Colors.BOLD}📊 STATUT: {cpu_color}CPU:{cpu_percent:.1f}%{Colors.END} | " \
             f"{mem_color}RAM:{mem.percent:.1f}%{Colors.END} | " \
             f"{alert_color}Alertes:{alerts_count}{Colors.END} | " \
             f"Processus:{len(list(psutil.process_iter()))}"
    
    print(f"{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"{status}")
    print(f"{Colors.CYAN}{'='*80}{Colors.END}\n")

def print_menu(compact=False):
    """Affiche le menu principal (version compacte pour ne pas spammer l'écran)"""
    if not compact:
        print(f"""
{Colors.BOLD}MENU PRINCIPAL:{Colors.END}
{Colors.GREEN}[1]{Colors.END} Scan complet      {Colors.GREEN}[5]{Colors.END} Infos système
{Colors.GREEN}[2]{Colors.END} Processus         {Colors.GREEN}[6]{Colors.END} Monitoring temps réel
{Colors.GREEN}[3]{Colors.END} Réseau            {Colors.GREEN}[7]{Colors.END} Analyse malware
{Colors.GREEN}[4]{Colors.END} Disques           {Colors.GREEN}[8]{Colors.END} Quitter

{Colors.YELLOW}Commandes rapides:{Colors.END}
• {Colors.CYAN}scan{Colors.END}              : Scan complet rapide
• {Colors.CYAN}proc{Colors.END}              : Lister processus avec détails
• {Colors.CYAN}net{Colors.END}               : Connexions réseau
• {Colors.CYAN}disk{Colors.END}              : Espace disque
• {Colors.CYAN}kill NOM{Colors.END}          : Tuer processus par nom
• {Colors.CYAN}killpid PID{Colors.END}       : Tuer par PID
• {Colors.CYAN}find NOM{Colors.END}          : Rechercher processus
• {Colors.CYAN}info{Colors.END}              : Infos système détaillées
• {Colors.CYAN}alert{Colors.END}             : Voir alertes
• {Colors.CYAN}log{Colors.END}               : Sauvegarder log
• {Colors.CYAN}clear{Colors.END}             : Effacer l'écran
• {Colors.CYAN}help{Colors.END}              : Afficher ce menu
• {Colors.CYAN}quit{Colors.END}              : Quitter
""")
    else:
        print(f"{Colors.YELLOW}📋 Tapez 'help' pour le menu complet ou une commande ci-dessus{Colors.END}")

# ================= FONCTIONS DE SCAN AMELIOREES =================
class SystemScanner:
    def __init__(self):
        self.alerts = []
        self.suspect_processes = []
        self.scan_history = []
        self.performance_log = []
        self.log_file = f"helpdesk_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
    def add_alert(self, level, message, process_info=None):
        """Ajoute une alerte avec niveau de sévérité"""
        colors = {
            'CRITICAL': Colors.CRITICAL,
            'HIGH': Colors.RED,
            'MEDIUM': Colors.YELLOW,
            'LOW': Colors.CYAN,
            'INFO': Colors.GREEN
        }
        alert = {
            'level': level,
            'message': message,
            'color': colors.get(level, Colors.END),
            'time': datetime.now().strftime('%H:%M:%S'),
            'process': process_info
        }
        self.alerts.append(alert)
        
        # Log immédiat si critique
        if level in ['CRITICAL', 'HIGH']:
            self._log_to_file(alert)
        return alert
    
    def _log_to_file(self, alert):
        """Log une alerte dans le fichier"""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'level': alert['level'],
                'message': alert['message'],
                'process': alert['process']
            }
            
            # Charger les logs existants ou créer nouveau
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(log_entry)
            
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"{Colors.RED}❌ Erreur de log: {e}{Colors.END}")
    
    def scan_processes(self, detailed=False, sort_by='cpu'):
        """Scan les processus avec détection de comportements suspects"""
        print(f"\n{Colors.BOLD}🔍 SCAN DES PROCESSUS - {datetime.now().strftime('%H:%M:%S')}{Colors.END}")
        print(f"{Colors.CYAN}{'='*100}{Colors.END}")
        
        # Patterns de processus suspects
        suspect_patterns = {
            'miner': ['miner', 'coin', 'xmr', 'monero', 'bitcoin', 'eth', 'ether', 'cryptonight'],
            'injection': ['inject', 'hook', 'dllinject', 'processhacker'],
            'scripting': ['powershell', 'wscript', 'cscript', 'cmd', 'python', 'perl', 'bash'],
            'system_abuse': ['svchost', 'services', 'lsass', 'winlogon', 'csrss'],
            'obfuscation': ['setup', 'install', 'update', 'updater', 'java', 'runtime']
        }
        
        # Collecte des données processus
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 
                                        'exe', 'username', 'create_time', 'num_threads', 
                                        'num_handles', 'ppid', 'status']):
            try:
                pinfo = proc.info
                with proc.oneshot():
                    pinfo['memory_mb'] = proc.memory_info().rss / (1024 * 1024)
                    pinfo['cpu_time'] = proc.cpu_times()
                    pinfo['connections'] = len(proc.connections())
                    pinfo['io_counters'] = proc.io_counters() if proc.io_counters() else None
                
                # Analyse de risques
                pinfo['risk_score'] = 0
                pinfo['flags'] = []
                
                # Détection CPU élevé
                if pinfo['cpu_percent'] > 70:
                    pinfo['risk_score'] += 3
                    pinfo['flags'].append('HIGH_CPU')
                    self.add_alert('HIGH', 
                        f"Processus gourmand CPU: {pinfo['name']} (PID:{pinfo['pid']}) - {pinfo['cpu_percent']}% CPU",
                        pinfo)
                
                # Détection mémoire élevée
                if pinfo['memory_percent'] > 15 or pinfo['memory_mb'] > 500:
                    pinfo['risk_score'] += 2
                    pinfo['flags'].append('HIGH_MEM')
                    self.add_alert('MEDIUM',
                        f"Processus gourmand mémoire: {pinfo['name']} - {pinfo['memory_mb']:.1f}MB ({pinfo['memory_percent']:.1f}%)",
                        pinfo)
                
                # Nombre de threads suspect
                if pinfo.get('num_threads', 0) > 50:
                    pinfo['risk_score'] += 1
                    pinfo['flags'].append('MANY_THREADS')
                
                # Nombre de handles suspect
                if pinfo.get('num_handles', 0) > 1000:
                    pinfo['risk_score'] += 2
                    pinfo['flags'].append('MANY_HANDLES')
                
                # Détection de patterns suspects
                proc_name_lower = pinfo['name'].lower()
                for category, keywords in suspect_patterns.items():
                    for keyword in keywords:
                        if keyword in proc_name_lower:
                            pinfo['risk_score'] += 3
                            pinfo['flags'].append(f'SUSPECT_{category.upper()}')
                            self.add_alert('HIGH',
                                f"Processus suspect ({category}): {pinfo['name']} (contient '{keyword}')",
                                pinfo)
                            break
                
                # Chemin suspect
                if pinfo['exe']:
                    suspicious_paths = ['temp', 'appdata', 'roaming', 'downloads', 'cache']
                    exe_lower = pinfo['exe'].lower()
                    if any(path in exe_lower for path in suspicious_paths):
                        pinfo['risk_score'] += 2
                        pinfo['flags'].append('SUSPECT_PATH')
                        self.add_alert('MEDIUM',
                            f"Processus dans dossier suspect: {pinfo['name']} -> {pinfo['exe']}",
                            pinfo)
                
                # Parent PID suspect (injection possible)
                if pinfo['ppid'] and pinfo['ppid'] != 0:
                    try:
                        parent = psutil.Process(pinfo['ppid'])
                        if parent.name().lower() != 'explorer.exe' and 'svchost' not in parent.name().lower():
                            pinfo['risk_score'] += 1
                            pinfo['flags'].append('SUSPECT_PARENT')
                    except:
                        pass
                
                processes.append(pinfo)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Tri selon le critère
        if sort_by == 'cpu':
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        elif sort_by == 'memory':
            processes.sort(key=lambda x: x['memory_mb'], reverse=True)
        elif sort_by == 'risk':
            processes.sort(key=lambda x: x['risk_score'], reverse=True)
        elif sort_by == 'name':
            processes.sort(key=lambda x: x['name'].lower())
        
        # Affichage détaillé
        if detailed:
            print(f"{'Nom':25} {'PID':>6} {'PPID':>6} {'CPU%':>6} {'MEM(MB)':>8} {'Threads':>7} {'Handles':>8} {'Risque':>6} {'Utilisateur':15}")
            print(f"{'-'*100}")
            
            for pinfo in processes[:50]:  # Limiter à 50 pour la lisibilité
                risk_color = Colors.RED if pinfo['risk_score'] > 5 else Colors.YELLOW if pinfo['risk_score'] > 2 else Colors.GREEN
                
                print(f"{pinfo['name'][:24]:25} "
                      f"{pinfo['pid']:>6} "
                      f"{pinfo.get('ppid', 'N/A'):>6} "
                      f"{pinfo['cpu_percent']:>6.1f} "
                      f"{pinfo.get('memory_mb', 0):>8.1f} "
                      f"{pinfo.get('num_threads', 'N/A'):>7} "
                      f"{pinfo.get('num_handles', 'N/A'):>8} "
                      f"{risk_color}{pinfo['risk_score']:>6}{Colors.END} "
                      f"{pinfo.get('username', 'N/A')[:14]:15}")
                
                # Afficher les flags si risque élevé
                if pinfo['risk_score'] > 3 and pinfo['flags']:
                    print(f"       ⚠️ {Colors.YELLOW}{', '.join(pinfo['flags'][:3])}{Colors.END}")
        
        # Résumé statistique
        print(f"\n{Colors.BOLD}📊 STATISTIQUES:{Colors.END}")
        print(f"  • Processus analysés: {len(processes)}")
        
        high_risk = len([p for p in processes if p['risk_score'] > 5])
        medium_risk = len([p for p in processes if 2 < p['risk_score'] <= 5])
        
        print(f"  • Processus à haut risque: {Colors.RED}{high_risk}{Colors.END}")
        print(f"  • Processus à risque moyen: {Colors.YELLOW}{medium_risk}{Colors.END}")
        
        total_memory = sum(p.get('memory_mb', 0) for p in processes)
        print(f"  • Mémoire totale utilisée: {total_memory:.1f} MB")
        
        # Top 3 CPU
        top_cpu = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:3]
        if top_cpu:
            print(f"  • Top 3 CPU: {', '.join([f'{p['name']} ({p['cpu_percent']:.1f}%)' for p in top_cpu])}")
        
        # Sauvegarde des données
        self.scan_history.append({
            'timestamp': datetime.now().isoformat(),
            'process_count': len(processes),
            'high_risk': high_risk,
            'total_memory_mb': total_memory
        })
        
        return processes
    
    def find_process(self, search_term):
        """Recherche un processus par nom, PID ou utilisateur"""
        print(f"\n{Colors.BOLD}🔎 RECHERCHE: '{search_term}'{Colors.END}")
        print(f"{Colors.CYAN}{'='*100}{Colors.END}")
        
        results = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'exe', 'cmdline']):
            try:
                pinfo = proc.info
                search_lower = search_term.lower()
                
                # Recherche dans nom, PID, utilisateur, chemin
                match = (search_lower in pinfo['name'].lower() or
                        search_term == str(pinfo['pid']) or
                        (pinfo['username'] and search_lower in pinfo['username'].lower()) or
                        (pinfo['exe'] and search_lower in pinfo['exe'].lower()) or
                        (pinfo['cmdline'] and any(search_lower in str(arg).lower() 
                                                  for arg in pinfo['cmdline'])))
                
                if match:
                    with proc.oneshot():
                        pinfo['memory_mb'] = proc.memory_info().rss / (1024 * 1024)
                        pinfo['cpu_percent'] = proc.cpu_percent(interval=0.1)
                        pinfo['num_threads'] = proc.num_threads()
                        pinfo['create_time'] = datetime.fromtimestamp(proc.create_time()).strftime('%H:%M:%S')
                    
                    results.append(pinfo)
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if results:
            print(f"{'Nom':25} {'PID':>6} {'CPU%':>6} {'MEM(MB)':>8} {'Threads':>7} {'Utilisateur':15} {'Chemin':30}")
            print(f"{'-'*100}")
            
            for pinfo in results[:20]:  # Limiter l'affichage
                print(f"{pinfo['name'][:24]:25} "
                      f"{pinfo['pid']:>6} "
                      f"{pinfo.get('cpu_percent', 0):>6.1f} "
                      f"{pinfo.get('memory_mb', 0):>8.1f} "
                      f"{pinfo.get('num_threads', 'N/A'):>7} "
                      f"{pinfo.get('username', 'N/A')[:14]:15} "
                      f"{pinfo.get('exe', 'N/A')[:29]:30}")
        else:
            print(f"{Colors.YELLOW}Aucun processus trouvé avec '{search_term}'{Colors.END}")
        
        return results
    
    def scan_network_detailed(self):
        """Scan détaillé des connexions réseau"""
        print(f"\n{Colors.BOLD}🌐 SCAN RÉSEAU DÉTAILLÉ{Colors.END}")
        print(f"{Colors.CYAN}{'='*100}{Colors.END}")
        
        suspicious_ports = {
            'mining': [3333, 4444, 5555, 6666, 7777, 8888, 9999],
            'remote_access': [3389, 5900, 5800, 22, 23],
            'malware': [8080, 8443, 8333, 9333, 19333],
            'torrent': [6881, 6889, 51413]
        }
        
        connections_by_process = defaultdict(list)
        
        for conn in psutil.net_connections(kind='inet'):
            try:
                if conn.raddr and conn.raddr != ():
                    ip, port = conn.raddr
                    
                    # Détection de menaces
                    threat_level = 'INFO'
                    reason = ''
                    
                    for category, ports in suspicious_ports.items():
                        if port in ports:
                            threat_level = 'HIGH'
                            reason = f"Port suspect ({category}:{port})"
                            self.add_alert('HIGH',
                                f"Connexion suspecte sur port {port} ({category}) vers {ip}",
                                {'port': port, 'ip': ip, 'category': category})
                            break
                    
                    # Recherche du processus
                    proc_info = {}
                    if conn.pid:
                        try:
                            proc = psutil.Process(conn.pid)
                            proc_info = {
                                'name': proc.name(),
                                'exe': proc.exe(),
                                'pid': conn.pid
                            }
                        except:
                            proc_info = {'name': 'INCONNU', 'pid': conn.pid}
                    
                    conn_info = {
                        'local': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else 'N/A',
                        'remote': f"{ip}:{port}",
                        'status': conn.status,
                        'family': 'IPv4' if conn.family == socket.AF_INET else 'IPv6',
                        'type': 'TCP' if conn.type == socket.SOCK_STREAM else 'UDP',
                        'threat': threat_level,
                        'reason': reason
                    }
                    
                    if conn.pid:
                        connections_by_process[proc_info['name']].append(conn_info)
                    
                    # Affichage
                    threat_color = Colors.RED if threat_level == 'HIGH' else Colors.YELLOW if threat_level == 'MEDIUM' else Colors.GREEN
                    print(f"{proc_info.get('name', 'SYSTEM'):25} "
                          f"{conn_info['local']:25} -> {conn_info['remote']:25} "
                          f"{conn_info['status']:12} {threat_color}{threat_level:7}{Colors.END}")
                    
            except (AttributeError, IndexError, psutil.AccessDenied):
                continue
        
        # Résumé par processus
        print(f"\n{Colors.BOLD}📡 RÉSUMÉ PAR PROCESSUS:{Colors.END}")
        for proc_name, conns in sorted(connections_by_process.items(), 
                                      key=lambda x: len(x[1]), reverse=True)[:10]:
            print(f"  • {proc_name:25} : {len(conns)} connexions")
        
        return connections_by_process
    
    def scan_disks_detailed(self):
        """Scan détaillé des disques avec analyse des fichiers temporaires"""
        print(f"\n{Colors.BOLD}💾 SCAN DES DISQUES DÉTAILLÉ{Colors.END}")
        print(f"{Colors.CYAN}{'='*100}{Colors.END}")
        
        disk_info = []
        
        for partition in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                
                # Analyse de l'utilisation
                status = 'OK'
                if usage.percent > 95:
                    status = 'CRITICAL'
                    self.add_alert('CRITICAL',
                        f"Disque CRITIQUEMENT PLEIN: {partition.device} ({usage.percent:.1f}%)")
                elif usage.percent > 85:
                    status = 'HIGH'
                    self.add_alert('HIGH',
                        f"Disque presque plein: {partition.device} ({usage.percent:.1f}%)")
                elif usage.percent > 70:
                    status = 'WARNING'
                
                # Taille des fichiers temporaires (Windows)
                temp_size = 0
                temp_count = 0
                if os.name == 'nt' and 'C:' in partition.device:
                    temp_dirs = ['C:\\Windows\\Temp', 'C:\\Users\\*\\AppData\\Local\\Temp']
                    for temp_dir in temp_dirs:
                        if os.path.exists(temp_dir.replace('*', getpass.getuser())):
                            try:
                                for root, dirs, files in os.walk(temp_dir.replace('*', getpass.getuser())):
                                    for file in files:
                                        try:
                                            temp_size += os.path.getsize(os.path.join(root, file))
                                            temp_count += 1
                                        except:
                                            continue
                            except:
                                pass
                
                disk_info.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'total_gb': usage.total / (1024**3),
                    'free_gb': usage.free / (1024**3),
                    'used_percent': usage.percent,
                    'status': status,
                    'temp_size_mb': temp_size / (1024**2),
                    'temp_count': temp_count
                })
                
                # Affichage
                status_color = Colors.RED if status == 'CRITICAL' else Colors.YELLOW if status in ['HIGH', 'WARNING'] else Colors.GREEN
                print(f"{partition.device:10} {partition.mountpoint:15} "
                      f"Total: {usage.total / (1024**3):6.1f}Go "
                      f"Libre: {usage.free / (1024**3):6.1f}Go "
                      f"{status_color}{usage.percent:6.1f}% {status:10}{Colors.END}")
                
                if temp_count > 0:
                    print(f"       📁 Fichiers temporaires: {temp_count} fichiers, {temp_size / (1024**2):.1f} MB")
                
            except (PermissionError, OSError) as e:
                print(f"{partition.device:10} {partition.mountpoint:15} {Colors.RED}ERREUR: {str(e)[:30]}{Colors.END}")
        
        return disk_info
    
    def scan_system_info_detailed(self):
        """Affiche les informations système détaillées"""
        print(f"\n{Colors.BOLD}🖥️  INFORMATIONS SYSTÈME DÉTAILLÉES{Colors.END}")
        print(f"{Colors.CYAN}{'='*100}{Colors.END}")
        
        infos = {}
        
        # Informations CPU
        print(f"{Colors.BOLD}🎯 PROCESSOR:{Colors.END}")
        infos['cpu'] = {
            'cores': psutil.cpu_count(logical=False),
            'threads': psutil.cpu_count(logical=True),
            'freq_mhz': psutil.cpu_freq().current if psutil.cpu_freq() else 'N/A',
            'usage': psutil.cpu_percent(interval=1)
        }
        print(f"  • Cores physiques: {infos['cpu']['cores']}")
        print(f"  • Threads logiques: {infos['cpu']['threads']}")
        print(f"  • Fréquence: {infos['cpu']['freq_mhz']} MHz")
        print(f"  • Utilisation: {infos['cpu']['usage']:.1f}%")
        
        # Informations Mémoire
        print(f"\n{Colors.BOLD}💾 MÉMOIRE:{Colors.END}")
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        infos['memory'] = {
            'total_gb': mem.total / (1024**3),
            'available_gb': mem.available / (1024**3),
            'used_percent': mem.percent,
            'swap_total_gb': swap.total / (1024**3),
            'swap_used_percent': swap.percent
        }
        print(f"  • Totale: {infos['memory']['total_gb']:.1f} Go")
        print(f"  • Disponible: {infos['memory']['available_gb']:.1f} Go")
        print(f"  • Utilisée: {infos['memory']['used_percent']:.1f}%")
        print(f"  • Swap: {infos['memory']['swap_total_gb']:.1f} Go ({infos['memory']['swap_used_percent']:.1f}%)")
        
        # Informations Système
        print(f"\n{Colors.BOLD}⚙️  SYSTÈME:{Colors.END}")
        infos['system'] = {
            'os': platform.system(),
            'version': platform.version(),
            'release': platform.release(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'hostname': socket.gethostname()
        }
        print(f"  • OS: {infos['system']['os']} {infos['system']['release']}")
        print(f"  • Version: {infos['system']['version']}")
        print(f"  • Machine: {infos['system']['machine']}")
        print(f"  • Hostname: {infos['system']['hostname']}")
        
        # Informations Réseau
        print(f"\n{Colors.BOLD}🌐 RÉSEAU:{Colors.END}")
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
            print(f"  • IP locale: {local_ip}")
        except:
            print(f"  • IP locale: {Colors.YELLOW}Indisponible{Colors.END}")
        
        # Boot et uptime
        print(f"\n{Colors.BOLD}⏱️  UPTIME:{Colors.END}")
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        infos['uptime'] = {
            'boot_time': boot_time.isoformat(),
            'uptime_seconds': uptime.total_seconds(),
            'uptime_human': str(uptime).split('.')[0]
        }
        print(f"  • Démarré le: {boot_time.strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"  • Uptime: {infos['uptime']['uptime_human']}")
        
        # Utilisateurs connectés
        print(f"\n{Colors.BOLD}👥 UTILISATEURS:{Colors.END}")
        users = psutil.users()
        for user in users[:5]:  # Limiter l'affichage
            print(f"  • {user.name} depuis {user.host or 'local'} (depuis {datetime.fromtimestamp(user.started).strftime('%H:%M:%S')})")
        
        return infos
    
    def scan_malware_indicators(self):
        """Recherche d'indicateurs de malware"""
        print(f"\n{Colors.BOLD}🕵️  ANALYSE MALWARE / INDICATEURS{Colors.END}")
        print(f"{Colors.CYAN}{'='*100}{Colors.END}")
        
        indicators = []
        
        # 1. Processus cachés ou sans chemin
        print(f"{Colors.BOLD}1. Processus suspects:{Colors.END}")
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                pinfo = proc.info
                if not pinfo['exe'] or pinfo['exe'] == '':
                    indicators.append({
                        'type': 'HIDDEN_PROCESS',
                        'process': pinfo['name'],
                        'pid': pinfo['pid'],
                        'reason': 'Pas de chemin d\'exécution'
                    })
                    print(f"  ⚠️ {Colors.YELLOW}Processus sans chemin: {pinfo['name']} (PID:{pinfo['pid']}){Colors.END}")
            except:
                continue
        
        # 2. Connexions sur ports suspects
        print(f"\n{Colors.BOLD}2. Connexions suspectes:{Colors.END}")
        suspicious_ports = [3333, 4444, 5555, 6666, 7777, 8080, 8333, 9333, 9999]
        for conn in psutil.net_connections(kind='inet'):
            try:
                if conn.raddr:
                    _, port = conn.raddr
                    if port in suspicious_ports:
                        indicators.append({
                            'type': 'SUSPICIOUS_PORT',
                            'port': port,
                            'reason': f'Port connu pour le mining/crypto'
                        })
                        print(f"  ⚠️ {Colors.YELLOW}Port suspect {port} utilisé{Colors.END}")
            except:
                continue
        
        # 3. Fichiers récents dans Temp avec extensions suspectes
        print(f"\n{Colors.BOLD}3. Fichiers temporaires suspects:{Colors.END}")
        temp_dirs = ['C:\\Windows\\Temp', os.environ.get('TEMP', '')]
        suspect_ext = ['.exe', '.dll', '.vbs', '.js', '.bat', '.ps1']
        
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                try:
                    files = os.listdir(temp_dir)[-10:]  # 10 derniers fichiers
                    for file in files:
                        if any(file.endswith(ext) for ext in suspect_ext):
                            filepath = os.path.join(temp_dir, file)
                            try:
                                size = os.path.getsize(filepath)
                                if size > 1024 * 1024:  # > 1MB
                                    indicators.append({
                                        'type': 'SUSPICIOUS_TEMP_FILE',
                                        'file': file,
                                        'size_mb': size / (1024*1024),
                                        'reason': 'Gros fichier exécutable dans Temp'
                                    })
                                    print(f"  ⚠️ {Colors.YELLOW}Fichier suspect dans Temp: {file} ({size/(1024*1024):.1f} MB){Colors.END}")
                            except:
                                pass
                except:
                    pass
        
        # 4. Services non-Microsoft avec noms suspects
        print(f"\n{Colors.BOLD}4. Services suspects:{Colors.END}")
        if os.name == 'nt':
            try:
                import win32service
                import win32con
                
                service_keywords = ['update', 'client', 'helper', 'service', 'host']
                sc = win32service.OpenSCManager(None, None, win32con.SC_MANAGER_ENUMERATE_SERVICE)
                services = win32service.EnumServicesStatus(sc, win32service.SERVICE_WIN32, win32service.SERVICE_STATE_ALL)
                
                for service in services[:20]:  # Limiter pour la performance
                    name, display_name, status = service
                    name_lower = name.lower()
                    
                    if 'microsoft' not in name_lower and 'windows' not in name_lower:
                        if any(keyword in name_lower for keyword in service_keywords):
                            indicators.append({
                                'type': 'SUSPICIOUS_SERVICE',
                                'service': name,
                                'display_name': display_name,
                                'reason': 'Service non-Microsoft avec nom générique'
                            })
                            print(f"  ⚠️ {Colors.YELLOW}Service suspect: {name} ({display_name}){Colors.END}")
                            
            except ImportError:
                print(f"  {Colors.YELLOW}Module win32service non disponible{Colors.END}")
            except Exception as e:
                print(f"  {Colors.YELLOW}Erreur analyse services: {e}{Colors.END}")
        
        # Résumé
        print(f"\n{Colors.BOLD}📊 RÉSUMÉ DE L'ANALYSE:{Colors.END}")
        print(f"  • Total indicateurs trouvés: {len(indicators)}")
        
        if indicators:
            print(f"  • {Colors.RED}⚠️  Des indicateurs de malware ont été détectés!{Colors.END}")
            print(f"  • {Colors.YELLOW}Recommandation: Analysez avec un antivirus et supprimez les fichiers suspects{Colors.END}")
        else:
            print(f"  • {Colors.GREEN}✅ Aucun indicateur de malware évident détecté{Colors.END}")
        
        return indicators
    
    def kill_process_by_pid(self, pid):
        """Tue un processus par son PID"""
        try:
            pid = int(pid)
            proc = psutil.Process(pid)
            proc_name = proc.name()
            
            # Demande de confirmation pour les processus système
            if proc_name in ['svchost.exe', 'lsass.exe', 'winlogon.exe', 'csrss.exe']:
                print(f"{Colors.RED}⚠️  ATTENTION: Tentative de tuer un processus système: {proc_name}{Colors.END}")
                confirm = input(f"Confirmer la terminaison de {proc_name} (PID:{pid})? [o/N]: ").lower()
                if confirm != 'o':
                    print(f"{Colors.YELLOW}Annulé{Colors.END}")
                    return False
            
            proc.terminate()
            try:
                proc.wait(timeout=3)
                print(f"{Colors.GREEN}✅ Processus terminé: {proc_name} (PID:{pid}){Colors.END}")
                return True
            except psutil.TimeoutExpired:
                proc.kill()
                print(f"{Colors.GREEN}✅ Processus forcé: {proc_name} (PID:{pid}){Colors.END}")
                return True
                
        except (psutil.NoSuchProcess, ValueError) as e:
            print(f"{Colors.YELLOW}⚠️  Processus non trouvé: PID {pid}{Colors.END}")
            return False
        except psutil.AccessDenied:
            print(f"{Colors.RED}❌ Accès refusé pour tuer le processus {pid}{Colors.END}")
            print(f"   Essayez de lancer le script en administrateur")
            return False
    
    def show_alerts(self, limit=20):
        """Affiche les alertes récentes"""
        if not self.alerts:
            print(f"\n{Colors.GREEN}✅ Aucune alerte détectée{Colors.END}")
            return []
        
        print(f"\n{Colors.BOLD}🚨 ALERTES RÉCENTES ({len(self.alerts)}){Colors.END}")
        print(f"{Colors.CYAN}{'='*100}{Colors.END}")
        
        recent_alerts = self.alerts[-limit:] if limit else self.alerts
        
        for alert in recent_alerts:
            level_color = alert['color']
            print(f"[{alert['time']}] {level_color}[{alert['level']:^9}]{Colors.END} {alert['message']}")
            
            if alert['process']:
                proc_info = alert['process']
                if isinstance(proc_info, dict):
                    print(f"       📌 Processus: {proc_info.get('name', 'N/A')} "
                          f"(PID:{proc_info.get('pid', 'N/A')}) "
                          f"CPU:{proc_info.get('cpu_percent', 0):.1f}% "
                          f"MEM:{proc_info.get('memory_mb', 0):.1f}MB")
        
        # Statistiques
        levels = [a['level'] for a in self.alerts]
        print(f"\n{Colors.BOLD}📈 STATISTIQUES ALERTES:{Colors.END}")
        print(f"  • CRITICAL: {levels.count('CRITICAL')}")
        print(f"  • HIGH: {levels.count('HIGH')}")
        print(f"  • MEDIUM: {levels.count('MEDIUM')}")
        print(f"  • TOTAL: {len(self.alerts)}")
        
        return recent_alerts
    
    def export_logs(self):
        """Exporte les logs et alertes dans un fichier"""
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'system_info': self.scan_system_info_detailed(),
            'alerts': self.alerts,
            'scan_history': self.scan_history,
            'total_scans': len(self.scan_history)
        }
        
        filename = f"helpdesk_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"{Colors.GREEN}✅ Logs exportés dans: {filename}{Colors.END}")
            print(f"   • Alertes: {len(self.alerts)}")
            print(f"   • Scans: {len(self.scan_history)}")
            print(f"   • Taille: {os.path.getsize(filename) / 1024:.1f} KB")
            
            return filename
        except Exception as e:
            print(f"{Colors.RED}❌ Erreur export: {e}{Colors.END}")
            return None

# ================= INTERFACE UTILISATEUR AMELIOREE =================
def main():
    scanner = SystemScanner()
    history = CommandHistory()
    last_command = ""
    
    # Initialisation
    print_header()
    print(f"{Colors.GREEN}✅ Scanner initialisé. Tapez 'help' pour les commandes.{Colors.END}")
    print(f"{Colors.YELLOW}📝 Historique conservé - Pas de clear automatique{Colors.END}\n")
    
    while True:
        try:
            # Afficher la barre de statut
            print_status_bar(scanner)
            
            # Afficher menu compact
            print_menu(compact=True)
            
            # Prompt avec historique
            prompt = f"\n{Colors.BOLD}helpdesk>{Colors.END} "
            try:
                import readline
                # Configuration de l'historique readline
                for i, cmd in enumerate(history.history[-10:]):
                    readline.add_history(cmd)
            except:
                pass
            
            choice = input(prompt).strip()
            
            if not choice and last_command:
                choice = last_command  # Répéter dernière commande
            else:
                history.add(choice)
                last_command = choice
            
            # Traitement des commandes
            if choice in ['8', 'quit', 'exit', 'q']:
                print(f"\n{Colors.GREEN}👋 Au revoir !{Colors.END}")
                print(f"📊 Résumé de la session:")
                print(f"   • Alertes générées: {len(scanner.alerts)}")
                print(f"   • Commandes exécutées: {len(history.history)}")
                print(f"   • Fichier de log: {scanner.log_file}")
                break
            
            elif choice in ['1', 'scan', 'scan-all']:
                print(f"\n{Colors.YELLOW}⏳ Lancement du scan complet...{Colors.END}")
                scanner.scan_system_info_detailed()
                scanner.scan_processes(detailed=True, sort_by='risk')
                scanner.scan_network_detailed()
                scanner.scan_disks_detailed()
                scanner.show_alerts(limit=10)
                
            elif choice in ['2', 'proc', 'process', 'scan-proc']:
                sort_by = input(f"Trier par [cpu/mem/risk/name] (défaut: cpu): ").strip().lower()
                sort_by = sort_by if sort_by in ['cpu', 'mem', 'risk', 'name'] else 'cpu'
                scanner.scan_processes(detailed=True, sort_by=sort_by)
                
            elif choice in ['3', 'net', 'scan-net']:
                scanner.scan_network_detailed()
                
            elif choice in ['4', 'disk', 'scan-disk']:
                scanner.scan_disks_detailed()
                
            elif choice in ['5', 'info', 'system']:
                scanner.scan_system_info_detailed()
                
            elif choice in ['6', 'monitor', 'real-time']:
                try:
                    duration = int(input(f"Durée (secondes, défaut 30): ") or "30")
                    scanner.real_time_monitor(duration)
                except ValueError:
                    print(f"{Colors.YELLOW}Durée invalide{Colors.END}")
                
            elif choice in ['7', 'malware', 'scan-malware']:
                scanner.scan_malware_indicators()
            
            elif choice.startswith('kill '):
                proc_name = choice[5:].strip()
                if proc_name:
                    killed = scanner.kill_process(proc_name)
                    if killed == 0:
                        print(f"{Colors.YELLOW}⚠️  Aucun processus trouvé. Essayez 'find {proc_name}' d'abord.{Colors.END}")
                else:
                    print(f"{Colors.YELLOW}Usage: kill NOM_PROCESSUS{Colors.END}")
            
            elif choice.startswith('killpid '):
                pid = choice[8:].strip()
                if pid:
                    scanner.kill_process_by_pid(pid)
                else:
                    print(f"{Colors.YELLOW}Usage: killpid PID{Colors.END}")
            
            elif choice.startswith('find '):
                search_term = choice[5:].strip()
                if search_term:
                    scanner.find_process(search_term)
                else:
                    print(f"{Colors.YELLOW}Usage: find NOM_OU_PID{Colors.END}")
            
            elif choice in ['alert', 'alerts']:
                limit = input(f"Nombre d'alertes (défaut 20): ").strip()
                limit = int(limit) if limit.isdigit() else 20
                scanner.show_alerts(limit=limit)
            
            elif choice in ['log', 'export', 'save']:
                scanner.export_logs()
            
            elif choice == 'history':
                print(f"\n{Colors.BOLD}📜 HISTORIQUE DES COMMANDES:{Colors.END}")
                for i, cmd in enumerate(history.history[-20:], 1):
                    print(f"  {i:3}. {cmd}")
            
            elif choice == 'clear':
                clear_screen()
                print_header()
                continue
            
            elif choice == 'help':
                print_menu(compact=False)
            
            elif choice == '':
                continue  # Ne rien faire sur entrée vide
                
            else:
                print(f"{Colors.YELLOW}❓ Commande non reconnue: '{choice}'{Colors.END}")
                print(f"   Tapez {Colors.CYAN}help{Colors.END} pour la liste des commandes")
            
            # Pas de pause forcée - l'historique reste visible
            print(f"\n{Colors.CYAN}{'─'*80}{Colors.END}")
            
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}\n⚠️  Ctrl+C détecté. Tapez 'quit' pour quitter.{Colors.END}")
            continue
        except Exception as e:
            print(f"{Colors.RED}❌ Erreur: {e}{Colors.END}")
            import traceback
            traceback.print_exc()
            time.sleep(2)

# ================= INSTALLATION =================
def check_dependencies():
    """Vérifie et installe les dépendances"""
    required = ['psutil']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"{Colors.YELLOW}Installation des dépendances manquantes: {', '.join(missing)}{Colors.END}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
            print(f"{Colors.GREEN}✅ Dépendances installées{Colors.END}")
        except subprocess.CalledProcessError:
            print(f"{Colors.RED}❌ Échec installation. Installez manuellement: pip install {' '.join(missing)}{Colors.END}")
            sys.exit(1)
    
    # Vérification des privilèges
    if os.name == 'nt':
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin:
                print(f"{Colors.YELLOW}⚠️  Attention: Pas en mode administrateur")
                print(f"   Certaines fonctionnalités peuvent être limitées{Colors.END}")
        except:
            pass

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
        input("Appuyez sur Entrée pour quitter...")