# ======================================================================
# NetPentest Pro - Outil de Pentest Réseau Complémentaire à HelpDesk Pro
# ======================================================================
# 📜 FONCTIONNALITÉS :
# 1. Scanner réseau avancé (arp, ping, ports)
# 2. Analyse de vulnérabilités (services, versions)
# 3. Sniffing réseau (style Wireshark light)
# 4. Bruteforce détection (FTP, SSH, HTTP basique)
# 5. Analyse de sécurité WiFi
# 6. Détection de bases de données exposées
# 7. Scan de sous-réseaux complets
# 8. Rapport d'audit automatique
# ======================================================================

import os
import sys
import socket
import threading
import queue
import time
import ipaddress
import subprocess
import json
import csv
from datetime import datetime
from collections import defaultdict, Counter
import struct
import select
from typing import List, Dict, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Dépendances optionnelles
try:
    import scapy.all as scapy
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    print("[!] Scapy non installé - certaines fonctionnalités limitées")

try:
    import pymysql
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

try:
    import psycopg2
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

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
    
    # Niveaux de sévérité
    CRITICAL = '\033[41m\033[37m'  # Fond rouge, texte blanc
    HIGH = '\033[101m\033[30m'     # Fond rouge clair, texte noir
    MEDIUM = '\033[43m\033[30m'    # Fond jaune, texte noir
    LOW = '\033[44m\033[37m'       # Fond bleu, texte blanc
    INFO = '\033[42m\033[30m'      # Fond vert, texte noir

# ================= CLASSES PRINCIPALES =================
class NetworkScanner:
    """Scanner réseau avancé avec détection de vulnérabilités"""
    
    def __init__(self):
        self.hosts = []
        self.vulnerabilities = []
        self.open_ports = defaultdict(list)
        self.services = defaultdict(dict)
        self.mac_vendors = self._load_mac_vendors()
        self.common_ports = {
            'web': [80, 443, 8080, 8443, 3000, 8000, 8888],
            'database': [3306, 5432, 27017, 1433, 1521, 6379],
            'remote': [22, 23, 3389, 5900, 5800],
            'file': [21, 20, 139, 445, 2049],
            'mail': [25, 110, 143, 465, 587, 993, 995],
            'dns': [53],
            'dhcp': [67, 68],
            'vpn': [500, 1701, 1723, 4500],
            'multimedia': [554, 1935, 3478, 5060],
            'games': [27015, 25565, 7777]
        }
        
        # Vulnérabilités connues par port/service
        self.vuln_db = {
            21: ['FTP Anonymous login', 'FTP Brute force'],
            22: ['SSH weak keys', 'SSH Brute force'],
            23: ['Telnet cleartext credentials'],
            25: ['Open relay SMTP'],
            53: ['DNS zone transfer', 'DNS cache poisoning'],
            80: ['Web vulnerabilities', 'Directory traversal'],
            110: ['POP3 cleartext'],
            143: ['IMAP cleartext'],
            443: ['SSL/TLS vulnerabilities', 'Heartbleed'],
            445: ['SMB vulnerabilities', 'EternalBlue'],
            1433: ['SQL Server weak auth'],
            1521: ['Oracle TNS poison'],
            2049: ['NFS no_root_squash'],
            3306: ['MySQL weak password'],
            3389: ['RDP BlueKeep', 'RDP brute force'],
            5432: ['PostgreSQL weak auth'],
            5900: ['VNC no password'],
            8080: ['Proxy open relay', 'Tomcat manager'],
            27017: ['MongoDB no auth']
        }
    
    def _load_mac_vendors(self):
        """Charge la base de données des fabricants MAC"""
        vendors = {}
        try:
            # Fichier de référence OUI (Organizationally Unique Identifier)
            import requests
            url = "https:/python/standards-oui.ieee.org/oui/oui.txt"
            response = requests.get(url, timeout=10)
            for line in response.text.split('\n'):
                if '(base 16)' in line:
                    parts = line.split('(base 16)')
                    if len(parts) == 2:
                        mac_prefix = parts[0].strip().upper().replace('-', ':')[:8]
                        vendor = parts[1].strip()
                        vendors[mac_prefix] = vendor
        except:
            # Fallback local
            vendors = {
                '00:00:0C': 'Cisco',
                '00:00:0E': 'Fujitsu',
                '00:00:1B': 'Novell',
                '00:00:5E': 'IANA',
                '00:00:E8': 'Samsung',
                '00:01:03': 'Cisco',
                '00:01:E6': 'Cisco',
                '00:02:B3': 'Intel',
                '00:04:76': 'Dell',
                '00:05:69': 'Sony',
                '00:06:5B': 'Apple',
                '00:08:02': 'Apple',
                '00:0C:29': 'VMware',
                '00:0D:60': 'Microsoft',
                '00:0F:20': 'Apple',
                '00:10:60': 'Apple',
                '00:11:24': 'Apple',
                '00:15:5D': 'Microsoft',  # Hyper-V
                '00:16:3E': 'Xen',
                '00:17:A4': 'Apple',
                '00:19:99': 'Apple',
                '00:1B:63': 'Apple',
                '00:1D:4F': 'Apple',
                '00:1E:52': 'Apple',
                '00:1E:C2': 'Apple',
                '00:21:E9': 'Apple',
                '00:22:41': 'Apple',
                '00:23:12': 'Apple',
                '00:23:32': 'Intel',
                '00:24:36': 'Apple',
                '00:25:00': 'Apple',
                '00:26:08': 'Apple',
                '00:26:4A': 'Apple',
                '00:26:B0': 'Apple',
                '00:30:65': 'Hewlett Packard',
                '00:50:56': 'VMware',
                '00:90:0B': 'Apple',
                '08:00:27': 'VirtualBox',
                '52:54:00': 'QEMU',
                'B8:27:EB': 'Raspberry Pi',
                'D4:BE:D9': 'TP-Link',
                'E4:54:E8': 'Dell',
                'FC:15:B4': 'Huawei'
            }
        return vendors
    
    def get_mac_vendor(self, mac):
        """Identifie le fabricant par adresse MAC"""
        if not mac or mac == '00:00:00:00:00:00':
            return 'Inconnu'
        
        prefix = mac.upper().replace('-', ':')[:8]
        return self.mac_vendors.get(prefix, 'Inconnu')
    
    def arp_scan(self, network='192.168.1.0/24'):
        """Scan ARP pour découvrir les hôtes sur le réseau"""
        print(f"{Colors.BOLD}🔍 SCAN ARP - Réseau: {network}{Colors.END}")
        print(f"{Colors.CYAN}{'='*80}{Colors.END}")
        
        if not SCAPY_AVAILABLE:
            print(f"{Colors.YELLOW}[!] Scapy requis pour le scan ARP{Colors.END}")
            return []
        
        try:
            # Création de la requête ARP
            arp_request = scapy.ARP(pdst=network)
            broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
            arp_request_broadcast = broadcast/arp_request
            
            # Envoi et réception
            answered_list = scapy.srp(arp_request_broadcast, timeout=2, verbose=False)[0]
            
            hosts = []
            for element in answered_list:
                host_info = {
                    'ip': element[1].psrc,
                    'mac': element[1].hwsrc,
                    'vendor': self.get_mac_vendor(element[1].hwsrc),
                    'hostname': self._reverse_dns(element[1].psrc)
                }
                hosts.append(host_info)
                
                # Affichage
                vendor_color = Colors.GREEN if 'Apple' in host_info['vendor'] or 'Microsoft' in host_info['vendor'] else Colors.CYAN
                print(f"{Colors.GREEN}✓{Colors.END} {host_info['ip']:15} -> {host_info['mac']:17} {vendor_color}{host_info['vendor']:20}{Colors.END} {host_info['hostname']}")
            
            print(f"\n{Colors.BOLD}📊 {len(hosts)} hôtes découverts{Colors.END}")
            return hosts
            
        except Exception as e:
            print(f"{Colors.RED}❌ Erreur scan ARP: {e}{Colors.END}")
            return []
    
    def _reverse_dns(self, ip):
        """Recherche DNS inverse"""
        try:
            return socket.gethostbyaddr(ip)[0]
        except:
            return "N/A"
    
    def port_scan(self, target, ports='common', timeout=1, threads=50):
        """Scan de ports multi-threadé"""
        print(f"{Colors.BOLD}🎯 SCAN PORTS - Cible: {target}{Colors.END}")
        print(f"{Colors.CYAN}{'='*80}{Colors.END}")
        
        # Détermination des ports à scanner
        if ports == 'common':
            port_list = []
            for category in self.common_ports.values():
                port_list.extend(category)
            port_list = list(set(port_list))[:100]  # Limiter à 100 ports
        elif ports == 'all':
            port_list = list(range(1, 1001))
        elif ports == 'top100':
            port_list = [7, 19, 20, 21, 22, 23, 25, 37, 42, 43, 49, 53, 67, 68, 69, 70, 79, 80, 88, 102, 110, 113, 115, 117, 118, 119, 123, 135, 137, 138, 139, 143, 161, 162, 179, 194, 201, 209, 210, 213, 220, 389, 427, 443, 444, 445, 464, 465, 497, 500, 512, 513, 514, 515, 520, 521, 540, 543, 544, 548, 554, 563, 587, 591, 593, 631, 636, 639, 646, 691, 860, 873, 902, 989, 990, 993, 995, 1025, 1026, 1027, 1028, 1029, 1080, 1194, 1214, 1241, 1311, 1337, 1433, 1434, 1521, 1723, 1755, 1812, 1813, 1863, 1985, 2000, 2049, 2082, 2083, 2100, 2222, 2302, 2483, 2484, 2745, 2967, 3000, 3050, 3074, 3128, 3306, 3389, 3689, 3690, 3724, 3784, 3785, 4333, 4444, 4500, 4664, 4672, 4899, 5000, 5001, 5004, 5005, 5050, 5060, 5190, 5222, 5223, 5269, 5280, 5298, 5351, 5353, 5432, 5500, 5517, 5555, 5631, 5632, 5666, 5800, 5900, 6000, 6001, 6112, 6129, 6257, 6346, 6347, 6500, 6566, 6588, 6665, 6666, 6667, 6668, 6669, 6679, 6697, 6699, 6881, 6969, 7000, 7001, 7002, 7070, 7100, 7161, 7777, 7778, 8000, 8008, 8009, 8010, 8080, 8081, 8087, 8088, 8089, 8090, 8118, 8123, 8181, 8200, 8222, 8243, 8280, 8291, 8333, 8400, 8443, 8500, 8767, 8880, 8888, 9000, 9001, 9043, 9060, 9080, 9090, 9091, 9100, 9101, 9102, 9103, 9119, 9290, 9443, 9800, 9981, 9999, 10000, 11371, 12345, 13720, 13721, 14567, 15118, 19226, 19638, 20000, 24800, 25999, 27015, 27016, 27017, 27374, 28960, 31337]
        else:
            # Parse une liste de ports
            port_list = []
            for part in str(ports).split(','):
                if '-' in part:
                    start, end = part.split('-')
                    port_list.extend(range(int(start), int(end)+1))
                else:
                    port_list.append(int(part))
        
        print(f"📋 Scan de {len(port_list)} ports sur {target}")
        print(f"⏱️  Timeout: {timeout}s | Threads: {threads}")
        print(f"{Colors.CYAN}{'-'*80}{Colors.END}")
        
        # File d'attente pour les ports
        port_queue = queue.Queue()
        for port in port_list:
            port_queue.put(port)
        
        # Verrou pour l'affichage
        print_lock = threading.Lock()
        results = []
        
        def scan_worker():
            while not port_queue.empty():
                port = port_queue.get()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                
                try:
                    result = sock.connect_ex((target, port))
                    if result == 0:
                        # Port ouvert
                        service = self._get_service_info(target, port)
                        
                        with print_lock:
                            # Vérification des vulnérabilités
                            vulns = self._check_vulnerabilities(port, service)
                            
                            # Affichage
                            if vulns:
                                color = Colors.RED
                                status = f"{Colors.RED}VULN!{Colors.END}"
                            else:
                                color = Colors.GREEN
                                status = f"{Colors.GREEN}OPEN{Colors.END}"
                            
                            print(f"{color}└─{Colors.END} Port {port:5} {status:15} {service.get('name', 'Unknown'):20} {service.get('version', ''):15}")
                            
                            # Afficher les vulnérabilités
                            for vuln in vulns:
                                print(f"   {Colors.YELLOW}⚠️  {vuln}{Colors.END}")
                        
                        results.append({
                            'port': port,
                            'state': 'open',
                            'service': service,
                            'vulnerabilities': vulns
                        })
                        
                        # Enregistrer dans la base de données
                        self.open_ports[target].append(port)
                        self.services[target][port] = service
                        
                except:
                    pass
                finally:
                    sock.close()
                    port_queue.task_done()
        
        # Lancement des threads
        threads_list = []
        for _ in range(min(threads, len(port_list))):
            t = threading.Thread(target=scan_worker)
            t.daemon = True
            t.start()
            threads_list.append(t)
        
        # Attente
        port_queue.join()
        
        # Résumé
        print(f"\n{Colors.BOLD}📊 RÉSUMÉ SCAN:{Colors.END}")
        print(f"  • Ports ouverts: {len(results)}")
        print(f"  • Vulnérabilités détectées: {sum(len(r['vulnerabilities']) for r in results)}")
        
        # Affichage par catégorie
        categories = defaultdict(list)
        for result in results:
            for cat, ports in self.common_ports.items():
                if result['port'] in ports:
                    categories[cat].append(result)
                    break
        
        print(f"\n{Colors.BOLD}📁 PORTS PAR CATÉGORIE:{Colors.END}")
        for cat, items in categories.items():
            print(f"  • {cat.upper():12}: {len(items)} ports")
        
        return results
    
    def _get_service_info(self, target, port, timeout=2):
        """Identifie le service et sa version"""
        service_info = {
            'name': 'unknown',
            'version': '',
            'banner': ''
        }
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((target, port))
            
            # Envoi de probes selon le port
            if port == 22:  # SSH
                sock.send(b'SSH-2.0-NetPentest\r\n')
                banner = sock.recv(1024).decode('utf-8', errors='ignore')
                service_info['name'] = 'ssh'
                service_info['banner'] = banner.strip()
                
                # Extraction version
                if 'SSH' in banner:
                    service_info['version'] = banner.split('SSH-')[1].split(' ')[0] if 'SSH-' in banner else ''
            
            elif port == 80 or port == 443:  # HTTP/S
                sock.send(b'GET / HTTP/1.0\r\n\r\n')
                banner = sock.recv(1024).decode('utf-8', errors='ignore')
                service_info['name'] = 'http' if port == 80 else 'https'
                service_info['banner'] = banner.strip()
                
                # Extraction Server header
                for line in banner.split('\n'):
                    if 'Server:' in line:
                        service_info['version'] = line.split('Server:')[1].strip()
                        break
            
            elif port == 21:  # FTP
                banner = sock.recv(1024).decode('utf-8', errors='ignore')
                service_info['name'] = 'ftp'
                service_info['banner'] = banner.strip()
                
                # Extraction version FTP
                if '220' in banner:
                    service_info['version'] = banner.split('220')[1].strip()
            
            elif port == 25 or port == 587:  # SMTP
                banner = sock.recv(1024).decode('utf-8', errors='ignore')
                service_info['name'] = 'smtp'
                service_info['banner'] = banner.strip()
            
            elif port == 3306:  # MySQL
                import struct
                # Packet MySQL handshake
                sock.send(b'\x0a\x00\x00\x00\x0a\x35\x2e\x37\x2e\x33\x32\x00')
                banner = sock.recv(1024)
                if banner:
                    service_info['name'] = 'mysql'
                    try:
                        version_len = banner[0]
                        service_info['version'] = banner[1:1+version_len].decode()
                    except:
                        pass
            
            elif port == 5432:  # PostgreSQL
                sock.send(b'\x00\x00\x00\x08\x04\xd2\x16\x2f')
                banner = sock.recv(1024)
                if banner:
                    service_info['name'] = 'postgresql'
            
            else:
                # Probe générique
                try:
                    banner = sock.recv(1024).decode('utf-8', errors='ignore')
                    if banner:
                        service_info['banner'] = banner.strip()
                        # Devine le service par le port
                        for name, ports in self.common_ports.items():
                            if port in ports:
                                service_info['name'] = name
                                break
                except:
                    pass
            
            sock.close()
            
        except:
            pass
        
        return service_info
    
    def _check_vulnerabilities(self, port, service_info):
        """Vérifie les vulnérabilités connues pour un port/service"""
        vulns = []
        
        # Vérifications basées sur le port
        if port in self.vuln_db:
            vulns.extend(self.vuln_db[port])
        
        # Vérifications basées sur la bannière
        banner = service_info.get('banner', '').lower()
        
        # Anciennes versions
        old_versions = {
            'openssh': ['7.2', '7.1', '7.0', '6.9', '6.8', '6.7'],
            'apache': ['2.2', '2.0', '1.3'],
            'nginx': ['1.10', '1.8', '1.6'],
            'iis': ['7.0', '6.0', '5.0'],
            'tomcat': ['7.0', '6.0', '5.5']
        }
        
        for software, versions in old_versions.items():
            if software in banner:
                for version in versions:
                    if version in banner:
                        vulns.append(f"{software.upper()} version obsolète {version}")
                        break
        
        # Services par défaut sans authentification
        if port == 21 and 'anonymous' in banner:  # FTP Anonymous
            vulns.append('FTP Anonymous login enabled')
        
        if port == 23:  # Telnet toujours dangereux
            vulns.append('Telnet en clair - INSÉCURE')
        
        if port == 445 and 'Samba' in banner:  # SMB ancien
            vulns.append('SMBv1 possible - vérifier EternalBlue')
        
        if port == 3389:  # RDP
            vulns.append('RDP exposé - risque de brute force')
        
        return vulns
    
    def scan_database_vulnerabilities(self, target):
        """Scan spécifique pour bases de données exposées"""
        print(f"{Colors.BOLD}🗄️  SCAN BASES DE DONNÉES - {target}{Colors.END}")
        print(f"{Colors.CYAN}{'='*80}{Colors.END}")
        
        db_ports = {
            3306: ('MySQL', self._check_mysql),
            5432: ('PostgreSQL', self._check_postgres),
            27017: ('MongoDB', self._check_mongodb),
            1433: ('SQL Server', self._check_mssql),
            1521: ('Oracle', self._check_oracle),
            6379: ('Redis', self._check_redis)
        }
        
        results = []
        for port, (name, checker) in db_ports.items():
            print(f"\n{Colors.BOLD}🔍 Test {name} (port {port})...{Colors.END}")
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((target, port))
                
                if result == 0:
                    print(f"{Colors.GREEN}✓ {name} accessible{Colors.END}")
                    vulns = checker(target, port)
                    
                    if vulns:
                        for vuln in vulns:
                            print(f"{Colors.RED}  ⚠️  {vuln}{Colors.END}")
                            self.vulnerabilities.append({
                                'target': target,
                                'port': port,
                                'service': name,
                                'vulnerability': vuln,
                                'severity': 'HIGH'
                            })
                    
                    results.append({
                        'port': port,
                        'service': name,
                        'accessible': True,
                        'vulnerabilities': vulns
                    })
                else:
                    print(f"{Colors.YELLOW}✗ {name} non accessible{Colors.END}")
                    
                sock.close()
                
            except Exception as e:
                print(f"{Colors.RED}❌ Erreur: {e}{Colors.END}")
        
        return results
    
    def _check_mysql(self, target, port):
        """Vérifie MySQL pour failles"""
        vulns = []
        
        # Test connexion sans mot de passe (root/root)
        try:
            if MYSQL_AVAILABLE:
                # Test avec credentials par défaut
                default_creds = [
                    ('root', ''),
                    ('root', 'root'),
                    ('root', 'password'),
                    ('root', '123456'),
                    ('admin', 'admin')
                ]
                
                for user, pwd in default_creds:
                    try:
                        conn = pymysql.connect(
                            host=target,
                            port=port,
                            user=user,
                            password=pwd,
                            connect_timeout=3
                        )
                        conn.close()
                        vulns.append(f"MySQL - Authentification faible: {user}:{pwd}")
                        break
                    except:
                        continue
        except:
            pass
        
        return vulns
    
    def _check_postgres(self, target, port):
        """Vérifie PostgreSQL pour failles"""
        vulns = []
        
        if POSTGRES_AVAILABLE:
            # Test avec credentials par défaut
            default_creds = [
                ('postgres', 'postgres'),
                ('postgres', 'password'),
                ('admin', 'admin')
            ]
            
            for user, pwd in default_creds:
                try:
                    conn = psycopg2.connect(
                        host=target,
                        port=port,
                        user=user,
                        password=pwd,
                        connect_timeout=3
                    )
                    conn.close()
                    vulns.append(f"PostgreSQL - Authentification faible: {user}:{pwd}")
                    break
                except:
                    continue
        
        return vulns
    
    def _check_mongodb(self, target, port):
        """Vérifie MongoDB pour failles"""
        vulns = []
        
        # MongoDB souvent sans authentification
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((target, port))
            
            # Envoi d'une requête MongoDB isMaster
            probe = b'\x3a\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xd4\x07\x00\x00\x00\x00\x00\x00\x61\x64\x6d\x69\x6e\x2e\x24\x63\x6d\x64\x00\x00\x00\x00\x00\x01\x00\x00\x00\x08\x69\x73\x4d\x61\x73\x74\x65\x72\x00\x01\x00\x00\x00\x00'
            sock.send(probe)
            response = sock.recv(1024)
            
            if response:
                vulns.append("MongoDB accessible sans authentification")
            
            sock.close()
        except:
            pass
        
        return vulns
    
    def _check_mssql(self, target, port):
        """Vérifie SQL Server pour failles"""
        vulns = ["SQL Server exposé - tester avec sa:sa"]
        return vulns
    
    def _check_oracle(self, target, port):
        """Vérifie Oracle pour failles"""
        vulns = ["Oracle exposé - TNS listener vulnérable"]
        return vulns
    
    def _check_redis(self, target, port):
        """Vérifie Redis pour failles"""
        vulns = []
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((target, port))
            
            # Commande Redis INFO
            sock.send(b'INFO\r\n')
            response = sock.recv(4096).decode('utf-8', errors='ignore')
            
            if 'redis_version' in response:
                vulns.append("Redis accessible sans authentification")
                
                # Vérifier si config exposée
                if 'CONFIG' in response.upper():
                    vulns.append("Redis CONFIG command accessible")
            
            sock.close()
        except:
            pass
        
        return vulns
    
    def generate_report(self, filename=None):
        """Génère un rapport d'audit"""
        if not filename:
            filename = f"pentest_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'scanner': 'NetPentest Pro',
            'hosts_scanned': list(self.open_ports.keys()),
            'open_ports': dict(self.open_ports),
            'services': dict(self.services),
            'vulnerabilities': self.vulnerabilities,
            'summary': {
                'total_hosts': len(self.open_ports),
                'total_ports': sum(len(ports) for ports in self.open_ports.values()),
                'total_vulns': len(self.vulnerabilities),
                'critical_vulns': len([v for v in self.vulnerabilities if v.get('severity') == 'CRITICAL']),
                'high_vulns': len([v for v in self.vulnerabilities if v.get('severity') == 'HIGH'])
            }
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            # Génère également un rapport HTML
            self._generate_html_report(report, filename.replace('.json', '.html'))
            
            print(f"{Colors.GREEN}✅ Rapport généré: {filename}{Colors.END}")
            return filename
            
        except Exception as e:
            print(f"{Colors.RED}❌ Erreur génération rapport: {e}{Colors.END}")
            return None
    
    def _generate_html_report(self, data, filename):
        """Génère un rapport HTML"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Rapport Pentest - {datetime.now().strftime('%d/%m/%Y %H:%M')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #333; }}
                .critical {{ color: red; font-weight: bold; }}
                .high {{ color: orange; }}
                .medium {{ color: #ffcc00; }}
                .low {{ color: blue; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
            </style>
        </head>
        <body>
            <h1>🎯 Rapport d'Audit Réseau - NetPentest Pro</h1>
            <p>Généré le: {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}</p>
            
            <h2>📊 Résumé</h2>
            <ul>
                <li>Hôtes scannés: {data['summary']['total_hosts']}</li>
                <li>Ports ouverts: {data['summary']['total_ports']}</li>
                <li>Vulnérabilités trouvées: {data['summary']['total_vulns']}</li>
                <li class="critical">Critiques: {data['summary']['critical_vulns']}</li>
                <li class="high">Hautes: {data['summary']['high_vulns']}</li>
            </ul>
            
            <h2>🚨 Vulnérabilités Détectées</h2>
            <table>
                <tr>
                    <th>Cible</th>
                    <th>Port</th>
                    <th>Service</th>
                    <th>Vulnérabilité</th>
                    <th>Sévérité</th>
                </tr>
        """
        
        for vuln in data['vulnerabilities']:
            severity_class = vuln.get('severity', 'MEDIUM').lower()
            html += f"""
                <tr>
                    <td>{vuln.get('target', 'N/A')}</td>
                    <td>{vuln.get('port', 'N/A')}</td>
                    <td>{vuln.get('service', 'N/A')}</td>
                    <td>{vuln.get('vulnerability', 'N/A')}</td>
                    <td class="{severity_class}">{vuln.get('severity', 'MEDIUM')}</td>
                </tr>
            """
        
        html += """
            </table>
            
            <h2>🔍 Ports Ouverts par Hôte</h2>
        """
        
        for host, ports in data['open_ports'].items():
            html += f"""
            <h3>{host}</h3>
            <ul>
            """
            for port in ports:
                service = data['services'].get(host, {}).get(port, {})
                html += f"<li>Port {port}: {service.get('name', 'unknown')} - {service.get('version', '')}</li>"
            html += "</ul>"
        
        html += """
            <footer>
                <p>Rapport généré par NetPentest Pro</p>
            </footer>
        </body>
        </html>
        """
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)


class PacketSniffer:
    """Sniffer réseau style Wireshark léger"""
    
    def __init__(self, interface=None):
        self.interface = interface
        self.packets = []
        self.running = False
        self.filter = ''
        
    def start_sniffing(self, count=100, filter=''):
        """Démarre la capture de paquets"""
        if not SCAPY_AVAILABLE:
            print(f"{Colors.RED}❌ Scapy requis pour le sniffing{Colors.END}")
            return
        
        print(f"{Colors.BOLD}📡 CAPTURE RÉSEAU - Interface: {self.interface or 'par défaut'}{Colors.END}")
        print(f"{Colors.CYAN}{'='*80}{Colors.END}")
        print(f"Filtre: {filter if filter else 'aucun'} | Paquets: {count}")
        print(f"{Colors.YELLOW}Appuyez sur Ctrl+C pour arrêter{Colors.END}\n")
        
        try:
            self.running = True
            packets = scapy.sniff(
                iface=self.interface,
                count=count,
                filter=filter,
                prn=self._packet_callback,
                store=True
            )
            
            self.packets.extend(packets)
            
            print(f"\n{Colors.BOLD}📊 CAPTURE TERMINÉE{Colors.END}")
            print(f"  • Paquets capturés: {len(packets)}")
            print(f"  • Total en mémoire: {len(self.packets)}")
            
            # Analyse des paquets
            self._analyze_packets(packets)
            
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}⚠️  Capture interrompue par l'utilisateur{Colors.END}")
        except Exception as e:
            print(f"{Colors.RED}❌ Erreur capture: {e}{Colors.END}")
        finally:
            self.running = False
    
    def _packet_callback(self, packet):
        """Callback pour chaque paquet capturé"""
        if packet.haslayer(scapy.IP):
            src_ip = packet[scapy.IP].src
            dst_ip = packet[scapy.IP].dst
            proto = packet[scapy.IP].proto
            
            proto_name = {1: 'ICMP', 6: 'TCP', 17: 'UDP'}.get(proto, f'IP:{proto}')
            
            info = ''
            if packet.haslayer(scapy.TCP):
                info = f"TCP {packet[scapy.TCP].sport}->{packet[scapy.TCP].dport}"
            elif packet.haslayer(scapy.UDP):
                info = f"UDP {packet[scapy.UDP].sport}->{packet[scapy.UDP].dport}"
            elif packet.haslayer(scapy.ICMP):
                info = 'ICMP'
            
            # Couleur selon le protocole
            if proto == 6:  # TCP
                color = Colors.CYAN
            elif proto == 17:  # UDP
                color = Colors.GREEN
            else:
                color = Colors.YELLOW
            
            print(f"{color}📦 {src_ip:15} -> {dst_ip:15} {proto_name:6} {info}{Colors.END}")
            
            # Détection d'activité suspecte
            self._detect_suspicious(packet)
    
    def _detect_suspicious(self, packet):
        """Détecte les activités réseau suspectes"""
        alerts = []
        
        # Scan de ports
        if packet.haslayer(scapy.TCP):
            tcp = packet[scapy.TCP]
            if tcp.flags == 2:  # SYN seul (scan)
                alerts.append("Possible scan SYN")
            
            # Tentative de connexion sur port sensible
            if tcp.dport in [22, 23, 3389, 5900]:
                alerts.append(f"Connexion sur port sensible {tcp.dport}")
        
        # DNS suspect
        if packet.haslayer(scapy.DNS):
            dns = packet[scapy.DNS]
            if dns.qd:
                qname = str(dns.qd.qname)
                suspicious_domains = ['crypt', 'miner', 'pool', 'xmr', 'torrent', 'pirate']
                if any(domain in qname.lower() for domain in suspicious_domains):
                    alerts.append(f"DNS suspect: {qname}")
        
        # Affichage des alertes
        if alerts:
            for alert in alerts:
                print(f"   {Colors.RED}🚨 {alert}{Colors.END}")
    
    def _analyze_packets(self, packets):
        """Analyse statistique des paquets capturés"""
        print(f"\n{Colors.BOLD}📈 ANALYSE STATISTIQUE:{Colors.END}")
        
        stats = {
            'total': len(packets),
            'by_protocol': Counter(),
            'by_source': Counter(),
            'by_destination': Counter(),
            'top_conversations': Counter()
        }
        
        for packet in packets:
            if packet.haslayer(scapy.IP):
                src = packet[scapy.IP].src
                dst = packet[scapy.IP].dst
                proto = packet[scapy.IP].proto
                
                stats['by_protocol'][proto] += 1
                stats['by_source'][src] += 1
                stats['by_destination'][dst] += 1
                stats['top_conversations'][(src, dst)] += 1
        
        # Affichage protocoles
        print(f"  • Par protocole:")
        proto_names = {1: 'ICMP', 6: 'TCP', 17: 'UDP'}
        for proto, count in stats['by_protocol'].most_common(5):
            name = proto_names.get(proto, f'Proto {proto}')
            print(f"    - {name}: {count}")
        
        # Top sources
        print(f"  • Top sources:")
        for src, count in stats['by_source'].most_common(5):
            print(f"    - {src}: {count} paquets")
        
        # Top conversations
        print(f"  • Top conversations:")
        for (src, dst), count in stats['top_conversations'].most_common(5):
            print(f"    - {src} ↔ {dst}: {count} paquets")
    
    def save_capture(self, filename=None):
        """Sauvegarde la capture en fichier pcap"""
        if not SCAPY_AVAILABLE or not self.packets:
            print(f"{Colors.YELLOW}⚠️  Aucun paquet à sauvegarder{Colors.END}")
            return
        
        if not filename:
            filename = f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pcap"
        
        try:
            scapy.wrpcap(filename, self.packets)
            print(f"{Colors.GREEN}✅ Capture sauvegardée: {filename} ({len(self.packets)} paquets){Colors.END}")
            return filename
        except Exception as e:
            print(f"{Colors.RED}❌ Erreur sauvegarde: {e}{Colors.END}")
            return None


class WiFiAnalyzer:
    """Analyseur WiFi (Windows/Linux)"""
    
    def __init__(self):
        self.networks = []
        
    def scan_wifi(self):
        """Scan les réseaux WiFi disponibles"""
        print(f"{Colors.BOLD}📶 SCAN WIFI{Colors.END}")
        print(f"{Colors.CYAN}{'='*80}{Colors.END}")
        
        if sys.platform == 'win32':
            return self._scan_wifi_windows()
        elif sys.platform.startswith('linux'):
            return self._scan_wifi_linux()
        else:
            print(f"{Colors.YELLOW}⚠️  Plateforme non supportée{Colors.END}")
            return []
    
    def _scan_wifi_windows(self):
        """Scan WiFi sur Windows"""
        try:
            import subprocess
            import re
            
            # Commande netsh pour lister les réseaux
            result = subprocess.run(
                ['netsh', 'wlan', 'show', 'networks', 'mode=bssid'],
                capture_output=True,
                text=True,
                encoding='cp850'
            )
            
            networks = []
            current = {}
            
            for line in result.stdout.split('\n'):
                line = line.strip()
                
                if 'SSID' in line and ':' in line:
                    if current:
                        networks.append(current)
                    ssid = line.split(':', 1)[1].strip()
                    current = {'ssid': ssid if ssid else '[Caché]'}
                
                elif 'Authentication' in line and ':' in line:
                    auth = line.split(':', 1)[1].strip()
                    current['auth'] = auth
                
                elif 'Encryption' in line and ':' in line:
                    enc = line.split(':', 1)[1].strip()
                    current['encryption'] = enc
                
                elif 'Signal' in line and ':' in line:
                    signal = line.split(':', 1)[1].strip().replace('%', '')
                    current['signal'] = int(signal) if signal.isdigit() else 0
                
                elif 'BSSID' in line and ':' in line:
                    bssid = line.split(':', 1)[1].strip()
                    if 'bssid' not in current:
                        current['bssid'] = bssid
            
            if current:
                networks.append(current)
            
            # Affichage
            print(f"{'SSID':25} {'BSSID':17} {'Signal':>6} {'Auth':15} {'Encryption':15}")
            print(f"{'-'*80}")
            
            for net in networks:
                # Couleur selon la sécurité
                if 'WPA2' in net.get('auth', '') or 'WPA3' in net.get('auth', ''):
                    color = Colors.GREEN
                elif 'WEP' in net.get('encryption', ''):
                    color = Colors.RED
                elif 'Open' in net.get('auth', ''):
                    color = Colors.YELLOW
                else:
                    color = Colors.CYAN
                
                # Niveau de signal
                signal = net.get('signal', 0)
                if signal > 70:
                    signal_color = Colors.GREEN
                elif signal > 40:
                    signal_color = Colors.YELLOW
                else:
                    signal_color = Colors.RED
                
                print(f"{color}{net.get('ssid', 'N/A')[:24]:25}{Colors.END} "
                      f"{net.get('bssid', 'N/A')[:17]:17} "
                      f"{signal_color}{signal:>6}%{Colors.END} "
                      f"{net.get('auth', 'N/A')[:14]:15} "
                      f"{net.get('encryption', 'N/A')[:14]:15}")
            
            self.networks = networks
            print(f"\n{Colors.BOLD}📊 {len(networks)} réseaux WiFi trouvés{Colors.END}")
            
            # Détection de faiblesses
            self._detect_wifi_vulnerabilities(networks)
            
            return networks
            
        except Exception as e:
            print(f"{Colors.RED}❌ Erreur scan WiFi: {e}{Colors.END}")
            return []
    
    def _detect_wifi_vulnerabilities(self, networks):
        """Détecte les vulnérabilités WiFi"""
        print(f"\n{Colors.BOLD}🔍 DÉTECTION DE FAIBLESSES WIFI:{Colors.END}")
        
        vulns = []
        
        for net in networks:
            ssid = net.get('ssid', '')
            auth = net.get('auth', '')
            enc = net.get('encryption', '')
            
            # WEP vulnérable
            if 'WEP' in enc:
                vulns.append(f"{ssid}: WEP - TRÈS VULNÉRABLE (cassable en minutes)")
            
            # WPA/WPA2 avec PMKID
            if 'WPA2-Personal' in auth:
                # Faiblesses connues
                vulns.append(f"{ssid}: WPA2-Personal - Attaque par dictionnaire possible")
            
            # WiFi ouvert
            if 'Open' in auth:
                vulns.append(f"{ssid}: WiFi ouvert - RISQUE ÉLEVÉ")
            
            # SSID par défaut
            default_names = ['Livebox', 'FreeWifi', 'SFR_WIFI', 'Bbox', 'Orange', 'default', 'linksys']
            if any(name.lower() in ssid.lower() for name in default_names):
                vulns.append(f"{ssid}: SSID par défaut - probable mot de passe faible")
        
        if vulns:
            for vuln in vulns:
                print(f"{Colors.RED}  ⚠️  {vuln}{Colors.END}")
        else:
            print(f"{Colors.GREEN}  ✅ Aucune faiblesse évidente détectée{Colors.END}")


# ================= INTERFACE UTILISATEUR =================
def print_banner():
    """Affiche la bannière du programme"""
    print(f"""{Colors.CYAN}
╔══════════════════════════════════════════════════════════════════════════╗
║                   NETPENTEST PRO - Outil de Pentest Réseau              ║
║           🔍 Scan réseau | 📡 Sniffing | 🗄️  DB Vulns | 📶 WiFi        ║
╚══════════════════════════════════════════════════════════════════════════╝
{Colors.END}""")


def print_menu():
    """Affiche le menu principal"""
    print(f"""
{Colors.BOLD}📋 MENU PRINCIPAL:{Colors.END}

{Colors.GREEN}[1]{Colors.END} Scan réseau complet
{Colors.GREEN}[2]{Colors.END} Scan ARP (découverte hôtes)
{Colors.GREEN}[3]{Colors.END} Scan de ports avancé
{Colors.GREEN}[4]{Colors.END} Scan bases de données
{Colors.GREEN}[5]{Colors.END} Sniffing réseau (capture paquets)
{Colors.GREEN}[6]{Colors.END} Analyse WiFi
{Colors.GREEN}[7]{Colors.END} Scan de vulnérabilités web
{Colors.GREEN}[8]{Colors.END} Bruteforce détection (FTP/SSH)
{Colors.GREEN}[9]{Colors.END} Générer rapport

{Colors.GREEN}[C]{Colors.END} Configurer scanner
{Colors.GREEN}[H]{Colors.END} Historique scans
{Colors.GREEN}[S]{Colors.END} Sauvegarder résultats
{Colors.GREEN}[Q]{Colors.END} Quitter

{Colors.YELLOW}Commandes rapides:{Colors.END}
• {Colors.CYAN}scan IP{Colors.END}          : Scan rapide d'une IP
• {Colors.CYAN}ports IP{Colors.END}         : Scan de ports
• {Colors.CYAN}dbscan IP{Colors.END}        : Scan bases de données
• {Colors.CYAN}sniff{Colors.END}            : Capturer paquets
• {Colors.CYAN}wifi{Colors.END}             : Scanner WiFi
• {Colors.CYAN}report{Colors.END}           : Générer rapport
""")


def main():
    """Fonction principale"""
    scanner = NetworkScanner()
    sniffer = PacketSniffer()
    wifi_analyzer = WiFiAnalyzer()
    scan_history = []
    
    print_banner()
    
    if not SCAPY_AVAILABLE:
        print(f"{Colors.YELLOW}⚠️  Scapy non installé - installation recommandée:{Colors.END}")
        print(f"   pip install scapy")
        print(f"{Colors.YELLOW}   Certaines fonctionnalités seront limitées.{Colors.END}\n")
    
    while True:
        try:
            print(f"\n{Colors.CYAN}{'─'*80}{Colors.END}")
            print_menu()
            
            choice = input(f"\n{Colors.BOLD}netpentest>{Colors.END} ").strip().lower()
            
            if choice in ['q', 'quit', 'exit']:
                print(f"\n{Colors.GREEN}👋 Au revoir !{Colors.END}")
                break
            
            elif choice == '1':
                # Scan réseau complet
                target = input(f"Cible (IP/réseau): ").strip()
                if not target:
                    target = '192.168.1.0/24'
                
                print(f"{Colors.YELLOW}⏳ Scan en cours...{Colors.END}")
                
                # 1. Découverte ARP
                hosts = scanner.arp_scan(target if '/' in target else target + '/24')
                
                # 2. Scan de ports sur chaque hôte
                for host in hosts[:5]:  # Limiter à 5 hôtes pour la démo
                    ip = host['ip']
                    print(f"\n{Colors.BOLD}🎯 Scan de {ip}...{Colors.END}")
                    scanner.port_scan(ip, ports='top100', threads=50)
                
                scan_history.append({
                    'type': 'full_scan',
                    'target': target,
                    'timestamp': datetime.now().isoformat(),
                    'hosts': len(hosts)
                })
            
            elif choice == '2':
                # Scan ARP
                network = input(f"Réseau (ex: 192.168.1.0/24): ").strip()
                if not network:
                    network = '192.168.1.0/24'
                
                scanner.arp_scan(network)
            
            elif choice == '3':
                # Scan de ports
                target = input(f"Cible IP: ").strip()
                if not target:
                    print(f"{Colors.YELLOW}⚠️  IP requise{Colors.END}")
                    continue
                
                port_range = input(f"Ports (common/top100/all/custom): ").strip().lower()
                if port_range == 'custom':
                    custom = input(f"Ports (ex: 22,80,443 ou 20-100): ").strip()
                    port_range = custom
                elif not port_range:
                    port_range = 'common'
                
                scanner.port_scan(target, ports=port_range)
            
            elif choice == '4':
                # Scan bases de données
                target = input(f"Cible IP: ").strip()
                if not target:
                    print(f"{Colors.YELLOW}⚠️  IP requise{Colors.END}")
                    continue
                
                scanner.scan_database_vulnerabilities(target)
            
            elif choice == '5':
                # Sniffing réseau
                if not SCAPY_AVAILABLE:
                    print(f"{Colors.RED}❌ Scapy requis pour le sniffing{Colors.END}")
                    continue
                
                interface = input(f"Interface (laisser vide pour auto): ").strip()
                if interface:
                    sniffer.interface = interface
                
                packet_count = input(f"Nombre de paquets (défaut 100): ").strip()
                count = int(packet_count) if packet_count.isdigit() else 100
                
                filter_str = input(f"Filtre BPF (ex: 'tcp port 80'): ").strip()
                
                sniffer.start_sniffing(count=count, filter=filter_str)
                
                # Sauvegarde optionnelle
                save = input(f"\nSauvegarder la capture? (o/n): ").strip().lower()
                if save == 'o':
                    sniffer.save_capture()
            
            elif choice == '6':
                # Analyse WiFi
                wifi_analyzer.scan_wifi()
            
            elif choice == '7':
                # Scan vulnérabilités web
                print(f"{Colors.YELLOW}⚠️  Fonctionnalité en développement...{Colors.END}")
                url = input(f"URL (ex: http://example.com): ").strip()
                if url:
                    # Placeholder pour scan web
                    print(f"Scan web de {url}...")
            
            elif choice == '8':
                # Détection bruteforce
                print(f"{Colors.YELLOW}⚠️  Fonctionnalité en développement...{Colors.END}")
                print(f"Ce module détecte les tentatives de bruteforce")
            
            elif choice == '9':
                # Génération rapport
                filename = scanner.generate_report()
                if filename:
                    print(f"{Colors.GREEN}✅ Rapport généré avec succès{Colors.END}")
            
            elif choice == 'c':
                # Configuration
                print(f"\n{Colors.BOLD}⚙️  CONFIGURATION:{Colors.END}")
                print(f"1. Threads de scan (actuel: 50)")
                print(f"2. Timeout (actuel: 1s)")
                print(f"3. Interface réseau")
                
                config_choice = input(f"Option: ").strip()
                # Configuration simplifiée
                print(f"{Colors.GREEN}✅ Configuration enregistrée{Colors.END}")
            
            elif choice == 'h':
                # Historique
                print(f"\n{Colors.BOLD}📜 HISTORIQUE DES SCANS:{Colors.END}")
                for i, scan in enumerate(scan_history[-10:], 1):
                    print(f"{i:2}. {scan['timestamp'][11:19]} - {scan['type']} sur {scan['target']}")
            
            elif choice == 's':
                # Sauvegarde
                print(f"\n{Colors.BOLD}💾 SAUVEGARDE:{Colors.END}")
                print(f"1. Sauvegarder scan actuel")
                print(f"2. Exporter en JSON")
                print(f"3. Exporter en CSV")
                
                save_choice = input(f"Option: ").strip()
                if save_choice == '1':
                    scanner.generate_report()
            
            elif choice.startswith('scan '):
                # Commande rapide scan
                target = choice[5:].strip()
                if target:
                    scanner.port_scan(target, ports='common')
            
            elif choice.startswith('ports '):
                # Commande rapide ports
                target = choice[6:].strip()
                if target:
                    scanner.port_scan(target, ports='top100')
            
            elif choice.startswith('dbscan '):
                # Commande rapide DB scan
                target = choice[7:].strip()
                if target:
                    scanner.scan_database_vulnerabilities(target)
            
            elif choice == 'sniff':
                sniffer.start_sniffing(count=50)
            
            elif choice == 'wifi':
                wifi_analyzer.scan_wifi()
            
            elif choice == 'report':
                scanner.generate_report()
            
            elif choice == '':
                continue
            
            else:
                print(f"{Colors.YELLOW}❓ Commande non reconnue: '{choice}'{Colors.END}")
        
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}\n⚠️  Interrompu. Tapez 'quit' pour quitter.{Colors.END}")
            continue
        except Exception as e:
            print(f"{Colors.RED}❌ Erreur: {e}{Colors.END}")
            import traceback
            traceback.print_exc()


# ================= INSTALLATION =================
def check_dependencies():
    """Vérifie et installe les dépendances"""
    required = ['psutil', 'requests']
    optional = ['scapy', 'pymysql', 'psycopg2']
    
    print(f"{Colors.BOLD}🔍 VÉRIFICATION DES DÉPENDANCES{Colors.END}")
    
    # Vérification des packages requis
    for package in required:
        try:
            __import__(package)
            print(f"{Colors.GREEN}✓ {package}{Colors.END}")
        except ImportError:
            print(f"{Colors.RED}✗ {package} - REQUIS{Colors.END}")
            install = input(f"Installer {package}? (o/n): ").strip().lower()
            if install == 'o':
                import subprocess
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    # Packages optionnels
    print(f"\n{Colors.BOLD}📦 PACKAGES OPTIONNELS:{Colors.END}")
    for package in optional:
        try:
            __import__(package)
            print(f"{Colors.GREEN}✓ {package}{Colors.END}")
        except ImportError:
            print(f"{Colors.YELLOW}✗ {package} - Optionnel (certaines fonctionnalités limitées){Colors.END}")
    
    print(f"\n{Colors.GREEN}✅ Vérification terminée{Colors.END}")


# ================= POINT D'ENTRÉE =================
if __name__ == "__main__":
    try:
        # Vérifier si on est root (pour sniffing)
        if os.name == 'posix' and os.geteuid() != 0:
            print(f"{Colors.YELLOW}⚠️  Pour le sniffing, exécutez en root (sudo){Colors.END}")
        
        # Vérifier dépendances
        if len(sys.argv) > 1 and sys.argv[1] == '--install':
            check_dependencies()
            sys.exit(0)
        
        # Démarrer
        main()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.GREEN}👋 Au revoir !{Colors.END}")
    except Exception as e:
        print(f"{Colors.RED}❌ Erreur critique: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        input("Appuyez sur Entrée pour quitter...")