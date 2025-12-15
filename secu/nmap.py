# - Terminal de surveillance système HELP DESK avec SCAN style NMAP -
# 📜 CORRESPONDANCE COMMANDES / FONCTIONS :

# Dans ce tool |	Équivalent en CMD/PowerShell	                           |    Ce que ça évite de faire manuellement
# scan	        tasklist /v | findstr /i "cpu memory" + tri + calcul	        Voir CPU% et RAM% de CHAQUE processus, trier, chercher les gourmands
# kill chrome	taskkill /f /im chrome.exe	                                    OK celle-là est simple, mais avec PID c'est chiant
# kill 1234	    taskkill /f /pid 1234	                                        Trouver le bon PID dans tasklist d'abord
# net	        netstat -ano | findstr ESTABLISHED + tasklist pour chaque PID	Croiser PID avec noms de processus, chercher ports suspects
# disk	        wmic logicaldisk get size,freespace,caption + calcul Go	        Convertir bytes en Go, calculer pourcentages
# info	        systeminfo + wmic cpu get + wmic memorychip get	                Extraire infos pertinentes dans 50 lignes
# full	        TOUTES les commandes ci-dessus + analyse automatique	        5 minutes de copier-coller dans 3 fenêtres
# nmap mini en cours...
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
from typing import List, Dict, Any, Tuple
import warnings
import ipaddress
import struct
import select
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import ssl
import http.client
import urllib.request
import urllib.error
#import win32service
#import win32con


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

# ================= MODULE NMAP-LIKE =================
class NetworkScanner:
    """Module de scan réseau style Nmap"""
    
    # Ports communs et leurs services
    COMMON_PORTS = {
        20: 'FTP-Data', 21: 'FTP', 22: 'SSH', 23: 'Telnet',
        25: 'SMTP', 53: 'DNS', 67: 'DHCP', 68: 'DHCP',
        69: 'TFTP', 80: 'HTTP', 110: 'POP3', 111: 'RPC',
        119: 'NNTP', 123: 'NTP', 135: 'MSRPC', 137: 'NetBIOS',
        138: 'NetBIOS', 139: 'NetBIOS', 143: 'IMAP', 161: 'SNMP',
        162: 'SNMP', 179: 'BGP', 194: 'IRC', 389: 'LDAP',
        443: 'HTTPS', 445: 'SMB', 465: 'SMTPS', 514: 'Syslog',
        515: 'LPD', 587: 'SMTP', 631: 'IPP', 636: 'LDAPS',
        993: 'IMAPS', 995: 'POP3S', 1080: 'SOCKS', 1194: 'OpenVPN',
        1433: 'MSSQL', 1521: 'Oracle', 1723: 'PPTP', 1883: 'MQTT',
        1900: 'UPnP', 2049: 'NFS', 2082: 'cPanel', 2083: 'cPanel SSL',
        2086: 'WHM', 2087: 'WHM SSL', 2095: 'Webmail', 2096: 'Webmail SSL',
        2222: 'DirectAdmin', 2375: 'Docker', 2376: 'Docker SSL',
        3000: 'Node.js', 3306: 'MySQL', 3389: 'RDP', 3690: 'SVN',
        4000: 'Ruby on Rails', 4333: 'mSQL', 4443: 'Apache SSL',
        4505: 'SaltStack', 4506: 'SaltStack', 4848: 'GlassFish',
        5432: 'PostgreSQL', 5900: 'VNC', 5938: 'TeamViewer',
        5984: 'CouchDB', 5985: 'WinRM', 5986: 'WinRM SSL',
        6379: 'Redis', 7001: 'WebLogic', 7002: 'WebLogic SSL',
        8000: 'HTTP Alt', 8008: 'HTTP Alt', 8080: 'HTTP Proxy',
        8081: 'HTTP Proxy', 8088: 'HTTP Alt', 8090: 'HTTP Alt',
        8091: 'CouchBase', 8140: 'Puppet', 8181: 'HTTP Alt',
        8443: 'HTTPS Alt', 8888: 'HTTP Alt', 9000: 'SonarQube',
        9001: 'Tor', 9042: 'Cassandra', 9090: 'HTTP Alt',
        9100: 'JetDirect', 9200: 'Elasticsearch', 9300: 'Elasticsearch',
        9418: 'Git', 9999: 'HTTP Alt', 10000: 'Webmin',
        11211: 'Memcached', 27017: 'MongoDB', 28017: 'MongoDB HTTP',
        50000: 'SAP', 50070: 'Hadoop', 50075: 'Hadoop',
        61616: 'ActiveMQ', 62078: 'iPhone Sync'
    }
    
    # Ports dangereux/vulnérables
    DANGEROUS_PORTS = {
        21: 'FTP - souvent non sécurisé',
        23: 'Telnet - credentials en clair',
        135: 'MSRPC - vulnérabilités connues',
        139: 'NetBIOS - informations système',
        445: 'SMB - EternalBlue, WannaCry',
        1433: 'MSSQL - injections possibles',
        1521: 'Oracle - attaques connues',
        3306: 'MySQL - bruteforce commun',
        3389: 'RDP - BlueKeep, bruteforce',
        5432: 'PostgreSQL - attaques connues',
        5900: 'VNC - bruteforce commun',
        5985: 'WinRM - accès distant Windows',
        6379: 'Redis - accès non authentifié',
        27017: 'MongoDB - souvent sans auth'
    }
    
    def __init__(self):
        self.scan_results = {}
        self.open_ports_cache = {}
        self.thread_pool = ThreadPoolExecutor(max_workers=100)
        self.timeout = 1.0
        
    def check_host_alive(self, host: str) -> bool:
        """Vérifie si un hôte est en ligne (ping)"""
        try:
            param = '-n' if os.name == 'nt' else '-c'
            command = ['ping', param, '1', '-w', '1000', host]
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2)
            return result.returncode == 0
        except:
            try:
                socket.gethostbyname(host)
                return True
            except:
                return False
    
    def scan_port(self, host: str, port: int, scan_type: str = 'tcp') -> Dict:
        """Scan un port unique"""
        result = {
            'port': port,
            'protocol': scan_type,
            'state': 'closed',
            'service': self.COMMON_PORTS.get(port, 'unknown'),
            'banner': '',
            'dangerous': port in self.DANGEROUS_PORTS
        }
        
        try:
            if scan_type == 'tcp':
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)
                
                start_time = time.time()
                connection_result = sock.connect_ex((host, port))
                scan_time = time.time() - start_time
                
                if connection_result == 0:
                    result['state'] = 'open'
                    result['response_time'] = f"{scan_time*1000:.1f}ms"
                    
                    try:
                        if port in [80, 443, 8080, 8443]:
                            sock.send(b"GET / HTTP/1.0\r\n\r\n")
                            banner = sock.recv(1024).decode('utf-8', errors='ignore')
                            if 'HTTP/' in banner or 'Server:' in banner:
                                result['banner'] = banner[:500]
                        elif port == 21:
                            banner = sock.recv(1024).decode('utf-8', errors='ignore')
                            result['banner'] = banner.strip()
                        elif port == 22:
                            banner = sock.recv(1024).decode('utf-8', errors='ignore')
                            result['banner'] = banner.strip()
                        elif port == 25:
                            banner = sock.recv(1024).decode('utf-8', errors='ignore')
                            result['banner'] = banner.strip()
                        else:
                            sock.send(b"\r\n\r\n")
                            banner = sock.recv(1024).decode('utf-8', errors='ignore')
                            if banner and len(banner) > 3:
                                result['banner'] = banner[:200]
                    except:
                        pass
                
                sock.close()
                
            elif scan_type == 'udp':
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(self.timeout)
                
                try:
                    sock.sendto(b'\x00', (host, port))
                    data, _ = sock.recvfrom(1024)
                    result['state'] = 'open|filtered'
                    if data:
                        result['state'] = 'open'
                        result['banner'] = str(data[:100])
                except socket.timeout:
                    result['state'] = 'open|filtered'
                except:
                    result['state'] = 'closed'
                finally:
                    sock.close()
        
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def quick_port_scan(self, host: str, ports: List[int] = None) -> List[Dict]:
        """Scan rapide des ports principaux"""
        if ports is None:
            ports = [21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 
                    443, 445, 993, 995, 1723, 3306, 3389, 5900, 8080]
        
        print(f"{Colors.BOLD}🔍 Scan rapide de {host}{Colors.END}")
        print(f"{Colors.CYAN}{'='*80}{Colors.END}")
        
        if not self.check_host_alive(host):
            print(f"{Colors.RED}❌ Hôte non joignable: {host}{Colors.END}")
            return []
        
        print(f"{Colors.GREEN}✅ Hôte actif: {host}{Colors.END}")
        print(f"Scan de {len(ports)} ports...\n")
        
        open_ports = []
        futures = []
        
        for port in ports:
            future = self.thread_pool.submit(self.scan_port, host, port, 'tcp')
            futures.append(future)
        
        for future in as_completed(futures):
            result = future.result()
            if result['state'] == 'open':
                open_ports.append(result)
                
                danger = f"{Colors.RED}⚠️ DANGER{Colors.END}" if result['dangerous'] else ""
                print(f"  {Colors.GREEN}✓{Colors.END} Port {result['port']:5} - {result['service']:20} OPEN {danger}")
                if result.get('banner'):
                    banner_preview = result['banner'][:50].replace('\n', ' ').replace('\r', '')
                    print(f"       📝 {banner_preview}...")
        
        print(f"\n{Colors.BOLD}📊 RÉSUMÉ:{Colors.END}")
        print(f"  • Ports scannés: {len(ports)}")
        print(f"  • Ports ouverts: {len(open_ports)}")
        
        if open_ports:
            dangerous = [p for p in open_ports if p['dangerous']]
            if dangerous:
                print(f"  • {Colors.RED}Ports dangereux: {len(dangerous)}{Colors.END}")
                for port in dangerous:
                    print(f"       ⚠️  Port {port['port']} ({port['service']}): {self.DANGEROUS_PORTS.get(port['port'], '')}")
        
        return open_ports
    
    def full_port_scan(self, host: str, start_port: int = 1, end_port: int = 1024) -> Dict:
        """Scan complet de tous les ports"""
        print(f"{Colors.BOLD}🔍 Scan complet de {host} (ports {start_port}-{end_port}){Colors.END}")
        print(f"{Colors.CYAN}{'='*80}{Colors.END}")
        
        if not self.check_host_alive(host):
            print(f"{Colors.RED}❌ Hôte non joignable: {host}{Colors.END}")
            return {}
        
        total_ports = end_port - start_port + 1
        print(f"{Colors.YELLOW}⏳ Scan de {total_ports} ports... (ça peut prendre du temps){Colors.END}")
        
        open_ports = []
        futures = []
        
        def print_progress(current, total):
            percent = (current / total) * 100
            bar_length = 40
            filled = int(bar_length * current / total)
            bar = '█' * filled + '░' * (bar_length - filled)
            sys.stdout.write(f'\r  [{bar}] {percent:.1f}% ({current}/{total})')
            sys.stdout.flush()
        
        for port in range(start_port, end_port + 1):
            future = self.thread_pool.submit(self.scan_port, host, port, 'tcp')
            futures.append(future)
        
        completed = 0
        for future in as_completed(futures):
            result = future.result()
            completed += 1
            
            if completed % 50 == 0 or completed == total_ports:
                print_progress(completed, total_ports)
            
            if result['state'] == 'open':
                open_ports.append(result)
        
        print()
        
        results = {
            'host': host,
            'scan_time': datetime.now().isoformat(),
            'ports_scanned': total_ports,
            'open_ports': open_ports,
            'open_count': len(open_ports),
            'dangerous_ports': [p for p in open_ports if p['dangerous']],
            'common_services': [],
            'unknown_services': []
        }
        
        print(f"\n{Colors.BOLD}📋 PORTS OUVERTS ({len(open_ports)}){Colors.END}")
        print(f"{'Port':<6} {'Protocole':<8} {'Service':<20} {'État':<12} {'Danger':<8}")
        print(f"{'-'*60}")
        
        for port in sorted(open_ports, key=lambda x: x['port']):
            service = port['service'][:18]
            danger = f"{Colors.RED}OUI{Colors.END}" if port['dangerous'] else "non"
            print(f"{port['port']:<6} {'TCP':<8} {service:<20} {port['state']:<12} {danger:<8}")
            
            if port.get('banner'):
                banner = port['banner'][:80].replace('\n', '\\n')
                print(f"       📝 {banner}")
        
        dangerous = results['dangerous_ports']
        if dangerous:
            print(f"\n{Colors.RED}🚨 RECOMMANDATIONS DE SÉCURITÉ:{Colors.END}")
            for port in dangerous:
                print(f"  • Port {port['port']} ({port['service']}): {self.DANGEROUS_PORTS.get(port['port'], 'Risque connu')}")
                print(f"    → Considérer la fermeture ou la sécurisation")
        
        return results
    
    def network_scan(self, network_cidr: str) -> Dict:
        """Scan de tout un réseau"""
        print(f"{Colors.BOLD}🌐 Scan du réseau: {network_cidr}{Colors.END}")
        print(f"{Colors.CYAN}{'='*80}{Colors.END}")
        
        try:
            network = ipaddress.ip_network(network_cidr, strict=False)
            hosts = list(network.hosts())
            
            print(f"Réseau: {network_cidr}")
            print(f"Plage: {network[1]} - {network[-2]}")
            print(f"Hôtes à scanner: {len(hosts)}\n")
            
            active_hosts = []
            futures = []
            
            for host in hosts[:50]:
                host_str = str(host)
                future = self.thread_pool.submit(self.check_host_alive, host_str)
                futures.append((host_str, future))
            
            print(f"{Colors.YELLOW}⏳ Recherche d'hôtes actifs...{Colors.END}")
            for host_str, future in futures:
                if future.result():
                    active_hosts.append(host_str)
                    print(f"  {Colors.GREEN}✓{Colors.END} {host_str}")
            
            print(f"\n{Colors.BOLD}🔍 Analyse des hôtes actifs:{Colors.END}")
            network_results = {
                'network': network_cidr,
                'total_hosts': len(hosts),
                'active_hosts': active_hosts,
                'host_details': {}
            }
            
            common_ports = [22, 23, 80, 135, 139, 443, 445, 3389, 8080]
            for host in active_hosts[:10]:
                print(f"\n  Hôte: {host}")
                open_ports = []
                
                for port in common_ports:
                    result = self.scan_port(host, port, 'tcp')
                    if result['state'] == 'open':
                        open_ports.append(result)
                        print(f"    {Colors.GREEN}✓{Colors.END} Port {port} ({result['service']})")
                
                network_results['host_details'][host] = {
                    'open_ports': open_ports,
                    'open_count': len(open_ports)
                }
            
            print(f"\n{Colors.BOLD}📊 RÉSUMÉ RÉSEAU:{Colors.END}")
            print(f"  • Hôtes dans le réseau: {len(hosts)}")
            print(f"  • Hôtes actifs trouvés: {len(active_hosts)}")
            print(f"  • Taux de réponse: {(len(active_hosts)/len(hosts))*100:.1f}%")
            
            return network_results
            
        except Exception as e:
            print(f"{Colors.RED}❌ Erreur: {e}{Colors.END}")
            return {}
    
    def vulnerability_scan(self, host: str) -> Dict:
        """Scan basique de vulnérabilités"""
        print(f"{Colors.BOLD}🛡️  Scan de vulnérabilités: {host}{Colors.END}")
        print(f"{Colors.CYAN}{'='*80}{Colors.END}")
        
        vulns = []
        
        open_ports = self.quick_port_scan(host)
        
        for port_info in open_ports:
            port = port_info['port']
            service = port_info['service']
            
            if port == 21:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    sock.connect((host, 21))
                    sock.recv(1024)
                    sock.send(b"USER anonymous\r\n")
                    response = sock.recv(1024).decode()
                    if "331" in response:
                        sock.send(b"PASS anonymous\r\n")
                        response = sock.recv(1024).decode()
                        if "230" in response:
                            vulns.append({
                                'port': port,
                                'service': service,
                                'risk': 'HIGH',
                                'description': 'FTP anonyme activé',
                                'recommendation': 'Désactiver l\'accès anonyme FTP'
                            })
                    sock.close()
                except:
                    pass
            
            elif port in [80, 443, 8080, 8443]:
                try:
                    protocol = 'https' if port in [443, 8443] else 'http'
                    
                    if protocol == 'https':
                        conn = http.client.HTTPSConnection(host, port, timeout=5)
                    else:
                        conn = http.client.HTTPConnection(host, port, timeout=5)
                    
                    conn.request("HEAD", "/")
                    response = conn.getresponse()
                    headers = response.getheaders()
                    
                    security_headers = ['X-Frame-Options', 'X-Content-Type-Options', 
                                       'X-XSS-Protection', 'Strict-Transport-Security']
                    missing_headers = []
                    
                    for header in security_headers:
                        if not any(h[0].lower() == header.lower() for h in headers):
                            missing_headers.append(header)
                    
                    if missing_headers:
                        vulns.append({
                            'port': port,
                            'service': service,
                            'risk': 'MEDIUM',
                            'description': f'En-têtes de sécurité manquants: {", ".join(missing_headers)}',
                            'recommendation': 'Ajouter les en-têtes de sécurité HTTP'
                        })
                    
                    conn.close()
                except:
                    pass
            
            elif port == 445:
                vulns.append({
                    'port': port,
                    'service': service,
                    'risk': 'HIGH',
                    'description': 'Port SMB ouvert - risque d\'exploitation (EternalBlue, WannaCry)',
                    #'recommendation': 'Mettre à jour Windows ou désactiver SMBv1',
                    'recommendation': 'Dans votre Powershell fermez le port : New-NetFirewallRule -DisplayName "SECU-BLOCK-SMB-445-IN" -Direction Inbound -Protocol TCP -LocalPort 445 -Action Block -RemoteAddress 192.168.1.0/24 -Profile Any'
                })
            
            elif port == 23:
                vulns.append({
                    'port': port,
                    'service': service,
                    'risk': 'CRITICAL',
                    'description': 'Telnet actif - credentials en clair',
                    'recommendation': 'Remplacer par SSH'
                })
            
            elif port == 3389:
                vulns.append({
                    'port': port,
                    'service': service,
                    'risk': 'HIGH',
                    'description': 'RDP exposé - risque de bruteforce/BlueKeep',
                    'recommendation': 'Mettre à jour Windows, utiliser VPN ou RDP Gateway'
                })
        
        if vulns:
            print(f"\n{Colors.RED}🚨 VULNÉRABILITÉS DÉTECTÉES:{Colors.END}")
            
            for vuln in vulns:
                risk_color = Colors.RED if vuln['risk'] in ['CRITICAL', 'HIGH'] else Colors.YELLOW
                print(f"\n{risk_color}[{vuln['risk']}]{Colors.END} Port {vuln['port']} ({vuln['service']})")
                print(f"   📝 {vuln['description']}")
                print(f"   💡 {Colors.GREEN}{vuln['recommendation']}{Colors.END}")
        else:
            print(f"\n{Colors.GREEN}✅ Aucune vulnérabilité évidente détectée{Colors.END}")
        
        return {
            'host': host,
            'open_ports': len(open_ports),
            'vulnerabilities': vulns,
            'scan_time': datetime.now().isoformat()
        }
    
    def service_detection(self, host: str, port: int) -> Dict:
        """Détection détaillée d'un service"""
        print(f"{Colors.BOLD}🔧 Analyse du service {host}:{port}{Colors.END}")
        print(f"{Colors.CYAN}{'='*80}{Colors.END}")
        
        result = self.scan_port(host, port, 'tcp')
        
        if result['state'] != 'open':
            print(f"{Colors.RED}❌ Port {port} fermé ou filtré{Colors.END}")
            return result
        
        print(f"{Colors.GREEN}✅ Port {port} ouvert{Colors.END}")
        print(f"Service probable: {result['service']}")
        
        if port in [80, 443, 8080, 8443]:
            self._analyze_web_service(host, port)
        elif port == 21:
            self._analyze_ftp_service(host, port)
        elif port == 22:
            self._analyze_ssh_service(host, port)
        elif port == 25:
            self._analyze_smtp_service(host, port)
        elif port == 3389:
            self._analyze_rdp_service(host, port)
        
        return result
    
    def _analyze_web_service(self, host: str, port: int):
        """Analyse détaillée d'un service web"""
        protocol = 'https' if port in [443, 8443] else 'http'
        url = f"{protocol}://{host}:{port}/"
        
        print(f"\n{Colors.BOLD}🌐 Analyse du service web:{Colors.END}")
        print(f"URL: {url}")
        
        try:
            if protocol == 'https':
                conn = http.client.HTTPSConnection(host, port, timeout=5)
            else:
                conn = http.client.HTTPConnection(host, port, timeout=5)
            
            conn.request("HEAD", "/")
            response = conn.getresponse()
            
            print(f"Status: {response.status} {response.reason}")
            print(f"Server: {response.getheader('Server', 'Inconnu')}")
            
            print(f"\n{Colors.BOLD}🔒 En-têtes de sécurité:{Colors.END}")
            security_headers = {
                'X-Frame-Options': 'Protection contre le clickjacking',
                'X-Content-Type-Options': 'Empêche MIME sniffing',
                'X-XSS-Protection': 'Protection XSS',
                'Content-Security-Policy': 'Politique de sécurité du contenu',
                'Strict-Transport-Security': 'Force HTTPS',
                'Referrer-Policy': 'Contrôle des referrers'
            }
            
            for header, description in security_headers.items():
                value = response.getheader(header)
                if value:
                    print(f"  {Colors.GREEN}✓{Colors.END} {header}: {value}")
                else:
                    print(f"  {Colors.RED}✗{Colors.END} {header}: Manquant - {description}")
            
            print(f"\n{Colors.BOLD}🔍 Technologies potentielles:{Colors.END}")
            server_header = response.getheader('Server', '').lower()
            
            tech_indicators = {
                'apache': ['apache', 'httpd'],
                'nginx': ['nginx'],
                'iis': ['microsoft-iis', 'iis'],
                'node.js': ['node', 'express'],
                'php': ['php'],
                'asp.net': ['asp.net', 'x-aspnet-version']
            }
            
            for tech, indicators in tech_indicators.items():
                if any(indicator in server_header for indicator in indicators):
                    print(f"  • {tech}")
            
            print(f"\n{Colors.BOLD}📁 Répertoires communs:{Colors.END}")
            common_dirs = ['/admin', '/login', '/wp-admin', '/phpmyadmin', '/test', '/backup']
            
            for directory in common_dirs:
                try:
                    conn.request("GET", directory)
                    dir_response = conn.getresponse()
                    if dir_response.status in [200, 301, 302]:
                        print(f"  {Colors.YELLOW}⚠️{Colors.END} {directory} - {dir_response.status}")
                except:
                    continue
            
            conn.close()
            
        except Exception as e:
            print(f"{Colors.RED}Erreur d'analyse: {e}{Colors.END}")
    
    def _analyze_ftp_service(self, host: str, port: int):
        """Analyse du service FTP"""
        print(f"\n{Colors.BOLD}📁 Analyse FTP:{Colors.END}")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((host, port))
            
            banner = sock.recv(1024).decode('utf-8', errors='ignore')
            print(f"Bannière: {banner.strip()}")
            
            sock.send(b"USER anonymous\r\n")
            response = sock.recv(1024).decode()
            if "331" in response:
                print(f"{Colors.YELLOW}⚠️  FTP anonyme supporté{Colors.END}")
            
            sock.close()
            
        except Exception as e:
            print(f"Erreur: {e}")
    
    def _analyze_ssh_service(self, host: str, port: int):
        """Analyse du service SSH"""
        print(f"\n{Colors.BOLD}🔑 Analyse SSH:{Colors.END}")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((host, port))
            
            banner = sock.recv(1024).decode('utf-8', errors='ignore')
            print(f"Bannière: {banner.strip()}")
            
            if 'OpenSSH' in banner:
                print("Service: OpenSSH")
            elif 'SSH-2.0' in banner:
                print("Service: SSH Protocol 2.0")
            
            sock.close()
            
        except Exception as e:
            print(f"Erreur: {e}")
    
    def _analyze_rdp_service(self, host: str, port: int):
        """Analyse du service RDP"""
        print(f"\n{Colors.BOLD}🖥️  Analyse RDP:{Colors.END}")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((host, port))
            
            sock.send(b'\x03\x00\x00\x13\x0e\xe0\x00\x00\x00\x00\x00\x01\x00\x08\x00\x03\x00\x00\x00')
            response = sock.recv(1024)
            
            if response:
                print(f"RDP actif - Longueur réponse: {len(response)} bytes")
                
                if len(response) > 20 and response[0] == 0x03:
                    print(f"{Colors.YELLOW}⚠️  Possible vulnérabilité BlueKeep (à vérifier){Colors.END}")
            
            sock.close()
            
        except Exception as e:
            print(f"Erreur: {e}")
    
    def _analyze_smtp_service(self, host: str, port: int):
        """Analyse du service SMTP"""
        print(f"\n{Colors.BOLD}📧 Analyse SMTP:{Colors.END}")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((host, port))
            
            banner = sock.recv(1024).decode('utf-8', errors='ignore')
            print(f"Bannière: {banner.strip()}")
            
            sock.send(b"VRFY root\r\n")
            response = sock.recv(1024).decode()
            if "252" in response or "250" in response:
                print(f"{Colors.RED}⚠️  Commande VRFY activée - énumération possible{Colors.END}")
            
            sock.close()
            
        except Exception as e:
            print(f"Erreur: {e}")

# ================= FONCTIONS DE SCAN SYSTÈME (CODE INITIAL) =================
class SystemScanner:
    def __init__(self):
        self.alerts = []
        self.suspect_processes = []
        self.scan_history = []
        self.performance_log = []
        self.log_file = f"helpdesk_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.network_scanner = NetworkScanner()
        
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
        return alert
    
    def scan_processes(self, detailed=False, sort_by='cpu'):
        """Scan les processus avec détection de comportements suspects"""
        print(f"\n{Colors.BOLD}🔍 SCAN DES PROCESSUS - {datetime.now().strftime('%H:%M:%S')}{Colors.END}")
        print(f"{Colors.CYAN}{'='*100}{Colors.END}")
        
        suspect_patterns = {
            'miner': ['miner', 'coin', 'xmr', 'monero', 'bitcoin', 'eth', 'ether', 'cryptonight'],
            'injection': ['inject', 'hook', 'dllinject', 'processhacker'],
            'scripting': ['powershell', 'wscript', 'cscript', 'cmd', 'python', 'perl', 'bash'],
            'system_abuse': ['svchost', 'services', 'lsass', 'winlogon', 'csrss'],
            'obfuscation': ['setup', 'install', 'update', 'updater', 'java', 'runtime']
        }
        
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
                
                pinfo['risk_score'] = 0
                pinfo['flags'] = []
                
                if pinfo['cpu_percent'] > 70:
                    pinfo['risk_score'] += 3
                    pinfo['flags'].append('HIGH_CPU')
                    self.add_alert('HIGH', 
                        f"Processus gourmand CPU: {pinfo['name']} (PID:{pinfo['pid']}) - {pinfo['cpu_percent']}% CPU",
                        pinfo)
                
                if pinfo['memory_percent'] > 15 or pinfo['memory_mb'] > 500:
                    pinfo['risk_score'] += 2
                    pinfo['flags'].append('HIGH_MEM')
                    self.add_alert('MEDIUM',
                        f"Processus gourmand mémoire: {pinfo['name']} - {pinfo['memory_mb']:.1f}MB ({pinfo['memory_percent']:.1f}%)",
                        pinfo)
                
                if pinfo.get('num_threads', 0) > 50:
                    pinfo['risk_score'] += 1
                    pinfo['flags'].append('MANY_THREADS')
                
                if pinfo.get('num_handles', 0) > 1000:
                    pinfo['risk_score'] += 2
                    pinfo['flags'].append('MANY_HANDLES')
                
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
                
                if pinfo['exe']:
                    suspicious_paths = ['temp', 'appdata', 'roaming', 'downloads', 'cache']
                    exe_lower = pinfo['exe'].lower()
                    if any(path in exe_lower for path in suspicious_paths):
                        pinfo['risk_score'] += 2
                        pinfo['flags'].append('SUSPECT_PATH')
                        self.add_alert('MEDIUM',
                            f"Processus dans dossier suspect: {pinfo['name']} -> {pinfo['exe']}",
                            pinfo)
                
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
        
        if sort_by == 'cpu':
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        elif sort_by == 'memory':
            processes.sort(key=lambda x: x['memory_mb'], reverse=True)
        elif sort_by == 'risk':
            processes.sort(key=lambda x: x['risk_score'], reverse=True)
        elif sort_by == 'name':
            processes.sort(key=lambda x: x['name'].lower())
        
        if detailed:
            print(f"{'Nom':25} {'PID':>6} {'PPID':>6} {'CPU%':>6} {'MEM(MB)':>8} {'Threads':>7} {'Handles':>8} {'Risque':>6} {'Utilisateur':15}")
            print(f"{'-'*100}")
            
            for pinfo in processes[:50]:
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
                
                if pinfo['risk_score'] > 3 and pinfo['flags']:
                    print(f"       ⚠️ {Colors.YELLOW}{', '.join(pinfo['flags'][:3])}{Colors.END}")
        
        print(f"\n{Colors.BOLD}📊 STATISTIQUES:{Colors.END}")
        print(f"  • Processus analysés: {len(processes)}")
        
        high_risk = len([p for p in processes if p['risk_score'] > 5])
        medium_risk = len([p for p in processes if 2 < p['risk_score'] <= 5])
        
        print(f"  • Processus à haut risque: {Colors.RED}{high_risk}{Colors.END}")
        print(f"  • Processus à risque moyen: {Colors.YELLOW}{medium_risk}{Colors.END}")
        
        total_memory = sum(p.get('memory_mb', 0) for p in processes)
        print(f"  • Mémoire totale utilisée: {total_memory:.1f} MB")
        
        top_cpu = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:3]
        if top_cpu:
            print(f"  • Top 3 CPU: {', '.join([f'{p['name']} ({p['cpu_percent']:.1f}%)' for p in top_cpu])}")
        
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
            
            for pinfo in results[:20]:
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
                    
                    threat_color = Colors.RED if threat_level == 'HIGH' else Colors.YELLOW if threat_level == 'MEDIUM' else Colors.GREEN
                    print(f"{proc_info.get('name', 'SYSTEM'):25} "
                          f"{conn_info['local']:25} -> {conn_info['remote']:25} "
                          f"{conn_info['status']:12} {threat_color}{threat_level:7}{Colors.END}")
                    
            except (AttributeError, IndexError, psutil.AccessDenied):
                continue
        
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
        
        print(f"\n{Colors.BOLD}🌐 RÉSEAU:{Colors.END}")
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
            print(f"  • IP locale: {local_ip}")
        except:
            print(f"  • IP locale: {Colors.YELLOW}Indisponible{Colors.END}")
        
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
        
        print(f"\n{Colors.BOLD}👥 UTILISATEURS:{Colors.END}")
        users = psutil.users()
        for user in users[:5]:
            print(f"  • {user.name} depuis {user.host or 'local'} (depuis {datetime.fromtimestamp(user.started).strftime('%H:%M:%S')})")
        
        return infos
    
    def scan_malware_indicators(self):
        """Recherche d'indicateurs de malware"""
        print(f"\n{Colors.BOLD}🕵️  ANALYSE MALWARE / INDICATEURS{Colors.END}")
        print(f"{Colors.CYAN}{'='*100}{Colors.END}")
        
        indicators = []
        
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
        
        print(f"\n{Colors.BOLD}3. Fichiers temporaires suspects:{Colors.END}")
        temp_dirs = ['C:\\Windows\\Temp', os.environ.get('TEMP', '')]
        suspect_ext = ['.exe', '.dll', '.vbs', '.js', '.bat', '.ps1']
        
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                try:
                    files = os.listdir(temp_dir)[-10:]
                    for file in files:
                        if any(file.endswith(ext) for ext in suspect_ext):
                            filepath = os.path.join(temp_dir, file)
                            try:
                                size = os.path.getsize(filepath)
                                if size > 1024 * 1024:
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
        
        print(f"\n{Colors.BOLD}4. Services suspects:{Colors.END}")
        if os.name == 'nt':
            try:
                import win32service
                import win32con
                
                service_keywords = ['update', 'client', 'helper', 'service', 'host']
                sc = win32service.OpenSCManager(None, None, win32con.SC_MANAGER_ENUMERATE_SERVICE)
                services = win32service.EnumServicesStatus(sc, win32service.SERVICE_WIN32, win32service.SERVICE_STATE_ALL)
                
                for service in services[:20]:
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
        
        print(f"\n{Colors.BOLD}📊 RÉSUMÉ DE L'ANALYSE:{Colors.END}")
        print(f"  • Total indicateurs trouvés: {len(indicators)}")
        
        if indicators:
            print(f"  • {Colors.RED}⚠️  Des indicateurs de malware ont été détectés!{Colors.END}")
            print(f"  • {Colors.YELLOW}Recommandation: Analysez avec un antivirus et supprimez les fichiers suspects{Colors.END}")
        else:
            print(f"  • {Colors.GREEN}✅ Aucun indicateur de malware évident détecté{Colors.END}")
        
        return indicators
    
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
    
    def kill_process_by_pid(self, pid):
        """Tue un processus par son PID"""
        try:
            pid = int(pid)
            proc = psutil.Process(pid)
            proc_name = proc.name()
            
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
    
    def real_time_monitor(self, duration=30):
        """Surveillance en temps réel"""
        print(f"\n{Colors.BOLD}📊 SURVEILLANCE TEMPS RÉEL ({duration}s){Colors.END}")
        print(f"{Colors.CYAN}{'='*80}{Colors.END}")
        print("Appuyez sur Ctrl+C pour arrêter\n")
        
        end_time = time.time() + duration
        try:
            while time.time() < end_time:
                os.system('cls' if os.name == 'nt' else 'clear')
                print_header()
                
                cpu_percent = psutil.cpu_percent(interval=1)
                cpu_color = Colors.RED if cpu_percent > 80 else Colors.YELLOW if cpu_percent > 50 else Colors.GREEN
                print(f"{Colors.BOLD}CPU:{Colors.END} {cpu_color}{'█' * int(cpu_percent/2)}{'░' * (50 - int(cpu_percent/2))} {cpu_percent:.1f}%{Colors.END}")
                
                mem = psutil.virtual_memory()
                mem_color = Colors.RED if mem.percent > 80 else Colors.YELLOW if mem.percent > 50 else Colors.GREEN
                print(f"{Colors.BOLD}RAM:{Colors.END} {mem_color}{'█' * int(mem.percent/2)}{'░' * (50 - int(mem.percent/2))} {mem.percent:.1f}%{Colors.END}")
                
                print(f"\n{Colors.BOLD}TOP 5 PROCESSUS (CPU):{Colors.END}")
                for proc in sorted(psutil.process_iter(['name', 'cpu_percent']), 
                                 key=lambda p: p.info['cpu_percent'], reverse=True)[:5]:
                    if proc.info['cpu_percent'] > 0:
                        print(f"  {proc.info['name']:25} {proc.info['cpu_percent']:5.1f}%")
                
                conn_count = len(psutil.net_connections(kind='inet'))
                print(f"\n{Colors.BOLD}CONNEXIONS:{Colors.END} {conn_count} actives")
                
                time.sleep(2)
                
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}⏹️  Surveillance arrêtée{Colors.END}")
    
    def scan_network_nmap(self, target=None):
        """Interface unifiée pour le scan réseau"""
        if not target:
            target = input(f"Cible (IP, hostname ou réseau CIDR): ").strip()
        
        if not target:
            print(f"{Colors.YELLOW}❌ Aucune cible spécifiée{Colors.END}")
            return
        
        print(f"\n{Colors.BOLD}🎯 Options de scan réseau:{Colors.END}")
        print(f"{Colors.GREEN}[1]{Colors.END} Scan rapide (ports communs)")
        print(f"{Colors.GREEN}[2]{Colors.END} Scan complet (1-1024)")
        print(f"{Colors.GREEN}[3]{Colors.END} Scan de vulnérabilités")
        print(f"{Colors.GREEN}[4]{Colors.END} Scan de réseau entier")
        print(f"{Colors.GREEN}[5]{Colors.END} Analyse détaillée d'un service")
        
        choice = input(f"\nChoix [1-5]: ").strip()
        
        if choice == '1':
            self.network_scanner.quick_port_scan(target)
        elif choice == '2':
            self.network_scanner.full_port_scan(target)
        elif choice == '3':
            self.network_scanner.vulnerability_scan(target)
        elif choice == '4':
            if '/' not in target:
                target = input(f"Réseau CIDR (ex: 192.168.1.0/24): ").strip()
            self.network_scanner.network_scan(target)
        elif choice == '5':
            port = input(f"Port à analyser: ").strip()
            if port.isdigit():
                self.network_scanner.service_detection(target, int(port))
            else:
                print(f"{Colors.YELLOW}Port invalide{Colors.END}")
        else:
            print(f"{Colors.YELLOW}Choix invalide{Colors.END}")
    
    def full_scan(self):
        """Scan complet du système"""
        print(f"\n{Colors.BOLD}🚀 SCAN COMPLET DU SYSTÈME{Colors.END}")
        print(f"{Colors.CYAN}{'='*80}{Colors.END}")
        
        print(f"{Colors.YELLOW}⏳ Démarrage du scan...{Colors.END}")
        
        self.scan_system_info_detailed()
        self.scan_processes(detailed=False)
        self.scan_network_detailed()
        self.scan_disks_detailed()
        
        self.show_alerts()
        
        return self.alerts

# ================= INTERFACE UTILISATEUR =================
def print_header():
    """Affiche l'en-tête"""
    print(f"""{Colors.CYAN}
╔══════════════════════════════════════════════════════════════════════════╗
║                   HELP DESK PRO - Terminal de surveillance               ║
║                   avec module Nmap-like intégré                          ║
╚══════════════════════════════════════════════════════════════════════════╝{Colors.END}
""")

def print_status_bar(scanner):
    """Affiche une barre de statut"""
    try:
        mem = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
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
    except:
        pass

def clear_screen():
    """Efface l'écran"""
    os.system('cls' if os.name == 'nt' else 'clear')

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
    
    if os.name == 'nt':
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin:
                print(f"{Colors.YELLOW}⚠️  Attention: Pas en mode administrateur")
                print(f"   Certaines fonctionnalités peuvent être limitées{Colors.END}")
        except:
            pass

def main():
    scanner = SystemScanner()
    history = CommandHistory()
    last_command = ""
    
    check_dependencies()
    
    clear_screen()
    print_header()
    print(f"{Colors.GREEN}✅ Scanner initialisé. Tapez 'help' pour les commandes.{Colors.END}")
    print(f"{Colors.YELLOW}🎯 Module Nmap-like intégré !{Colors.END}")
    print(f"{Colors.CYAN}Commandes réseau: portscan, fullscan, netscan, vulnscan, service{Colors.END}\n")
    
    while True:
        try:
            print_status_bar(scanner)
            
            print(f"""
{Colors.BOLD}📋 MENU RAPIDE:{Colors.END}
{Colors.GREEN}sys{Colors.END}     : Système       {Colors.GREEN}net{Colors.END}     : Réseau
{Colors.GREEN}proc{Colors.END}    : Processus     {Colors.GREEN}disk{Colors.END}    : Disques
{Colors.GREEN}malware{Colors.END} : Analyse       {Colors.GREEN}alert{Colors.END}   : Alertes
{Colors.GREEN}nmap{Colors.END}    : Scan réseau   {Colors.GREEN}help{Colors.END}    : Aide complète
{Colors.GREEN}monitor{Colors.END} : Temps réel    {Colors.GREEN}quit{Colors.END}    : Quitter
""")
            
            prompt = f"\n{Colors.BOLD}helpdesk>{Colors.END} "
            choice = input(prompt).strip().lower()
            
            if not choice and last_command:
                choice = last_command
            else:
                history.add(choice)
                last_command = choice
            
            # Commandes système originales
            if choice in ['1', 'scan-all', 'full']:
                scanner.full_scan()
                
            elif choice in ['2', 'proc', 'process', 'scan-proc']:
                sort_by = input(f"Trier par [cpu/mem/risk/name] (défaut: cpu): ").strip().lower()
                sort_by = sort_by if sort_by in ['cpu', 'mem', 'risk', 'name'] else 'cpu'
                scanner.scan_processes(detailed=True, sort_by=sort_by)
                
            elif choice in ['3', 'net', 'network', 'scan-net']:
                scanner.scan_network_detailed()
                
            elif choice in ['4', 'disk', 'disks', 'scan-disk']:
                scanner.scan_disks_detailed()
                
            elif choice in ['5', 'sys', 'system', 'info', 'scan-sys']:
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
            
            # Commandes Nmap
            elif choice.startswith('portscan ') or choice.startswith('scan '):
                target = choice.split(' ', 1)[1] if len(choice.split()) > 1 else None
                scanner.scan_network_nmap(target)
            
            elif choice.startswith('fullscan '):
                target = choice.split(' ', 1)[1] if len(choice.split()) > 1 else None
                if target:
                    scanner.network_scanner.full_port_scan(target)
                else:
                    print(f"{Colors.YELLOW}Usage: fullscan IP_OU_HOSTNAME{Colors.END}")
            
            elif choice.startswith('netscan '):
                network = choice.split(' ', 1)[1] if len(choice.split()) > 1 else None
                if network:
                    scanner.network_scanner.network_scan(network)
                else:
                    print(f"{Colors.YELLOW}Usage: netscan RESEAU_CIDR (ex: 192.168.1.0/24){Colors.END}")
            
            elif choice.startswith('vulnscan '):
                target = choice.split(' ', 1)[1] if len(choice.split()) > 1 else None
                if target:
                    scanner.network_scanner.vulnerability_scan(target)
                else:
                    print(f"{Colors.YELLOW}Usage: vulnscan IP_OU_HOSTNAME{Colors.END}")
            
            elif choice.startswith('service '):
                parts = choice.split(' ', 2)
                if len(parts) >= 3:
                    target = parts[1]
                    port = parts[2]
                    if port.isdigit():
                        scanner.network_scanner.service_detection(target, int(port))
                    else:
                        print(f"{Colors.YELLOW}Port invalide{Colors.END}")
                else:
                    print(f"{Colors.YELLOW}Usage: service HOST PORT{Colors.END}")
            
            elif choice == 'nmap':
                scanner.scan_network_nmap()
            
            # Commandes d'administration
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
             
            elif choice in ['8', 'quit', 'exit', 'q']:
                print(f"\n{Colors.GREEN}👋 Au revoir !{Colors.END}")
                print(f"📊 Résumé de la session:")
                print(f"   • Alertes générées: {len(scanner.alerts)}")
                print(f"   • Commandes exécutées: {len(history.history)}")
                print(f"   • Fichier de log: {scanner.log_file}")
                print(f"{Colors.CYAN}Toolkit by gael-berru.com{Colors.END}\n")
                break
            
            elif choice == 'help':
                print(f"""
{Colors.BOLD}📚 AIDE COMPLÈTE - HELP DESK PRO{Colors.END}

{Colors.BOLD}🔍 SCAN SYSTÈME (ORIGINAL):{Colors.END}
  {Colors.GREEN}scan-all{Colors.END}     : Scan système complet
  {Colors.GREEN}proc{Colors.END}         : Liste des processus avec risques
  {Colors.GREEN}net{Colors.END}          : Connexions réseau actives
  {Colors.GREEN}disk{Colors.END}         : Espace disque et fichiers temp
  {Colors.GREEN}sys{Colors.END}          : Informations système détaillées
  {Colors.GREEN}monitor{Colors.END}      : Surveillance temps réel
  {Colors.GREEN}malware{Colors.END}      : Analyse indicateurs malware
  {Colors.GREEN}find NOM{Colors.END}     : Rechercher processus
  {Colors.GREEN}kill NOM{Colors.END}     : Tuer processus par nom
  {Colors.GREEN}killpid PID{Colors.END}  : Tuer processus par PID

{Colors.BOLD}🎯 SCAN RÉSEAU (NMAP-LIKE):{Colors.END}
  {Colors.GREEN}portscan HOST{Colors.END} : Scan rapide ports communs
  {Colors.GREEN}fullscan HOST{Colors.END} : Scan complet ports 1-1024
  {Colors.GREEN}netscan CIDR{Colors.END}  : Scan réseau entier (ex: 192.168.1.0/24)
  {Colors.GREEN}vulnscan HOST{Colors.END} : Scan vulnérabilités basiques
  {Colors.GREEN}service HOST PORT{Colors.END} : Analyse détaillée service
  {Colors.GREEN}nmap{Colors.END}          : Menu interactif scan réseau

{Colors.BOLD}⚡ COMMANDES RAPIDES:{Colors.END}
  {Colors.GREEN}alert{Colors.END}         : Voir alertes sécurité
  {Colors.GREEN}log{Colors.END}           : Exporter logs en JSON
  {Colors.GREEN}history{Colors.END}       : Historique commandes
  {Colors.GREEN}clear{Colors.END}         : Effacer l'écran
  {Colors.GREEN}quit{Colors.END}          : Quitter

{Colors.BOLD}📝 EXEMPLES:{Colors.END}
  proc                        # Liste processus
  find chrome                 # Recherche Chrome
  kill malware.exe            # Tuer malware
  portscan 192.168.1.1       # Scan réseau
  netscan 192.168.1.0/24     # Scan réseau entier
  service google.com 80      # Analyse web
""")
            
            elif choice == '':
                continue
                
            else:
                print(f"{Colors.YELLOW}❓ Commande non reconnue: '{choice}'{Colors.END}")
                print(f"   Tapez {Colors.CYAN}help{Colors.END} pour la liste des commandes")
            
            print(f"\n{Colors.CYAN}{'─'*80}{Colors.END}")
            
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}\n⚠️  Ctrl+C détecté. Tapez 'quit' pour quitter.{Colors.END}")
            continue
        except Exception as e:
            print(f"{Colors.RED}❌ Erreur: {e}{Colors.END}")
            import traceback
            traceback.print_exc()
            time.sleep(2)

# ================= POINT D'ENTRÉE =================
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.GREEN}👋 Au revoir !{Colors.END}")
    except Exception as e:
        print(f"{Colors.RED}❌ Erreur critique: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        input("Appuyez sur Entrée pour quitter...")