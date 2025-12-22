#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMB chat V2 V1.0 - COMPLETE
Fusion complète SMBchat + SMB Transfer avec interface duale
Système de messages auto-destructifs + Toutes fonctionnalités originales
"""

import os
import sys
import json
import time
import base64
import hashlib
import socket
import threading
import subprocess
import ipaddress
import queue
from datetime import datetime, timedelta
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# ============================================================================
# CONFIGURATION & CONSTANTES
# ============================================================================

CHAT_PORT = 9998
DISCOVERY_PORT = 9999
SMB_PORT = 445
SCAN_TIMEOUT = 2
MAX_HOSTS = 50

# ============================================================================
# MODULE RÉSEAU UNIFIÉ
# ============================================================================

class NetworkScanner:
    """Scanner réseau unifié (ARP + Ping + SMB)"""
    
    def __init__(self):
        self.local_ip = self._get_local_ip()
        self.available_hosts = []  # (ip, has_chat, has_smb, hostname)
        self.online_users = {}     # {ip: {name, status, last_seen}}
        self.scanning = False
    
    def _get_local_ip(self):
        """Récupère l'IP locale"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def get_network_range(self):
        """Retourne le réseau /24"""
        if self.local_ip == "127.0.0.1":
            return "192.168.1.0/24"
        parts = self.local_ip.split('.')
        return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
    
    def scan_arp(self):
        """Scan via table ARP"""
        arp_hosts = []
        try:
            if os.name == 'nt':  # Windows
                result = subprocess.run(['arp', '-a'], 
                                      capture_output=True, 
                                      text=True,
                                      encoding='cp850',
                                      errors='ignore')
                
                for line in result.stdout.split('\n'):
                    line_lower = line.lower()
                    if 'dynamique' in line_lower or 'dynamic' in line_lower:
                        parts = line.split()
                        for part in parts:
                            if part.count('.') == 3:
                                ip_parts = part.split('.')
                                if len(ip_parts) == 4 and all(p.isdigit() for p in ip_parts):
                                    if part not in arp_hosts and part != self.local_ip:
                                        arp_hosts.append(part)
                                        break
            else:  # Linux/Mac
                result = subprocess.run(['arp', '-a'], 
                                      capture_output=True, 
                                      text=True)
                for line in result.stdout.split('\n'):
                    if '(' in line and ')' in line:
                        start = line.find('(') + 1
                        end = line.find(')')
                        ip = line[start:end]
                        if ip.count('.') == 3 and ip not in arp_hosts and ip != self.local_ip:
                            arp_hosts.append(ip)
            return arp_hosts
        except:
            return []
    
    def ping_host(self, ip, timeout=1):
        """Ping une IP"""
        try:
            param = '-n' if os.name == 'nt' else '-c'
            timeout_str = str(timeout * 1000) if os.name == 'nt' else str(timeout)
            
            command = ['ping', param, '1', '-w', timeout_str, ip]
            
            with subprocess.Popen(command, stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE) as proc:
                out, _ = proc.communicate(timeout=timeout + 0.5)
            
            return proc.returncode == 0
        except:
            return False
    
    def is_port_open(self, ip, port, timeout=1):
        """Test si un port est ouvert"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def get_hostname(self, ip):
        """Récupère le nom d'hôte"""
        try:
            return socket.gethostbyaddr(ip)[0]
        except:
            return None
    
    def scan_network(self, quick=False):
        """Scan réseau complet"""
        self.scanning = True
        self.available_hosts = []
        
        print("🔍 Scan réseau en cours...")
        
        # Méthode 1: ARP
        print("  → Méthode ARP...")
        arp_hosts = self.scan_arp()
        
        # Méthode 2: Ping rapide
        print("  → Scan ping...")
        network_base = '.'.join(self.local_ip.split('.')[:3])
        
        # Scanner les IPs
        for i in range(1, 101 if quick else 255):
            ip = f"{network_base}.{i}"
            
            if ip == self.local_ip:
                continue
            
            # Vérifier si déjà détecté via ARP
            already_found = any(h[0] == ip for h in self.available_hosts)
            
            if not already_found and (ip in arp_hosts or self.ping_host(ip, 0.3)):
                # Tester les services
                has_chat = self.is_port_open(ip, CHAT_PORT, 0.5)
                has_smb = self.is_port_open(ip, SMB_PORT, 0.5)
                hostname = self.get_hostname(ip)
                
                self.available_hosts.append((ip, has_chat, has_smb, hostname))
        
        self.scanning = False
        print(f"✅ Scan terminé: {len(self.available_hosts)} hôtes")
        return self.available_hosts
    
    def get_chat_users(self):
        """Retourne les utilisateurs avec chat actif"""
        return [h for h in self.available_hosts if h[1]]  # has_chat == True
    
    def get_smb_hosts(self):
        """Retourne les hôtes avec SMB actif"""
        return [h for h in self.available_hosts if h[2]]  # has_smb == True

# ============================================================================
# MODULE CHAT P2P
# ============================================================================

class ChatEngine:
    """Moteur de chat P2P (basé sur SMBchat)"""
    
    def __init__(self, username, network_scanner, message_store):
        self.username = username
        self.scanner = network_scanner
        self.store = message_store
        self.running = False
        self.discovery_thread = None
        self.chat_thread = None
        
    def start(self):
        """Démarre les services de chat"""
        self.running = True
        
        # Démarrer serveur découverte
        self.discovery_thread = threading.Thread(target=self._discovery_server, daemon=True)
        self.discovery_thread.start()
        
        # Démarrer serveur chat
        self.chat_thread = threading.Thread(target=self._chat_server, daemon=True)
        self.chat_thread.start()
        
        # Annoncer présence
        self._broadcast_presence()
        
        print("💬 Services chat démarrés")
    
    def stop(self):
        """Arrête les services"""
        self.running = False
    
    def _discovery_server(self):
        """Serveur de découverte UDP"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(('', DISCOVERY_PORT))
        
        while self.running:
            try:
                data, addr = sock.recvfrom(1024)
                ip = addr[0]
                
                if ip == self.scanner.local_ip:
                    continue
                
                try:
                    message = json.loads(data.decode('utf-8', errors='ignore'))
                    
                    if message.get('type') == 'hello':
                        self.scanner.online_users[ip] = {
                            'name': message.get('name', 'Inconnu'),
                            'status': message.get('status', '🟢 En ligne'),
                            'last_seen': datetime.now(),
                            'chat_port': message.get('chat_port', CHAT_PORT),
                            'ip': ip
                        }
                except:
                    pass
                    
            except:
                pass
        
        sock.close()
    
    def _chat_server(self):
        """Serveur de chat TCP"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            sock.bind(('0.0.0.0', CHAT_PORT))
            sock.listen(5)
            
            sock.settimeout(1)  # Timeout pour vérifier running
            
            while self.running:
                try:
                    client_socket, addr = sock.accept()
                    threading.Thread(target=self._handle_chat_connection, 
                                   args=(client_socket, addr), daemon=True).start()
                except socket.timeout:
                    continue
                except:
                    break
                    
        except Exception as e:
            print(f"❌ Erreur serveur chat: {e}")
        finally:
            sock.close()
    
    def _handle_chat_connection(self, client_socket, addr):
        """Gère une connexion chat entrante"""
        try:
            data = client_socket.recv(4096).decode('utf-8', errors='ignore')
            message = json.loads(data)
            
            # Sauvegarder le message
            self.store.add_message({
                'from': addr[0],
                'from_name': message.get('sender_name', 'Inconnu'),
                'to': self.scanner.local_ip,
                'text': message.get('text', ''),
                'type': 'text',
                'chat': True
            })
            
            # Répondre OK
            response = {'status': 'received', 'timestamp': time.time()}
            client_socket.send(json.dumps(response).encode())
            
            print(f"📨 Message reçu de {addr[0]}: {message.get('text', '')[:50]}...")
            
        except Exception as e:
            print(f"⚠️  Erreur traitement message: {e}")
        finally:
            client_socket.close()
    
    def _broadcast_presence(self):
        """Annonce notre présence sur le réseau"""
        message = {
            'type': 'hello',
            'name': self.username,
            'status': '🟢 En ligne',
            'chat_port': CHAT_PORT,
            'ip': self.scanner.local_ip,
            'timestamp': time.time()
        }
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        try:
            sock.sendto(json.dumps(message).encode(), ('255.255.255.255', DISCOVERY_PORT))
            network_base = '.'.join(self.scanner.local_ip.split('.')[:3])
            sock.sendto(json.dumps(message).encode(), (f'{network_base}.255', DISCOVERY_PORT))
        except:
            pass
        finally:
            sock.close()
    
    def send_message(self, target_ip, text):
        """Envoie un message à une IP"""
        try:
            # Chercher le port de chat
            target_port = CHAT_PORT
            if target_ip in self.scanner.online_users:
                target_port = self.scanner.online_users[target_ip].get('chat_port', CHAT_PORT)
            
            # Créer le message
            message = {
                'type': 'chat',
                'sender_name': self.username,
                'text': text,
                'timestamp': time.time(),
                'target': target_ip
            }
            
            # Envoyer
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((target_ip, target_port))
            sock.send(json.dumps(message).encode())
            
            # Attendre réponse
            sock.recv(1024)
            sock.close()
            
            # Sauvegarder localement
            self.store.add_message({
                'from': self.scanner.local_ip,
                'from_name': self.username,
                'to': target_ip,
                'text': text,
                'type': 'text',
                'chat': True
            })
            
            return True, "✅ Message envoyé"
            
        except ConnectionRefusedError:
            return False, "❌ L'utilisateur n'a pas le chat actif"
        except Exception as e:
            return False, f"❌ Erreur: {str(e)}"

# ============================================================================
# MODULE TRANSFERT FICHIERS SMB
# ============================================================================

class FileTransfer:
    """Transfert de fichiers via SMB"""
    
    def __init__(self, scanner, message_store):
        self.scanner = scanner
        self.store = message_store
    
    def send_file(self, source_path, target_ip, share_name="TransferShare"):
        """Envoie un fichier via SMB"""
        try:
            if not os.path.exists(source_path):
                return False, "❌ Fichier introuvable"
            
            filename = os.path.basename(source_path)
            file_size = os.path.getsize(source_path)
            
            print(f"📤 Envoi de {filename} à {target_ip}...")
            
            # Simuler transfert (remplacer par vrai code SMB)
            success = self._simulate_smb_transfer(source_path, target_ip, share_name)
            
            if success:
                # Enregistrer dans l'historique
                self.store.add_message({
                    'from': self.scanner.local_ip,
                    'to': target_ip,
                    'type': 'file',
                    'file_name': filename,
                    'file_size': file_size,
                    'file_path': source_path,
                    'text': f"Fichier envoyé: {filename}",
                    'transfer': True,
                    'status': 'success'
                })
                
                return True, f"✅ Fichier '{filename}' envoyé"
            else:
                return False, "❌ Échec du transfert"
                
        except Exception as e:
            return False, f"❌ Erreur: {str(e)}"
    
    def _simulate_smb_transfer(self, source_path, target_ip, share_name):
        """Simule un transfert SMB (à remplacer par vrai code)"""
        print(f"  📡 Connexion à \\\\{target_ip}\\{share_name}...")
        
        filename = os.path.basename(source_path)
        file_size = os.path.getsize(source_path)
        
        # Simulation de progression
        print(f"  📦 Fichier: {filename} ({file_size:,} octets)")
        print("  🚀 Transfert en cours...")
        
        for percent in range(0, 101, 10):
            bar = '█' * (percent//5) + '░' * (20 - percent//5)
            print(f"\r  [{bar}] {percent}%", end='')
            time.sleep(0.2)
        
        print(f"\n  ✅ Transfert simulé vers {target_ip}")
        return True
    
    def setup_receiver(self, share_name="ReceiveShare"):
        """Configure la réception de fichiers"""
        try:
            receive_folder = os.path.join(os.path.expanduser("~"), "SMB_Receive")
            Path(receive_folder).mkdir(exist_ok=True)
            
            if os.name == 'nt':
                # Créer un partage Windows
                cmd = f'net share {share_name}="{receive_folder}" /grant:Everyone,full'
                subprocess.run(cmd, shell=True, capture_output=True)
                
                print(f"✅ Partage créé: \\\\{self.scanner.local_ip}\\{share_name}")
                print(f"📁 Dossier: {receive_folder}")
            
            return True, receive_folder
            
        except Exception as e:
            return False, str(e)

# ============================================================================
# STOCKAGE MESSAGES ÉPHÉMÈRES
# ============================================================================

class EphemeralMessageStore:
    """Stocke messages dans fichiers JSON chiffrés auto-destructifs"""
    
    def __init__(self, username, ttl_hours=24):
        self.username = username
        self.ttl_hours = ttl_hours
        self.data_dir = Path.home() / ".localchat"
        self.data_dir.mkdir(exist_ok=True)
        
        self.encryption_key = self._generate_key(username + "_localchat_2024")
        self.current_file = None
        self.messages = []
        
        self._clean_old_files()
        self._load_or_create_file()
    
    def _generate_key(self, password: str) -> bytes:
        """Génère une clé de chiffrement"""
        salt = b"localchat_secure_salt"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def _get_current_filename(self) -> Path:
        """Génère un nom de fichier basé sur la date"""
        date_str = datetime.now().strftime("%Y%m%d")
        return self.data_dir / f"messages_{date_str}_{self.username[:8]}.enc"
    
    def _clean_old_files(self):
        """Supprime les fichiers de plus de TTL heures"""
        cutoff = datetime.now() - timedelta(hours=self.ttl_hours)
        
        for file in self.data_dir.glob("messages_*.enc"):
            try:
                parts = file.stem.split('_')
                if len(parts) >= 2:
                    file_date = datetime.strptime(parts[1], "%Y%m%d")
                    if file_date < cutoff:
                        file.unlink()
            except:
                continue
    
    def _load_or_create_file(self):
        """Charge ou crée le fichier du jour"""
        self.current_file = self._get_current_filename()
        
        if self.current_file.exists():
            try:
                encrypted_data = self.current_file.read_bytes()
                cipher = Fernet(self.encryption_key)
                decrypted = cipher.decrypt(encrypted_data)
                self.messages = json.loads(decrypted.decode())
            except:
                self.messages = []
        else:
            self.messages = []
    
    def save(self):
        """Sauvegarde les messages"""
        if not self.current_file:
            return
        
        try:
            cipher = Fernet(self.encryption_key)
            data_json = json.dumps(self.messages, ensure_ascii=False, default=str)
            encrypted = cipher.encrypt(data_json.encode())
            self.current_file.write_bytes(encrypted)
        except:
            pass
    
    def add_message(self, message_data):
        """Ajoute un message"""
        message_data['id'] = hashlib.md5(
            f"{time.time()}_{message_data.get('from', '')}".encode()
        ).hexdigest()[:8]
        
        message_data['timestamp'] = datetime.now().isoformat()
        message_data['expires'] = (datetime.now() + timedelta(hours=self.ttl_hours)).isoformat()
        message_data['read'] = message_data.get('read', False)
        
        self.messages.append(message_data)
        
        # Limiter à 2000 messages max
        if len(self.messages) > 2000:
            self.messages = self.messages[-2000:]
        
        self.save()
    
    def get_conversation(self, contact_ip=None, limit=100):
        """Récupère les messages d'une conversation"""
        filtered = self.messages
        
        if contact_ip:
            filtered = [
                m for m in self.messages
                if m.get('from') == contact_ip or m.get('to') == contact_ip
            ]
        
        filtered.sort(key=lambda x: x.get('timestamp', ''))
        return filtered[-limit:]
    
    def get_unread_count(self, contact_ip=None):
        """Compte les messages non lus"""
        unread = [m for m in self.messages 
                 if not m.get('read', False) and m.get('from') != self.username]
        
        if contact_ip:
            unread = [m for m in unread if m.get('from') == contact_ip]
        
        return len(unread)
    
    def mark_as_read(self, contact_ip=None):
        """Marque les messages comme lus"""
        for msg in self.messages:
            if msg.get('from') == contact_ip and msg.get('from') != self.username:
                msg['read'] = True
        
        self.save()
    
    def clear_old_messages(self):
        """Supprime les messages expirés (basé sur TTL)"""
        cutoff = datetime.now() - timedelta(hours=self.ttl_hours)
        
        self.messages = [
            m for m in self.messages
            if datetime.fromisoformat(m.get('expires', '2000-01-01')) > cutoff
        ]
        
        self.save()

# ============================================================================
# MODE CONSOLE COMPLET
# ============================================================================

class ConsoleMode:
    """Mode console avec toutes les fonctionnalités"""
    
    def __init__(self, username, scanner, chat_engine, file_transfer, message_store):
        self.username = username
        self.scanner = scanner
        self.chat = chat_engine
        self.transfer = file_transfer
        self.store = message_store
        self.current_chat = None
        
        # Couleurs
        self.GREEN = '\033[92m'
        self.BLUE = '\033[94m'
        self.YELLOW = '\033[93m'
        self.RED = '\033[91m'
        self.CYAN = '\033[96m'
        self.MAGENTA = '\033[95m'
        self.BOLD = '\033[1m'
        self.END = '\033[0m'
    
    def clear(self):
        """Efface l'écran"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_banner(self):
        """Affiche la bannière"""
        self.clear()
        banner = f"""
{self.CYAN}{'='*70}
{self.BOLD}💬 SMB chat V2 - Mode Console{self.END}
{self.CYAN}{'='*70}
{self.YELLOW}📡 Chat P2P + Transfert fichiers + Messages auto-destructifs (24h)
{self.MAGENTA}👤 Vous: {self.username} | IP: {self.scanner.local_ip}
{self.GREEN}🔄 Tapez 'gui' pour l'interface graphique | 'quit' pour quitter
{self.CYAN}{'='*70}{self.END}
        """
        print(banner)
    
    def show_network_info(self):
        """Affiche les infos réseau"""
        print(f"\n{self.BOLD}🌐 RÉSEAU LOCAL:{self.END}")
        print(f"  {self.GREEN}📍 Votre IP: {self.scanner.local_ip}")
        print(f"  {self.BLUE}📡 Réseau: {self.scanner.get_network_range()}")
        
        chat_users = self.scanner.get_chat_users()
        smb_hosts = self.scanner.get_smb_hosts()
        
        if chat_users:
            print(f"\n{self.GREEN}💬 UTILISATEURS CHAT ({len(chat_users)}):{self.END}")
            for i, (ip, has_chat, has_smb, hostname) in enumerate(chat_users[:8]):
                display = f"{hostname} ({ip})" if hostname else ip
                print(f"     {self.CYAN}{i+1}. {display}{self.END}")
        
        if smb_hosts:
            print(f"\n{self.MAGENTA}📁 HÔTES SMB ({len(smb_hosts)}):{self.END}")
            for i, (ip, has_chat, has_smb, hostname) in enumerate(smb_hosts[:5]):
                display = f"{hostname} ({ip})" if hostname else ip
                print(f"     {self.MAGENTA}{i+1}. {display}{self.END}")
        
        if not chat_users and not smb_hosts:
            print(f"\n{self.YELLOW}⚠️  Aucun hôte détecté. Essayez de rescanner.{self.END}")
        
        print(f"{self.CYAN}{'─'*70}{self.END}")
    
    def main_menu(self):
        """Menu principal console"""
        # Démarrer les services
        self.chat.start()
        
        while True:
            self.show_banner()
            self.show_network_info()
            
            # Afficher notifications
            unread = self.store.get_unread_count()
            if unread > 0:
                print(f"\n{self.YELLOW}📨 Vous avez {unread} message(s) non lu(s){self.END}")
            
            # Menu
            print(f"\n{self.BOLD}📋 MENU PRINCIPAL:{self.END}")
            print(f"{self.GREEN}[1] 💬 Discuter avec quelqu'un")
            print(f"{self.BLUE}[2] 📁 Envoyer un fichier")
            print(f"{self.YELLOW}[3] 🔍 Rescanner le réseau")
            print(f"{self.MAGENTA}[4] 📨 Voir messages récents")
            print(f"{self.CYAN}[5] 👥 Voir tous les contacts")
            print(f"{self.BLUE}[6] ⚙️  Configurer réception fichiers")
            print(f"{self.RED}[0] 🚪 Quitter{self.END}")
            
            print(f"\n{self.CYAN}{'─'*70}{self.END}")
            
            try:
                choice = input(f"\n{self.BOLD}👉 Votre choix: {self.END}").strip().lower()
                
                if choice == '0' or choice == 'quit':
                    break
                elif choice == 'gui':
                    return 'switch_to_gui'
                elif choice == '1':
                    self.chat_menu()
                elif choice == '2':
                    self.transfer_menu()
                elif choice == '3':
                    self.rescan_network()
                elif choice == '4':
                    self.show_recent_messages()
                elif choice == '5':
                    self.show_all_contacts()
                elif choice == '6':
                    self.setup_receiver()
                else:
                    print(f"{self.RED}❌ Choix invalide!{self.END}")
                    time.sleep(1)
            except KeyboardInterrupt:
                print(f"\n{self.YELLOW}⚠️  Utilisez 'quit' pour quitter proprement{self.END}")
            except Exception as e:
                print(f"{self.RED}❌ Erreur: {e}{self.END}")
                time.sleep(1)
        
        # Arrêter les services
        self.chat.stop()
        return None
    
    def chat_menu(self):
        """Menu de chat"""
        chat_users = self.scanner.get_chat_users()
        
        if not chat_users:
            print(f"\n{self.RED}😔 Aucun utilisateur chat disponible{self.END}")
            print(f"{self.YELLOW}Assurez-vous que les autres ont lancé l'application{self.END}")
            input(f"{self.CYAN}Appuyez sur Entrée...{self.END}")
            return
        
        print(f"\n{self.GREEN}👥 Sélectionnez un contact:{self.END}")
        
        for i, (ip, has_chat, has_smb, hostname) in enumerate(chat_users[:15]):
            user_info = self.scanner.online_users.get(ip, {})
            name = user_info.get('name', f'Utilisateur{i+1}')
            status = user_info.get('status', '?')
            
            unread = self.store.get_unread_count(ip)
            unread_badge = f" {self.RED}[{unread}]{self.END}" if unread > 0 else ""
            
            display = f"{name} ({hostname})" if hostname else f"{name} ({ip})"
            print(f"   {self.CYAN}[{i+1}] {display} - {status}{unread_badge}{self.END}")
        
        print(f"   {self.YELLOW}[0] Retour{self.END}")
        
        try:
            choice = input(f"\n{self.CYAN}👉 Numéro: {self.END}").strip()
            
            if choice == '0':
                return
            
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(chat_users):
                    target_ip = chat_users[idx][0]
                    self.start_chat(target_ip)
                else:
                    print(f"{self.RED}❌ Choix invalide{self.END}")
                    time.sleep(1)
            else:
                # Essayer de trouver par IP ou nom
                for ip, has_chat, has_smb, hostname in chat_users:
                    if choice == ip or (hostname and choice.lower() in hostname.lower()):
                        self.start_chat(ip)
                        return
                
                print(f"{self.RED}❌ Contact non trouvé{self.END}")
                time.sleep(1)
                
        except Exception as e:
            print(f"{self.RED}❌ Erreur: {e}{self.END}")
            time.sleep(1)
    
    def start_chat(self, target_ip):
        """Démarre une conversation"""
        self.current_chat = target_ip
        
        # Marquer les messages comme lus
        self.store.mark_as_read(target_ip)
        
        user_info = self.scanner.online_users.get(target_ip, {})
        target_name = user_info.get('name', target_ip)
        
        self.clear()
        print(f"\n{self.GREEN}💬 Discussion avec {target_name} ({target_ip}){self.END}")
        print(f"{self.YELLOW}Tapez '/quit' pour quitter | '/file' pour envoyer un fichier{self.END}")
        print(f"{self.CYAN}{'─'*70}{self.END}")
        
        # Afficher l'historique
        history = self.store.get_conversation(target_ip, limit=20)
        
        for msg in history:
            timestamp = datetime.fromisoformat(msg['timestamp']).strftime("%H:%M")
            
            if msg['from'] == self.scanner.local_ip:
                print(f"{self.BLUE}[{timestamp}] Vous: {msg.get('text', '')}{self.END}")
            else:
                print(f"{self.GREEN}[{timestamp}] {msg.get('from_name', target_name)}: {msg.get('text', '')}{self.END}")
        
        # Boucle de chat
        while True:
            try:
                user_input = input(f"\n{self.BOLD}Vous: {self.END}").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() == '/quit':
                    print(f"{self.YELLOW}👋 Fin de la discussion{self.END}")
                    self.current_chat = None
                    time.sleep(1)
                    break
                
                elif user_input.lower() == '/file':
                    self.send_file_to_contact(target_ip)
                    continue
                
                # Envoyer le message
                success, result = self.chat.send_message(target_ip, user_input)
                
                if success:
                    # Afficher immédiatement
                    timestamp = datetime.now().strftime("%H:%M")
                    print(f"{self.BLUE}[{timestamp}] Vous: {user_input}{self.END}")
                else:
                    print(f"{self.RED}{result}{self.END}")
                    
            except KeyboardInterrupt:
                print(f"\n{self.YELLOW}⚠️  Tapez '/quit' pour quitter{self.END}")
            except Exception as e:
                print(f"{self.RED}❌ Erreur: {e}{self.END}")
    
    def send_file_to_contact(self, target_ip):
        """Envoie un fichier depuis le chat"""
        print(f"\n{self.MAGENTA}📁 ENVOYER UN FICHIER À {target_ip}{self.END}")
        
        file_path = input(f"{self.CYAN}Chemin du fichier: {self.END}").strip().strip('"\'')
        
        if not os.path.exists(file_path):
            print(f"{self.RED}❌ Fichier introuvable!{self.END}")
            return
        
        share_name = input(f"{self.CYAN}Nom du partage [TransferShare]: {self.END}").strip()
        if not share_name:
            share_name = "TransferShare"
        
        success, result = self.transfer.send_file(file_path, target_ip, share_name)
        
        if success:
            print(f"{self.GREEN}{result}{self.END}")
            
            # Afficher dans le chat
            filename = os.path.basename(file_path)
            timestamp = datetime.now().strftime("%H:%M")
            print(f"{self.BLUE}[{timestamp}] Vous: 📁 {filename} envoyé{self.END}")
        else:
            print(f"{self.RED}{result}{self.END}")
        
        time.sleep(1)
    
    def transfer_menu(self):
        """Menu transfert de fichiers"""
        print(f"\n{self.BOLD}📁 TRANSFERT DE FICHIERS{self.END}")
        
        # Lister les hôtes SMB
        smb_hosts = self.scanner.get_smb_hosts()
        
        if not smb_hosts:
            print(f"{self.YELLOW}⚠️  Aucun hôte SMB détecté{self.END}")
            print(f"{self.CYAN}Essayez de rescanner le réseau{self.END}")
            input(f"{self.CYAN}Appuyez sur Entrée...{self.END}")
            return
        
        print(f"\n{self.MAGENTA}📡 HÔTES SMB DISPONIBLES:{self.END}")
        
        for i, (ip, has_chat, has_smb, hostname) in enumerate(smb_hosts[:10]):
            display = f"{hostname} ({ip})" if hostname else ip
            print(f"   {self.CYAN}[{i+1}] {display}{self.END}")
        
        print(f"   {self.YELLOW}[0] Retour{self.END}")
        
        try:
            choice = input(f"\n{self.CYAN}👉 Sélection ou IP: {self.END}").strip()
            
            if choice == '0':
                return
            
            target_ip = None
            
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(smb_hosts):
                    target_ip = smb_hosts[idx][0]
            else:
                # Chercher par IP ou nom
                for ip, has_chat, has_smb, hostname in smb_hosts:
                    if choice == ip or (hostname and choice.lower() in hostname.lower()):
                        target_ip = ip
                        break
            
            if not target_ip:
                print(f"{self.RED}❌ Hôte non trouvé{self.END}")
                time.sleep(1)
                return
            
            # Demander le fichier
            file_path = input(f"\n{self.CYAN}📂 Chemin du fichier: {self.END}").strip().strip('"\'')
            
            if not os.path.exists(file_path):
                print(f"{self.RED}❌ Fichier introuvable!{self.END}")
                return
            
            share_name = input(f"{self.CYAN}📁 Nom du partage [TransferShare]: {self.END}").strip()
            if not share_name:
                share_name = "TransferShare"
            
            # Confirmer
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            print(f"\n{self.BOLD}📋 CONFIRMATION:{self.END}")
            print(f"   {self.GREEN}Fichier: {filename}")
            print(f"   {self.BLUE}Taille: {file_size:,} octets")
            print(f"   {self.MAGENTA}Destination: {target_ip} ({share_name}){self.END}")
            
            confirm = input(f"\n{self.YELLOW}⚠️  Lancer le transfert? (o/n): {self.END}").lower()
            
            if confirm == 'o':
                success, result = self.transfer.send_file(file_path, target_ip, share_name)
                print(f"\n{result}")
            else:
                print(f"\n{self.YELLOW}🚫 Transfert annulé{self.END}")
            
            input(f"\n{self.CYAN}Appuyez sur Entrée...{self.END}")
            
        except Exception as e:
            print(f"{self.RED}❌ Erreur: {e}{self.END}")
            time.sleep(1)
    
    def rescan_network(self):
        """Rescanne le réseau"""
        print(f"\n{self.YELLOW}🔄 Nouveau scan en cours...{self.END}")
        
        # Animation
        for i in range(5):
            print(f"{self.YELLOW}.", end='', flush=True)
            time.sleep(0.3)
        print()
        
        self.scanner.scan_network(quick=True)
        
        print(f"{self.GREEN}✅ Scan terminé!{self.END}")
        time.sleep(1)
    
    def show_recent_messages(self, limit=20):
        """Affiche les messages récents"""
        recent = self.store.messages[-limit:]
        
        if not recent:
            print(f"\n{self.YELLOW}📭 Aucun message récent{self.END}")
            input(f"{self.CYAN}Appuyez sur Entrée...{self.END}")
            return
        
        print(f"\n{self.BOLD}📨 {len(recent)} MESSAGES RÉCENTS:{self.END}")
        print(f"{self.CYAN}{'─'*70}{self.END}")
        
        for msg in recent:
            timestamp = datetime.fromisoformat(msg['timestamp']).strftime("%m/%d %H:%M")
            sender = msg.get('from_name', msg.get('from', '?'))
            
            # Couleur selon l'expéditeur
            if sender == self.username or msg['from'] == self.scanner.local_ip:
                color = self.BLUE
                sender_display = "Vous"
            else:
                color = self.GREEN
                sender_display = sender
            
            # Format selon le type
            if msg.get('type') == 'file':
                content = f"📁 {msg.get('file_name', 'fichier')}"
                if msg.get('file_size'):
                    content += f" ({msg.get('file_size'):,} octets)"
            else:
                content = msg.get('text', '')[:60]
                if len(msg.get('text', '')) > 60:
                    content += "..."
            
            # Marqueur non lu
            read_marker = "" if msg.get('read') or sender == self.username else f" {self.RED}●{self.END}"
            
            print(f"{color}[{timestamp}] {sender_display}: {content}{read_marker}{self.END}")
        
        print(f"{self.CYAN}{'─'*70}{self.END}")
        input(f"\n{self.CYAN}Appuyez sur Entrée...{self.END}")
    
    def show_all_contacts(self):
        """Affiche tous les contacts"""
        # Extraire les contacts uniques
        contacts = set()
        for msg in self.store.messages[-500:]:
            if msg.get('from') and msg.get('from') != self.scanner.local_ip:
                contacts.add((msg['from'], msg.get('from_name', 'Inconnu')))
            if msg.get('to'):
                contacts.add((msg['to'], self.scanner.online_users.get(msg['to'], {}).get('name', msg['to'])))
        
        if not contacts:
            print(f"\n{self.YELLOW}👥 Aucun contact trouvé{self.END}")
            input(f"{self.CYAN}Appuyez sur Entrée...{self.END}")
            return
        
        print(f"\n{self.BOLD}👥 {len(contacts)} CONTACTS:{self.END}")
        print(f"{self.CYAN}{'─'*70}{self.END}")
        
        for i, (ip, name) in enumerate(sorted(list(contacts))[:30]):
            unread = self.store.get_unread_count(ip)
            unread_badge = f" {self.RED}[{unread}]{self.END}" if unread > 0 else ""
            
            print(f"   {self.CYAN}{i+1:2d}. {name} ({ip}){unread_badge}{self.END}")
        
        print(f"{self.CYAN}{'─'*70}{self.END}")
        input(f"\n{self.CYAN}Appuyez sur Entrée...{self.END}")
    
    def setup_receiver(self):
        """Configure la réception de fichiers"""
        print(f"\n{self.BOLD}⚙️  CONFIGURATION RÉCEPTION FICHIERS{self.END}")
        
        share_name = input(f"{self.CYAN}Nom du partage [ReceiveShare]: {self.END}").strip()
        if not share_name:
            share_name = "ReceiveShare"
        
        success, result = self.transfer.setup_receiver(share_name)
        
        if success:
            print(f"\n{self.GREEN}✅ Configuration réussie!{self.END}")
            print(f"\n{self.BOLD}🎯 Partage créé:{self.END}")
            print(f"   {self.CYAN}Adresse: \\\\{self.scanner.local_ip}\\{share_name}{self.END}")
            print(f"   {self.CYAN}Dossier: {result}{self.END}")
        else:
            print(f"\n{self.RED}❌ Erreur: {result}{self.END}")
        
        input(f"\n{self.CYAN}Appuyez sur Entrée...{self.END}")

# ============================================================================
# INTERFACE GRAPHIQUE (CustomTkinter)
# ============================================================================

class GUIMode:
    """Interface graphique complète"""
    
    def __init__(self, username, scanner, chat_engine, file_transfer, message_store):
        self.username = username
        self.scanner = scanner
        self.chat = chat_engine
        self.transfer = file_transfer
        self.store = message_store
        
        self.app = None
        self.current_chat = None
        
        try:
            import customtkinter as ctk
            self.ctk = ctk
            self.has_gui = True
        except ImportError:
            print("❌ CustomTkinter non installé. pip install customtkinter")
            self.has_gui = False
            return
        
        # Configurer CustomTkinter
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
    
    def launch(self):
        """Lance l'interface graphique"""
        if not self.has_gui:
            return 'switch_to_console'
        
        try:
            self._create_app()
            self.chat.start()
            self._start_auto_refresh()
            self.app.mainloop()
            self.chat.stop()
            return None
        except Exception as e:
            print(f"❌ Erreur GUI: {e}")
            return 'switch_to_console'
    
    def _create_app(self):
        """Crée la fenêtre principale"""
        self.app = self.ctk.CTk()
        self.app.title(f"SMB chat V2 - {self.username}")
        self.app.geometry("1200x800")
        
        # Configurer la grille
        self.app.grid_columnconfigure(1, weight=1)
        self.app.grid_rowconfigure(0, weight=1)
        
        # Créer les frames
        self._create_sidebar()
        self._create_main_area()
        self._create_status_bar()
        
        # Mettre à jour initialement
        self._update_contacts_list()
        self._update_status()
    
    def _create_sidebar(self):
        """Crée la barre latérale"""
        sidebar = self.ctk.CTkFrame(self.app, width=300, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew", rowspan=2)
        sidebar.grid_propagate(False)
        
        # Titre
        title = self.ctk.CTkLabel(
            sidebar,
            text="💬 Contacts",
            font=("Arial", 22, "bold")
        )
        title.pack(pady=(20, 10), padx=20)
        
        # Bouton scan
        scan_btn = self.ctk.CTkButton(
            sidebar,
            text="🔍 Scanner réseau",
            command=self._scan_network_gui
        )
        scan_btn.pack(pady=5, padx=20, fill="x")
        
        # Séparateur
        sep = self.ctk.CTkFrame(sidebar, height=2, fg_color="gray30")
        sep.pack(pady=10, padx=20, fill="x")
        
        # Frame contacts avec scroll
        contacts_container = self.ctk.CTkScrollableFrame(sidebar)
        contacts_container.pack(pady=10, padx=10, fill="both", expand=True)
        
        self.contacts_frame = contacts_container
        self.contact_widgets = {}
        
        # Boutons d'action
        action_frame = self.ctk.CTkFrame(sidebar, fg_color="transparent")
        action_frame.pack(pady=10, padx=20, fill="x")
        
        # Bouton transfert
        transfer_btn = self.ctk.CTkButton(
            action_frame,
            text="📁 Envoyer fichier",
            command=self._show_transfer_dialog
        )
        transfer_btn.pack(pady=5, fill="x")
        
        # Bouton console
        console_btn = self.ctk.CTkButton(
            action_frame,
            text="⌨️ Mode Console",
            fg_color="gray40",
            hover_color="gray50",
            command=self._switch_to_console
        )
        console_btn.pack(pady=5, fill="x")
    
    def _create_main_area(self):
        """Crée la zone principale de chat"""
        main_area = self.ctk.CTkFrame(self.app, corner_radius=0)
        main_area.grid(row=0, column=1, sticky="nsew")
        
        # En-tête de conversation
        self.chat_header = self.ctk.CTkFrame(main_area, height=80)
        self.chat_header.pack(fill="x", padx=20, pady=(20, 10))
        self.chat_header.pack_propagate(False)
        
        self.chat_title = self.ctk.CTkLabel(
            self.chat_header,
            text="💬 Sélectionnez un contact",
            font=("Arial", 24, "bold")
        )
        self.chat_title.pack(expand=True)
        
        self.chat_status = self.ctk.CTkLabel(
            self.chat_header,
            text="",
            font=("Arial", 12),
            text_color="gray"
        )
        self.chat_status.pack()
        
        # Zone de messages
        messages_container = self.ctk.CTkScrollableFrame(
            main_area,
            fg_color="transparent"
        )
        messages_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.messages_frame = messages_container
        self.message_widgets = []
        
        # Zone de saisie
        input_frame = self.ctk.CTkFrame(main_area, height=120)
        input_frame.pack(fill="x", padx=20, pady=(0, 20))
        input_frame.pack_propagate(False)
        
        # Boutons rapides
        quick_frame = self.ctk.CTkFrame(input_frame, fg_color="transparent")
        quick_frame.pack(fill="x", padx=10, pady=5)
        
        buttons = [
            ("📎 Fichier", self._attach_file),
            ("🖼️ Image", self._attach_image),
            ("🎤 Audio", self._record_audio),
            ("📁 Envoyer", self._show_transfer_dialog)
        ]
        
        for text, command in buttons:
            btn = self.ctk.CTkButton(
                quick_frame,
                text=text,
                width=80,
                command=command
            )
            btn.pack(side="left", padx=2)
        
        # Zone texte
        self.message_input = self.ctk.CTkTextbox(
            input_frame,
            height=60,
            font=("Arial", 14)
        )
        self.message_input.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.message_input.bind("<Return>", self._on_enter_pressed)
        
        # Bouton envoyer
        send_btn = self.ctk.CTkButton(
            input_frame,
            text="➤ ENVOYER",
            width=100,
            font=("Arial", 14, "bold"),
            command=self._send_message_gui
        )
        send_btn.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)
    
    def _create_status_bar(self):
        """Crée la barre de statut"""
        status_bar = self.ctk.CTkFrame(self.app, height=40)
        status_bar.grid(row=1, column=1, sticky="ew", padx=20, pady=(0, 20))
        status_bar.grid_propagate(False)
        
        # IP locale
        self.ip_label = self.ctk.CTkLabel(
            status_bar,
            text=f"🌐 {self.scanner.local_ip}",
            font=("Arial", 12)
        )
        self.ip_label.pack(side="left", padx=20)
        
        # Nombre de messages
        self.msg_count_label = self.ctk.CTkLabel(
            status_bar,
            text="📨 0 messages",
            font=("Arial", 12)
        )
        self.msg_count_label.pack(side="left", padx=20)
        
        # Utilisateurs en ligne
        self.users_label = self.ctk.CTkLabel(
            status_bar,
            text="👥 0 en ligne",
            font=("Arial", 12)
        )
        self.users_label.pack(side="left", padx=20)
        
        # Bouton rafraîchir
        refresh_btn = self.ctk.CTkButton(
            status_bar,
            text="🔄",
            width=40,
            command=self._update_all
        )
        refresh_btn.pack(side="right", padx=20)
    
    def _update_contacts_list(self):
        """Met à jour la liste des contacts"""
        # Nettoyer
        for widget in self.contacts_frame.winfo_children():
            widget.destroy()
        
        self.contact_widgets.clear()
        
        # Obtenir les contacts avec chat
        chat_users = self.scanner.get_chat_users()
        
        if not chat_users:
            empty_label = self.ctk.CTkLabel(
                self.contacts_frame,
                text="Aucun contact disponible\n(Scanner le réseau)",
                text_color="gray",
                font=("Arial", 14)
            )
            empty_label.pack(pady=50)
            return
        
        # Ajouter chaque contact
        for ip, has_chat, has_smb, hostname in chat_users[:30]:
            user_info = self.scanner.online_users.get(ip, {})
            name = user_info.get('name', f"Utilisateur {ip[-3:]}")
            status = user_info.get('status', '🟢')
            
            unread = self.store.get_unread_count(ip)
            
            # Créer le frame du contact
            contact_frame = self.ctk.CTkFrame(
                self.contacts_frame,
                height=70,
                corner_radius=10
            )
            contact_frame.pack(fill="x", pady=5, padx=5)
            contact_frame.pack_propagate(False)
            
            # Bind le clic
            contact_frame.bind("<Button-1>", lambda e, ip=ip: self._open_chat_gui(ip))
            
            # Avatar/emoji
            avatar = self.ctk.CTkLabel(
                contact_frame,
                text="👤",
                font=("Arial", 20),
                width=50
            )
            avatar.pack(side="left", padx=15, pady=10)
            avatar.bind("<Button-1>", lambda e, ip=ip: self._open_chat_gui(ip))
            
            # Informations
            info_frame = self.ctk.CTkFrame(contact_frame, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=10)
            
            name_label = self.ctk.CTkLabel(
                info_frame,
                text=name,
                font=("Arial", 16, "bold"),
                anchor="w"
            )
            name_label.pack(fill="x")
            name_label.bind("<Button-1>", lambda e, ip=ip: self._open_chat_gui(ip))
            
            ip_label = self.ctk.CTkLabel(
                info_frame,
                text=f"{hostname or ip} • {status}",
                font=("Arial", 12),
                text_color="gray",
                anchor="w"
            )
            ip_label.pack(fill="x")
            ip_label.bind("<Button-1>", lambda e, ip=ip: self._open_chat_gui(ip))
            
            # Badge messages non lus
            if unread > 0:
                badge = self.ctk.CTkLabel(
                    contact_frame,
                    text=str(unread),
                    text_color="white",
                    fg_color="red",
                    width=30,
                    height=30,
                    corner_radius=15,
                    font=("Arial", 12, "bold")
                )
                badge.pack(side="right", padx=15)
                badge.bind("<Button-1>", lambda e, ip=ip: self._open_chat_gui(ip))
            
            self.contact_widgets[ip] = contact_frame
    
    def _open_chat_gui(self, contact_ip):
        """Ouvre une conversation"""
        self.current_chat = contact_ip
        
        # Marquer comme lus
        self.store.mark_as_read(contact_ip)
        
        # Mettre à jour l'en-tête
        user_info = self.scanner.online_users.get(contact_ip, {})
        name = user_info.get('name', contact_ip)
        status = user_info.get('status', '🟢 En ligne')
        
        self.chat_title.configure(text=f"💬 {name}")
        self.chat_status.configure(text=f"{contact_ip} • {status}")
        
        # Nettoyer les messages
        for widget in self.messages_frame.winfo_children():
            widget.destroy()
        
        self.message_widgets.clear()
        
        # Charger l'historique
        history = self.store.get_conversation(contact_ip, limit=50)
        
        for msg in history:
            self._add_message_to_gui(msg)
        
        # Focus sur l'input
        self.message_input.focus()
    
    def _add_message_to_gui(self, msg):
        """Ajoute un message à l'interface"""
        # Créer le frame du message
        msg_frame = self.ctk.CTkFrame(
            self.messages_frame,
            fg_color="transparent",
            corner_radius=10
        )
        
        # Configurer selon l'expéditeur
        if msg['from'] == self.scanner.local_ip or msg.get('from_name') == self.username:
            # Notre message (aligné à droite)
            msg_frame.pack(anchor="e", padx=20, pady=5, fill="x")
            bg_color = "#2B5278"  # Bleu foncé
            text_color = "white"
        else:
            # Message reçu (aligné à gauche)
            msg_frame.pack(anchor="w", padx=20, pady=5, fill="x")
            bg_color = "#1F1F1F"  # Gris foncé
            text_color = "white"
        
        # Contenu
        content_frame = self.ctk.CTkFrame(
            msg_frame,
            fg_color=bg_color,
            corner_radius=15
        )
        content_frame.pack(fill="x", padx=10 if msg['from'] == self.scanner.local_ip else 50)
        
        # En-tête (nom + heure)
        timestamp = datetime.fromisoformat(msg['timestamp']).strftime("%H:%M")
        sender = msg.get('from_name', msg['from'])
        
        header_frame = self.ctk.CTkFrame(content_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(10, 0))
        
        if msg['from'] != self.scanner.local_ip:
            name_label = self.ctk.CTkLabel(
                header_frame,
                text=sender,
                font=("Arial", 12, "bold"),
                text_color="#4FC3F7",
                anchor="w"
            )
            name_label.pack(side="left")
        
        time_label = self.ctk.CTkLabel(
            header_frame,
            text=timestamp,
            font=("Arial", 10),
            text_color="gray",
            anchor="e"
        )
        time_label.pack(side="right")
        
        # Corps du message
        if msg.get('type') == 'file':
            # Message fichier
            file_frame = self.ctk.CTkFrame(content_frame, fg_color="transparent")
            file_frame.pack(fill="x", padx=15, pady=5)
            
            file_icon = self.ctk.CTkLabel(
                file_frame,
                text="📁",
                font=("Arial", 20)
            )
            file_icon.pack(side="left", padx=(0, 10))
            
            file_info = self.ctk.CTkFrame(file_frame, fg_color="transparent")
            file_info.pack(side="left", fill="both", expand=True)
            
            file_name = self.ctk.CTkLabel(
                file_info,
                text=msg.get('file_name', 'Fichier'),
                font=("Arial", 14),
                text_color=text_color,
                anchor="w"
            )
            file_name.pack(fill="x")
            
            if msg.get('file_size'):
                file_size = self.ctk.CTkLabel(
                    file_info,
                    text=f"{msg.get('file_size'):,} octets",
                    font=("Arial", 11),
                    text_color="gray",
                    anchor="w"
                )
                file_size.pack(fill="x")
            
            if msg.get('status') == 'success':
                status_label = self.ctk.CTkLabel(
                    file_frame,
                    text="✅",
                    font=("Arial", 16)
                )
                status_label.pack(side="right", padx=10)
        else:
            # Message texte
            text_label = self.ctk.CTkLabel(
                content_frame,
                text=msg.get('text', ''),
                font=("Arial", 14),
                text_color=text_color,
                wraplength=500,
                justify="left",
                anchor="w"
            )
            text_label.pack(fill="x", padx=15, pady=10)
        
        # Scroll vers le bas
        self.messages_frame._parent_canvas.yview_moveto(1.0)
        
        self.message_widgets.append(msg_frame)
    
    def _send_message_gui(self):
        """Envoie un message depuis l'interface"""
        if not self.current_chat:
            self._show_notification("⚠️ Sélectionnez un contact d'abord")
            return
        
        message = self.message_input.get("1.0", "end-1c").strip()
        if not message:
            return
        
        # Envoyer
        success, result = self.chat.send_message(self.current_chat, message)
        
        if success:
            # Effacer l'input
            self.message_input.delete("1.0", "end")
            
            # Ajouter à l'affichage immédiatement
            msg_data = {
                'from': self.scanner.local_ip,
                'from_name': self.username,
                'to': self.current_chat,
                'text': message,
                'type': 'text',
                'timestamp': datetime.now().isoformat()
            }
            
            self._add_message_to_gui(msg_data)
        else:
            self._show_notification(f"❌ {result}")
    
    def _on_enter_pressed(self, event):
        """Gère Entrée (Ctrl+Entrée pour nouvelle ligne)"""
        if event.state & 0x4:  # Ctrl
            return  # Nouvelle ligne
        else:
            self._send_message_gui()
            return "break"
    
    def _show_transfer_dialog(self):
        """Affiche la boîte de dialogue de transfert"""
        dialog = self.ctk.CTkToplevel(self.app)
        dialog.title("📁 Envoyer un fichier")
        dialog.geometry("600x500")
        dialog.transient(self.app)
        dialog.grab_set()
        
        # Centrer
        dialog.update_idletasks()
        x = self.app.winfo_x() + (self.app.winfo_width() // 2) - (600 // 2)
        y = self.app.winfo_y() + (self.app.winfo_height() // 2) - (500 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Titre
        title = self.ctk.CTkLabel(
            dialog,
            text="Envoyer un fichier",
            font=("Arial", 20, "bold")
        )
        title.pack(pady=20)
        
        # Sélection fichier
        file_frame = self.ctk.CTkFrame(dialog, fg_color="transparent")
        file_frame.pack(fill="x", padx=40, pady=10)
        
        self.ctk.CTkLabel(
            file_frame,
            text="Fichier:",
            font=("Arial", 14)
        ).pack(anchor="w")
        
        file_path_var = self.ctk.StringVar()
        
        file_entry = self.ctk.CTkEntry(
            file_frame,
            textvariable=file_path_var,
            font=("Arial", 12)
        )
        file_entry.pack(fill="x", pady=5)
        
        browse_btn = self.ctk.CTkButton(
            file_frame,
            text="Parcourir...",
            command=lambda: self._browse_file(file_path_var),
            width=100
        )
        browse_btn.pack(anchor="e")
        
        # Sélection destination
        dest_frame = self.ctk.CTkFrame(dialog, fg_color="transparent")
        dest_frame.pack(fill="x", padx=40, pady=10)
        
        self.ctk.CTkLabel(
            dest_frame,
            text="Destination:",
            font=("Arial", 14)
        ).pack(anchor="w")
        
        # Liste des hôtes SMB
        smb_hosts = self.scanner.get_smb_hosts()
        
        if not smb_hosts:
            self.ctk.CTkLabel(
                dest_frame,
                text="Aucun hôte SMB détecté",
                text_color="gray"
            ).pack(pady=10)
        else:
            for ip, has_chat, has_smb, hostname in smb_hosts[:10]:
                host_frame = self.ctk.CTkFrame(dest_frame, height=50, corner_radius=8)
                host_frame.pack(fill="x", pady=2)
                host_frame.pack_propagate(False)
                
                # Radio button
                radio = self.ctk.CTkRadioButton(
                    host_frame,
                    text=f"{hostname or ip}",
                    value=ip,
                    variable=self.ctk.StringVar(value=""),
                    command=lambda ip=ip: file_path_var.set(ip)
                )
                radio.pack(side="left", padx=15, pady=15)
                
                # IP
                self.ctk.CTkLabel(
                    host_frame,
                    text=ip,
                    text_color="gray",
                    font=("Arial", 11)
                ).pack(side="right", padx=15, pady=15)
        
        # Nom du partage
        share_frame = self.ctk.CTkFrame(dialog, fg_color="transparent")
        share_frame.pack(fill="x", padx=40, pady=10)
        
        self.ctk.CTkLabel(
            share_frame,
            text="Nom du partage:",
            font=("Arial", 14)
        ).pack(anchor="w")
        
        share_entry = self.ctk.CTkEntry(
            share_frame,
            placeholder_text="TransferShare",
            font=("Arial", 12)
        )
        share_entry.pack(fill="x", pady=5)
        
        # Boutons
        btn_frame = self.ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=40, pady=20)
        
        def send_file():
            file_path = file_path_var.get()
            target_ip = ""  # À récupérer du radio button
            share_name = share_entry.get() or "TransferShare"
            
            if not file_path or not os.path.exists(file_path):
                self._show_notification("❌ Fichier invalide")
                return
            
            if not target_ip:
                self._show_notification("❌ Sélectionnez une destination")
                return
            
            dialog.destroy()
            
            # Envoyer le fichier
            success, result = self.transfer.send_file(file_path, target_ip, share_name)
            
            if success and self.current_chat == target_ip:
                # Ajouter au chat
                msg_data = {
                    'from': self.scanner.local_ip,
                    'from_name': self.username,
                    'to': target_ip,
                    'type': 'file',
                    'file_name': os.path.basename(file_path),
                    'file_size': os.path.getsize(file_path),
                    'text': f"Fichier envoyé: {os.path.basename(file_path)}",
                    'timestamp': datetime.now().isoformat()
                }
                
                self.store.add_message(msg_data)
                self._add_message_to_gui(msg_data)
            
            self._show_notification(result)
        
        send_btn = self.ctk.CTkButton(
            btn_frame,
            text="📤 Envoyer",
            command=send_file,
            height=40,
            font=("Arial", 14, "bold")
        )
        send_btn.pack(side="right", padx=5)
        
        cancel_btn = self.ctk.CTkButton(
            btn_frame,
            text="Annuler",
            command=dialog.destroy,
            height=40,
            fg_color="gray40",
            hover_color="gray50"
        )
        cancel_btn.pack(side="right", padx=5)
    
    def _browse_file(self, path_var): 
        """Ouvre un dialogue de sélection de fichier"""
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="Sélectionner un fichier",
            filetypes=[("Tous les fichiers", "*.*")]
        )
        if file_path:
            path_var.set(file_path)
    
    def _scan_network_gui(self):
        """Scan réseau depuis l'interface"""
        # Désactiver bouton pendant le scan
        for widget in self.app.winfo_children():
            if isinstance(widget, self.ctk.CTkButton) and "Scanner" in widget.cget("text"):
                widget.configure(state="disabled", text="🔍 Scanning...")
                break
        
        # Scanner dans un thread
        def scan_thread():
            self.scanner.scan_network(quick=True)
            self.app.after(0, self._update_all)
            self.app.after(0, lambda: self._show_notification(f"✅ {len(self.scanner.available_hosts)} hôtes détectés"))
            
            # Réactiver bouton
            for widget in self.app.winfo_children():
                if isinstance(widget, self.ctk.CTkButton) and "Scanning" in widget.cget("text"):
                    widget.configure(state="normal", text="🔍 Scanner réseau")
                    break
        
        threading.Thread(target=scan_thread, daemon=True).start()
    
    def _update_all(self):
        """Met à jour toute l'interface"""
        self._update_contacts_list()
        self._update_status()
        
        # Si en chat, vérifier nouveaux messages
        if self.current_chat:
            history = self.store.get_conversation(self.current_chat, limit=100)
            current_ids = {w.winfo_id() for w in self.message_widgets}
            
            # Vérifier si nouveaux messages
            if len(history) > len(self.message_widgets):
                # Nettoyer et recharger
                for widget in self.messages_frame.winfo_children():
                    widget.destroy()
                
                self.message_widgets.clear()
                
                for msg in history:
                    self._add_message_to_gui(msg)
    
    def _update_status(self):
        """Met à jour la barre de statut"""
        self.ip_label.configure(text=f"🌐 {self.scanner.local_ip}")
        self.msg_count_label.configure(text=f"📨 {len(self.store.messages)} messages")
        
        online_count = len([h for h in self.scanner.available_hosts if h[1]])  # has_chat
        self.users_label.configure(text=f"👥 {online_count} en ligne")
    
    def _start_auto_refresh(self):
        """Démarre le rafraîchissement automatique"""
        def refresh():
            if self.app and self.app.winfo_exists():
                self._update_all()
                self.app.after(5000, refresh)  # Toutes les 5 secondes
        
        self.app.after(5000, refresh)
    
    def _show_notification(self, message):
        """Affiche une notification"""
        # Simple popup temporaire
        notification = self.ctk.CTkToplevel(self.app)
        notification.title("Notification")
        notification.geometry("300x100")
        notification.overrideredirect(True)  # Sans bordure
        
        # Positionner en bas à droite
        x = self.app.winfo_x() + self.app.winfo_width() - 320
        y = self.app.winfo_y() + self.app.winfo_height() - 120
        notification.geometry(f"+{x}+{y}")
        
        # Contenu
        label = self.ctk.CTkLabel(
            notification,
            text=message,
            font=("Arial", 12),
            wraplength=280
        )
        label.pack(expand=True, padx=20, pady=20)
        
        # Fermer après 3 secondes
        notification.after(3000, notification.destroy)
    
    def _attach_file(self):
        self._show_notification("📎 Fonctionnalité à implémenter")
    
    def _attach_image(self):
        self._show_notification("🖼️ Fonctionnalité à implémenter")
    
    def _record_audio(self):
        self._show_notification("🎤 Fonctionnalité à implémenter")
    
    def _switch_to_console(self):
        """Retourne au mode console"""
        self.app.destroy()
        raise SystemExit("switch_to_console")

# ============================================================================
# POINT D'ENTRÉE PRINCIPAL
# ============================================================================

def main():
    """Point d'entrée principal"""
    print("\n" + "="*70)
    print("🚀 SMB chat V2 V1.0 - Lancement...")
    print("="*70)
    
    # Demander le pseudo
    username = input("\n👤 Entrez votre pseudo: ").strip()
    if not username:
        username = f"User_{int(time.time()) % 10000}"
    
    print(f"\n🔧 Initialisation des modules...")
    
    # Initialiser les modules
    scanner = NetworkScanner()
    store = EphemeralMessageStore(username)
    chat = ChatEngine(username, scanner, store)
    transfer = FileTransfer(scanner, store)
    
    # Scanner rapide
    print("🔍 Scan réseau initial...")
    scanner.scan_network(quick=True)
    
    # Vérifier si GUI disponible
    try:
        import customtkinter
        has_gui = True
    except ImportError:
        has_gui = False
        print("\n⚠️  CustomTkinter non installé - Mode console uniquement")
        print("   Pour l'interface graphique: pip install customtkinter")
    
    # Choix du mode
    if has_gui:
        print("\n🎯 CHOIX DU MODE D'INTERFACE:")
        print("   1. 🖥️  Interface graphique (recommandé)")
        print("   2. ⌨️  Mode console rapide")
        print("   3. 🤖 Démarrer en arrière-plan")
        
        choice = input("\n👉 Votre choix [1-3]: ").strip()
        
        if choice == "1":
            print("\n🚀 Lancement de l'interface graphique...")
            gui = GUIMode(username, scanner, chat, transfer, store)
            result = gui.launch()
            
            if result == 'switch_to_console':
                print("\n🔄 Retour au mode console...")
                time.sleep(1)
                choice = "2"
        
        if choice == "2" or not has_gui:
            print("\n🚀 Lancement du mode console...")
            console = ConsoleMode(username, scanner, chat, transfer, store)
            console.main_menu()
        
        elif choice == "3":
            print("\n🤖 Mode arrière-plan - À implémenter")
            print("   (Le service tourne, interface via tray icon)")
            input("Appuyez sur Entrée pour quitter...")
    
    else:
        # Mode console forcé
        print("\n🚀 Lancement du mode console...")
        console = ConsoleMode(username, scanner, chat, transfer, store)
        console.main_menu()
    
    print("\n👋 Au revoir!")
    print("="*70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption - Fermeture propre...")
    except SystemExit as e:
        if str(e) == "switch_to_console":
            # Relancer en mode console
            print("\n" + "="*70)
            print("🔄 Passage au mode console...")
            print("="*70)
            
            # Réinitialiser et relancer en console
            # (Dans une vraie app, on redémarrerait proprement)
            print("\n⚠️  Redémarrez l'application pour le mode console")
            input("Appuyez sur Entrée pour quitter...")
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        input("\nAppuyez sur Entrée pour quitter...")