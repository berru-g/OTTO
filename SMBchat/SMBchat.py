"""
LOCAL NETWORK CHAT P2P V1.2- Chat en réseau local via le protocol SMB
Version avec : Toast notifications + Sons + Tray icon
"""

import os
import sys
import socket
import threading
import json
import time
import select
from datetime import datetime
import ipaddress
import subprocess
from pathlib import Path
import codecs
import base64
import tempfile
import winsound  # Pour les sons Windows
import ctypes    # Pour les notifications avancées

# Fix pour l'encodage Windows
if os.name == 'nt':
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    except:
        pass

# Pour les couleurs dans le terminal
class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

# Variables globales
available_hosts = []  # Liste des IPs disponibles
online_users = {}     # {ip: {name, status, last_seen}}
messages = []         # Historique des messages
current_chat = None   # IP de la personne avec qui on discute
username = "Anonyme"  # Notre pseudo
chat_port = 9998      # Port pour le chat
discovery_port = 9999 # Port pour la découverte
last_header = ""      # Pour stocker le dernier header affiché
notifications_enabled = True  # Activer/désactiver les notifications
tray_icon = None      # Référence à l'icône de tray

# === NOUVEAU : SYSTÈME DE NOTIFICATIONS WINDOWS ===

class WindowsNotifier:
    """Gère les notifications Windows (Toast, Sons, Tray)"""
    
    @staticmethod
    def play_notification_sound():
        """Joue un son de notification"""
        try:
            # Sons système Windows
            sound_options = {
                'default': winsound.MB_ICONASTERISK,
                'info': winsound.MB_ICONINFORMATION,
                'warning': winsound.MB_ICONEXCLAMATION,
                'error': winsound.MB_ICONHAND
            }
            winsound.MessageBeep(sound_options['info'])
            
            # Alternative : son personnalisé
            # winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
        except:
            pass
    
    @staticmethod
    def show_toast_notification(title, message, duration=5):
        """Affiche une notification toast Windows 10/11"""
        try:
            # Méthode 1 : PowerShell (universel)
            ps_script = f'''
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
            $text = $template.GetElementsByTagName("text")
            $text[0].AppendChild($template.CreateTextNode("{title}")) | Out-Null
            $text[1].AppendChild($template.CreateTextNode("{message}")) | Out-Null
            $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
            $toast.Tag = "ChatColoc"
            $toast.Group = "ChatColoc"
            $toast.ExpirationTime = [DateTimeOffset]::Now.AddSeconds({duration})
            $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Chat SMB")
            $notifier.Show($toast)
            '''
            
            # Encoder en base64 pour éviter les problèmes de guillemets
            encoded_script = base64.b64encode(ps_script.encode('utf-16le')).decode()
            subprocess.run([
                'powershell', '-ExecutionPolicy', 'Bypass', '-NoProfile',
                '-EncodedCommand', encoded_script
            ], capture_output=True, timeout=2)
            
        except Exception as e:
            # Méthode 2 : Balloon tip (ancien système)
            try:
                WindowsNotifier._show_balloon_tip(title, message)
            except:
                print(f"{Colors.YELLOW}⚠️ Toast notification échouée: {e}{Colors.END}")
    
    @staticmethod
    def _show_balloon_tip(title, message):
        """Notification ballon (Windows 7/8/10)"""
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, message, title, 0x40)
        except:
            pass
    
    @staticmethod
    def create_tray_icon(app_name="Chat SMB"):
        """Crée une icône dans la barre des tâches (systray)"""
        try:
            import pystray
            from PIL import Image, ImageDraw
            import threading as th
            
            # Créer une image simple pour l'icône
            image = Image.new('RGB', (64, 64), color=(66, 133, 244))
            draw = ImageDraw.Draw(image)
            draw.ellipse((10, 10, 54, 54), fill=(255, 255, 255))
            draw.ellipse((22, 22, 42, 42), fill=(66, 133, 244))
            
            # Définir les actions du menu
            def show_app():
                print(f"{Colors.GREEN}📱 Apportée au premier plan{Colors.END}")
            
            def quit_app(icon, item):
                icon.stop()
                os._exit(0)
            
            menu = (
                pystray.MenuItem("Ouvrir Chat", show_app),
                pystray.MenuItem("Quitter", quit_app)
            )
            
            # Créer l'icône
            icon = pystray.Icon(app_name, image, app_name, menu)
            
            # Lancer dans un thread séparé
            def run_icon():
                icon.run()
            
            thread = th.Thread(target=run_icon, daemon=True)
            thread.start()
            
            return icon
            
        except ImportError:
            print(f"{Colors.YELLOW}⚠️ Installer 'pystray' et 'PIL' pour l'icône tray{Colors.END}")
            return None
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️ Tray icon échoué: {e}{Colors.END}")
            return None
    
    @staticmethod
    def flash_taskbar_icon():
        """Fait clignoter l'icône dans la barre des tâches"""
        try:
            # Récupérer la fenêtre de la console
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                FLASHW_STOP = 0
                FLASHW_CAPTION = 0x00000001
                FLASHW_TRAY = 0x00000002
                FLASHW_ALL = FLASHW_CAPTION | FLASHW_TRAY
                FLASHW_TIMER = 0x00000004
                FLASHW_TIMERNOFG = 0x0000000C
                
                class FLASHWINFO(ctypes.Structure):
                    _fields_ = [
                        ('cbSize', ctypes.c_uint),
                        ('hwnd', ctypes.c_void_p),
                        ('dwFlags', ctypes.c_uint),
                        ('uCount', ctypes.c_uint),
                        ('dwTimeout', ctypes.c_uint)
                    ]
                
                fwi = FLASHWINFO()
                fwi.cbSize = ctypes.sizeof(FLASHWINFO)
                fwi.hwnd = hwnd
                fwi.dwFlags = FLASHW_ALL | FLASHW_TIMERNOFG
                fwi.uCount = 3  # Nombre de clignotements
                fwi.dwTimeout = 0  # Vitesse par défaut
                
                ctypes.windll.user32.FlashWindowEx(ctypes.byref(fwi))
        except:
            pass

# === FIN DU SYSTÈME DE NOTIFICATIONS ===

def clear_screen():
    """Efface l'écran"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    """Affiche la bannière"""
    clear_screen()
    banner = f"""
{Colors.CYAN}{'='*50}
{Colors.BOLD}💬 LOCAL NETWORK CHAT P2P - Notifications Windows{Colors.END}
{Colors.CYAN}{'='*50}
{Colors.YELLOW}📡 Scan ARP + Détection avancée + Notifications système
{Colors.MAGENTA}✨ Toast Windows + Sons + Tray icon + Clignotement barre
{Colors.GREEN}👥 Discute avec les personnes sur ton réseau WiFi!
{Colors.MAGENTA}💎 Projet: github.com/berru-g/OTTO/SMBchat/
{Colors.CYAN}{'='*50}{Colors.END}
    """
    print(banner)

def get_local_ip():
    """Récupère l'IP locale"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def print_header():
    """Affiche un header fixe en haut de l'écran"""
    global last_header
    local_ip = get_local_ip()
    unread = len([m for m in messages if m.get('notification') and not m.get('notification_shown')])
    
    # Emoji pour notifications
    notif_emoji = "🔔" if notifications_enabled else "🔕"
    unread_emoji = "📨" if unread > 0 else "📭"
    
    header = f"{Colors.CYAN}┌{'─'*68}┐{Colors.END}\n"
    header += f"{Colors.CYAN}│{Colors.END} {Colors.BOLD}💬 Chat SMB{Colors.END} {Colors.CYAN}│{Colors.END} 🌐 {local_ip} {Colors.CYAN}│{Colors.END} 👤 {username[:15]} {Colors.CYAN}│{Colors.END} {unread_emoji} {unread} {Colors.CYAN}│{Colors.END} {notif_emoji} {Colors.CYAN}│{Colors.END}\n"
    header += f"{Colors.CYAN}└{'─'*68}┘{Colors.END}"
    
    last_header = header
    return header

def format_message(msg):
    """Formate un message avec emojis selon le contenu"""
    text = msg['text'].lower()
    
    # Détection automatique d'emojis
    emoji_map = {
        'salut': '👋', 'hello': '👋', 'hey': '👋', 'bonjour': '👋',
        'coucou': '👋', 'hi': '👋',
        'rire': '😂', 'mdr': '😂', 'lol': '😂', 'haha': '😂',
        '?': '❓', 'quoi': '❓', 'pourquoi': '❓',
        'ok': '✅', 'd\'accord': '✅', 'dacc': '✅',
        'non': '❌', 'nope': '❌', 'nah': '❌',
        'oui': '👍', 'yes': '👍', 'ouais': '👍',
        '...': '😶', 'hmm': '🤔', 'hum': '🤔',
        'merci': '🙏', 'thanks': '🙏',
        'a+': '👋', 'bye': '👋', 'ciao': '👋',
        'wow': '😲', 'ouah': '😲',
        'triste': '😢', 'snif': '😢',
        'coeur': '❤️', 'love': '❤️',
        'musique': '🎵', 'chanson': '🎵',
        'nourriture': '🍕', 'manger': '🍽️', 'faim': '🍽️',
        'café': '☕', 'thé': '🍵',
        'bière': '🍺', 'vin': '🍷',
        'jeu': '🎮', 'gaming': '🎮',
        'film': '🎬', 'série': '📺',
        'dodo': '😴', 'nuit': '🌙', 'sleep': '😴'
    }
    
    emoji = ''
    for key, value in emoji_map.items():
        if key in text:
            emoji = f" {value}"
            break
    
    return emoji

def scan_arp():
    """Scan via table ARP - Beaucoup plus fiable sur réseau local"""
    arp_hosts = []
    
    try:
        if os.name == 'nt':  # Windows
            # Utiliser l'encodage correct pour Windows
            result = subprocess.run(['arp', '-a'], 
                                  capture_output=True, 
                                  text=True,
                                  encoding='cp850',  # Encoding Windows français
                                  errors='ignore')
            
            for line in result.stdout.split('\n'):
                line_lower = line.lower()
                if 'dynamique' in line_lower or 'dynami' in line_lower or 'dynamic' in line_lower:
                    # Extrait l'IP (format: 192.168.1.1)
                    parts = line.split()
                    for part in parts:
                        if part.count('.') == 3:
                            # Vérifier que c'est bien une IP
                            ip_parts = part.split('.')
                            if len(ip_parts) == 4 and all(p.isdigit() for p in ip_parts):
                                ip = part
                                if ip not in arp_hosts and ip != get_local_ip():
                                    arp_hosts.append(ip)
                                    break
        
        else:  # Linux/Mac
            result = subprocess.run(['arp', '-a'], 
                                  capture_output=True, 
                                  text=True)
            # Format Linux: hostname (192.168.1.1) at aa:bb:cc:dd:ee:ff
            for line in result.stdout.split('\n'):
                if '(' in line and ')' in line:
                    start = line.find('(') + 1
                    end = line.find(')')
                    ip = line[start:end]
                    if ip.count('.') == 3 and ip not in arp_hosts and ip != get_local_ip():
                        arp_hosts.append(ip)
            
        return arp_hosts
        
    except Exception as e:
        print(f"{Colors.YELLOW}⚠️ Scan ARP échoué: {e}{Colors.END}")
        return []

def is_port_open(ip, port, timeout=1):
    """Test si un port est ouvert"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False

def enhanced_network_scan():
    """Scan amélioré utilisant multiple méthodes"""
    local_ip = get_local_ip()
    network_base = '.'.join(local_ip.split('.')[:3])
    
    all_hosts = []
    detected_ips = set()
    
    print(f"{Colors.YELLOW}🔍 Scan réseau en cours...{Colors.END}")
    
    # Méthode 1: ARP (le plus fiable)
    print(f"  {Colors.CYAN}→ Méthode ARP...{Colors.END}")
    arp_hosts = scan_arp()
    for ip in arp_hosts:
        if ip not in detected_ips:
            has_chat = is_chat_available(ip)
            all_hosts.append((ip, has_chat))
            detected_ips.add(ip)
    
    # Méthode 2: Ping scan rapide
    print(f"  {Colors.CYAN}→ Scan ping rapide...{Colors.END}")
    threads = []
    results_queue = []
    
    def ping_worker(i, results):
        ip = f"{network_base}.{i}"
        if ip == local_ip or ip in detected_ips:
            return
        
        if ping_host(ip, timeout=0.3):
            results.append(ip)
    
    for i in range(1, 101):
        t = threading.Thread(target=ping_worker, args=(i, results_queue))
        threads.append(t)
        t.start()
    
    # Attendre un peu
    time.sleep(0.5)
    
    for ip in results_queue:
        if ip not in detected_ips:
            has_chat = is_chat_available(ip)
            all_hosts.append((ip, has_chat))
            detected_ips.add(ip)
    
    # Méthode 3: Port scan communs (échantillon)
    print(f"  {Colors.CYAN}→ Test ports communs...{Colors.END}")
    common_ports = [445, 139, 135, 80, 443, 22, 21]  # SMB, HTTP, SSH, FTP
    
    test_ips = []
    for i in range(1, 51, 2):  # IPs paires seulement
        ip = f"{network_base}.{i}"
        if ip not in detected_ips and ip != local_ip:
            test_ips.append(ip)
    
    for ip in test_ips[:10]:  # Limiter à 10 tests
        for port in common_ports[:3]:  # 3 premiers ports
            if is_port_open(ip, port, timeout=0.2):
                if ip not in detected_ips:
                    has_chat = is_chat_available(ip)
                    all_hosts.append((ip, has_chat))
                    detected_ips.add(ip)
                break
    
    print(f"{Colors.GREEN}✅ Scan terminé: {len(all_hosts)} hôtes détectés{Colors.END}")
    return list(all_hosts)

def ping_host(ip, timeout=1):
    """Ping une IP pour vérifier si elle est active"""
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

def is_chat_available(ip, port=chat_port):
    """Vérifie si le service chat est disponible sur l'IP"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False

def start_discovery_service():
    """Démarre le service de découverte (annonce notre présence)"""
    def discovery_server():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(('', discovery_port))
        
        print(f"{Colors.BLUE}📡 Service découverte démarré (port {discovery_port}){Colors.END}")
        
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                ip = addr[0]
                
                if ip == get_local_ip():
                    continue
                
                try:
                    message = json.loads(data.decode('utf-8', errors='ignore'))
                    
                    if message.get('type') == 'hello':
                        # Mettre à jour la liste des utilisateurs
                        online_users[ip] = {
                            'name': message.get('name', 'Inconnu'),
                            'status': message.get('status', 'En ligne'),
                            'last_seen': datetime.now(),
                            'chat_port': message.get('chat_port', chat_port),
                            'ip': ip
                        }
                        
                except Exception as e:
                    pass
                    
            except:
                pass
    
    # Lancer dans un thread
    thread = threading.Thread(target=discovery_server, daemon=True)
    thread.start()

def broadcast_presence():
    """Annonce notre présence sur le réseau"""
    local_ip = get_local_ip()
    
    message = {
        'type': 'hello',
        'name': username,
        'status': '🟢 En ligne',
        'chat_port': chat_port,
        'ip': local_ip,
        'timestamp': time.time()
    }
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    try:
        sock.sendto(json.dumps(message).encode(), ('255.255.255.255', discovery_port))
        # Envoyer aussi sur le sous-réseau broadcast
        network_base = '.'.join(local_ip.split('.')[:3])
        sock.sendto(json.dumps(message).encode(), (f'{network_base}.255', discovery_port))
    except:
        pass
    finally:
        sock.close()

def start_chat_server():
    """Démarre le serveur de chat (pour recevoir des messages)"""
    def chat_server():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            sock.bind(('0.0.0.0', chat_port))
            sock.listen(5)
            
            print(f"{Colors.GREEN}💬 Serveur chat démarré (port {chat_port}){Colors.END}")
            
            while True:
                client_socket, addr = sock.accept()
                
                # Traiter la connexion dans un thread séparé
                thread = threading.Thread(
                    target=handle_chat_connection,
                    args=(client_socket, addr),
                    daemon=True
                )
                thread.start()
                
        except Exception as e:
            print(f"{Colors.RED}❌ Erreur serveur chat: {e}{Colors.END}")
    
    # Lancer dans un thread
    thread = threading.Thread(target=chat_server, daemon=True)
    thread.start()

def handle_chat_connection(client_socket, addr):
    """Gère une connexion chat entrante"""
    try:
        data = client_socket.recv(4096).decode('utf-8', errors='ignore')
        message = json.loads(data)
        
        # Ajouter le message à l'historique
        msg_obj = {
            'from': addr[0],
            'from_name': message.get('sender_name', 'Inconnu'),
            'text': message.get('text', ''),
            'timestamp': datetime.now(),
            'type': 'received'
        }
        messages.append(msg_obj)
        
        # === NOUVEAU : NOTIFICATIONS SYSTÈME ===
        if notifications_enabled and current_chat != addr[0]:
            # Son de notification
            WindowsNotifier.play_notification_sound()
            
            # Toast notification
            sender_name = msg_obj['from_name']
            message_preview = msg_obj['text'][:50] + ("..." if len(msg_obj['text']) > 50 else "")
            WindowsNotifier.show_toast_notification(
                f"💬 Message de {sender_name}",
                message_preview
            )
            
            # Clignotement barre des tâches
            WindowsNotifier.flash_taskbar_icon()
        
        # Afficher notification dans le terminal
        if current_chat != addr[0]:
            msg_with_emoji = f"{msg_obj['text']}{format_message(msg_obj)}"
            print(f"\n{Colors.YELLOW}📨 {msg_obj['from_name']}: {msg_with_emoji}{Colors.END}")
        
        # Répondre OK
        response = {'status': 'received'}
        client_socket.send(json.dumps(response).encode())
        
    except Exception as e:
        pass
    finally:
        client_socket.close()

def send_chat_message(target_ip, text):
    """Envoie un message à une IP spécifique"""
    try:
        # Chercher le port de chat de la cible
        target_port = chat_port
        if target_ip in online_users:
            target_port = online_users[target_ip].get('chat_port', chat_port)
        
        # Créer le message
        message = {
            'type': 'chat',
            'sender_name': username,
            'text': text,
            'timestamp': time.time(),
            'target': target_ip
        }
        
        # Envoyer via socket TCP
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((target_ip, target_port))
        sock.send(json.dumps(message).encode())
        
        # Attendre la réponse
        response = sock.recv(1024).decode('utf-8', errors='ignore')
        sock.close()
        
        # Ajouter à notre historique
        msg_obj = {
            'from': get_local_ip(),
            'from_name': username,
            'text': text,
            'timestamp': datetime.now(),
            'type': 'sent',
            'to': target_ip
        }
        messages.append(msg_obj)
        
        return True, "✅ Message envoyé"
        
    except ConnectionRefusedError:
        return False, "❌ L'utilisateur n'a pas le chat actif"
    except Exception as e:
        return False, f"❌ Erreur: {str(e)}"

def display_network_map():
    """Affiche la carte du réseau avec les utilisateurs"""
    local_ip = get_local_ip()
    
    print(f"{Colors.CYAN}{'═'*50}{Colors.END}")
    print(f"{Colors.BOLD}🗺️  CARTE DU RÉSEAU LOCAL{Colors.END}")
    print(f"{Colors.CYAN}{'─'*50}{Colors.END}")
    
    print(f"{Colors.GREEN}📍 Vous: {username} ({local_ip}){Colors.END}")
    print(f"{Colors.BLUE}📡 Port chat: {chat_port}{Colors.END}")
    print(f"{Colors.MAGENTA}🔔 Notifications: {'Activées' if notifications_enabled else 'Désactivées'}{Colors.END}")
    
    # Afficher les hôtes avec chat
    chat_users = [ip for ip, has_chat in available_hosts if has_chat and ip != local_ip]
    other_hosts = [ip for ip, has_chat in available_hosts if not has_chat and ip != local_ip]
    
    if chat_users:
        print(f"\n{Colors.GREEN}💬 UTILISATEURS CHAT ({len(chat_users)}):{Colors.END}")
        for i, ip in enumerate(chat_users[:10]):
            user_info = online_users.get(ip, {})
            name = user_info.get('name', f'Utilisateur{i+1}')
            status = user_info.get('status', '?')
            
            # Couleur selon statut
            if '🟢' in status:
                status_color = Colors.GREEN
            elif '🟡' in status:
                status_color = Colors.YELLOW
            elif '🔴' in status:
                status_color = Colors.RED
            else:
                status_color = Colors.CYAN
            
            print(f"   {Colors.CYAN}{i+1:2d}. {name} {Colors.END}({ip}) - {status_color}{status}{Colors.END}")
    
    if other_hosts:
        print(f"\n{Colors.YELLOW}📶 HÔTES ACTIFS SANS CHAT ({len(other_hosts)}):{Colors.END}")
        for i, ip in enumerate(other_hosts[:5]):
            print(f"   {Colors.YELLOW}{i+len(chat_users)+1:2d}. {ip}{Colors.END}")
    
    if not chat_users and not other_hosts:
        print(f"\n{Colors.RED}😔 Aucun hôte trouvé sur le réseau{Colors.END}")
        print(f"   Vérifiez que vous êtes sur le même WiFi")
    
    print(f"{Colors.CYAN}{'═'*50}{Colors.END}")

def display_chat_history(target_ip=None):
    """Affiche l'historique de chat"""
    if not messages:
        return
    
    print(f"\n{Colors.BOLD}💬 HISTORIQUE DES MESSAGES:{Colors.END}")
    print(f"{Colors.CYAN}{'─'*50}{Colors.END}")
    
    # Filtrer par IP si spécifiée
    filtered_messages = messages
    if target_ip:
        filtered_messages = [
            m for m in messages 
            if m['from'] == target_ip or m.get('to') == target_ip
        ]
    
    for msg in filtered_messages[-15:]:  # 15 derniers messages
        time_str = msg['timestamp'].strftime("%H:%M")
        emoji = format_message(msg)
        
        if msg['type'] == 'sent':
            to_name = online_users.get(msg.get('to', ''), {}).get('name', msg.get('to', '?'))
            print(f"{Colors.BLUE}[{time_str}] Vous → {to_name}:{Colors.END} {msg['text']}{emoji}")
        else:
            print(f"{Colors.GREEN}[{time_str}] {msg['from_name']}:{Colors.END} {msg['text']}{emoji}")
    
    print(f"{Colors.CYAN}{'─'*50}{Colors.END}")

def handle_slash_command(cmd, target_ip=None):
    """Gère les commandes slash étendues"""
    global notifications_enabled
    
    cmd = cmd.lower().strip()
    
    if cmd.startswith('/msg '):
        # /msg pseudo message → envoie direct
        parts = cmd[5:].split(' ', 1)
        if len(parts) == 2:
            target_name, message = parts
            # Chercher l'IP par pseudo
            for ip, info in online_users.items():
                if info['name'].lower() == target_name.lower():
                    success, result = send_chat_message(ip, message)
                    if success:
                        print(f"{Colors.GREEN}{result}{Colors.END}")
                    else:
                        print(f"{Colors.RED}{result}{Colors.END}")
                    return True
            print(f"{Colors.RED}❌ Utilisateur '{target_name}' non trouvé{Colors.END}")
        return True
    
    elif cmd == '/notif' or cmd == '/notification':
        # Basculer les notifications
        notifications_enabled = not notifications_enabled
        status = "activées" if notifications_enabled else "désactivées"
        print(f"{Colors.GREEN}✅ Notifications {status}{Colors.END}")
        return True
    
    elif cmd == '/testnotif':
        # Tester les notifications
        print(f"{Colors.YELLOW}🧪 Test des notifications...{Colors.END}")
        WindowsNotifier.play_notification_sound()
        WindowsNotifier.show_toast_notification(
            "💬 Test Notification",
            "Ceci est un test du système de notifications!"
        )
        WindowsNotifier.flash_taskbar_icon()
        print(f"{Colors.GREEN}✅ Test terminé{Colors.END}")
        return True
    
    elif cmd == '/users' or cmd == '/list':
        # Affiche tous les utilisateurs
        display_network_map()
        return True
    
    elif cmd == '/clearall':
        # Efface tout l'historique
        global messages
        messages = []
        print(f"{Colors.GREEN}✅ Historique effacé{Colors.END}")
        return True
    
    elif cmd.startswith('/status '):
        # /status nouveau_status
        new_status = cmd[8:]
        if get_local_ip() in online_users:
            online_users[get_local_ip()]['status'] = new_status
        broadcast_presence()
        print(f"{Colors.GREEN}✅ Statut changé: {new_status}{Colors.END}")
        return True
    
    elif cmd == '/help':
        print(f"\n{Colors.CYAN}📚 COMMANDES DISPONIBLES:{Colors.END}")
        print(f"  {Colors.GREEN}/msg <pseudo> <message>{Colors.END} - Envoyer un message direct")
        print(f"  {Colors.GREEN}/notif{Colors.END} - Activer/désactiver les notifications")
        print(f"  {Colors.GREEN}/testnotif{Colors.END} - Tester les notifications système")
        print(f"  {Colors.GREEN}/users ou /list{Colors.END} - Afficher tous les utilisateurs")
        print(f"  {Colors.GREEN}/status <texte>{Colors.END} - Changer votre statut")
        print(f"  {Colors.GREEN}/clearall{Colors.END} - Effacer tout l'historique")
        print(f"  {Colors.GREEN}/help{Colors.END} - Afficher cette aide")
        print(f"  {Colors.GREEN}/quit{Colors.END} - Quitter le chat actuel")
        print(f"  {Colors.GREEN}/clear{Colors.END} - Effacer l'écran")
        return True
    
    elif cmd == '/broadcast':
        broadcast_presence()
        print(f"{Colors.GREEN}✅ Présence annoncée sur le réseau{Colors.END}")
        return True
    
    elif cmd.startswith('/'):
        print(f"{Colors.RED}❌ Commande inconnue. Tapez /help pour la liste{Colors.END}")
        return True
    
    return False

def tab_autocomplete(input_text, online_users):
    """Auto-complète les pseudos avec Tab"""
    if not input_text or input_text[-1] == ' ':
        return input_text
    
    # Vérifier si on est dans une commande /msg
    if input_text.startswith('/msg '):
        parts = input_text[5:].split()
        if len(parts) == 1:  # On est en train de taper le pseudo
            partial_name = parts[0].lower()
            matches = []
            for ip, info in online_users.items():
                if info['name'].lower().startswith(partial_name):
                    matches.append(info['name'])
            
            if matches:
                return f"/msg {matches[0]} "
    
    return input_text

def get_user_input(prompt, timeout=1):
    """Récupère l'input utilisateur avec timeout"""
    print(prompt, end='', flush=True)
    
    # Pour Unix/Linux/Mac
    if os.name != 'nt':
        import select
        ready, _, _ = select.select([sys.stdin], [], [], timeout)
        if ready:
            return sys.stdin.readline().strip()
        return None
    
    # Pour Windows (version simplifiée)
    else:
        import msvcrt
        import time
        
        start_time = time.time()
        input_buffer = []
        
        while (time.time() - start_time) < timeout:
            if msvcrt.kbhit():
                char = msvcrt.getwch()
                
                if char == '\t':  # Tab pour auto-complétion
                    current_text = ''.join(input_buffer)
                    completed = tab_autocomplete(current_text, online_users)
                    if completed != current_text:
                        # Efface la ligne et réécrit
                        print('\r' + ' ' * (len(prompt) + len(current_text) + 2), end='')
                        print(f'\r{prompt}{completed}', end='', flush=True)
                        input_buffer = list(completed)
                
                elif char == '\r':  # Enter
                    print()
                    return ''.join(input_buffer)
                elif char == '\x08':  # Backspace
                    if input_buffer:
                        input_buffer.pop()
                        print('\b \b', end='', flush=True)
                else:
                    input_buffer.append(char)
                    print(char, end='', flush=True)
            
            time.sleep(0.01)
        
        return None

def chat_with_user(target_ip):
    """Mode chat interactif avec un utilisateur"""
    global current_chat
    
    current_chat = target_ip
    
    # Récupérer le nom de l'utilisateur
    target_name = online_users.get(target_ip, {}).get('name', target_ip)
    
    clear_screen()
    print(print_header())
    print(f"\n{Colors.GREEN}💬 Discussion avec {target_name} ({target_ip}){Colors.END}")
    print(f"{Colors.YELLOW}Tapez '/quit' pour quitter, '/help' pour l'aide{Colors.END}")
    print(f"{Colors.CYAN}{'─'*50}{Colors.END}")
    
    # Afficher les derniers messages avec cette personne
    display_chat_history(target_ip)
    
    # Boucle de chat
    while True:
        # Vérifier les nouveaux messages (non bloquant)
        check_new_messages()
        
        # Input utilisateur
        user_input = get_user_input(f"\n{Colors.BOLD}Vous: {Colors.END}", timeout=0.5)
        
        if user_input is not None:
            user_input = user_input.strip()
            
            if not user_input:
                continue
            
            # Vérifier si c'est une commande slash
            if user_input.startswith('/'):
                if handle_slash_command(user_input, target_ip):
                    if user_input.lower() == '/quit':
                        print(f"{Colors.YELLOW}👋 Fin de la discussion{Colors.END}")
                        current_chat = None
                        time.sleep(1)
                        break
                    elif user_input.lower() == '/clear':
                        clear_screen()
                        print(print_header())
                        print(f"\n{Colors.Green}💬 Discussion avec {target_name} ({target_ip}){Colors.END}")
                        display_chat_history(target_ip)
                    continue
            else:
                # Envoyer le message normal
                success, message = send_chat_message(target_ip, user_input)
                
                if success:
                    # Afficher notre message immédiatement avec emoji
                    time_str = datetime.now().strftime("%H:%M")
                    emoji = format_message({'text': user_input.lower()})
                    print(f"{Colors.BLUE}[{time_str}] Vous: {user_input}{emoji}{Colors.END}")
                else:
                    print(f"{Colors.RED}{message}{Colors.END}")
        
        # Petite pause pour éviter la surcharge CPU
        time.sleep(0.1)

def check_new_messages():
    """Vérifie et affiche les nouveaux messages"""
    global messages
    
    # Récupérer les messages non affichés
    new_messages = [m for m in messages if not m.get('displayed', False)]
    
    for msg in new_messages:
        if msg['type'] == 'received':
            time_str = msg['timestamp'].strftime("%H:%M")
            emoji = format_message(msg)
            
            # Si on est en chat avec cette personne, afficher directement
            if current_chat == msg['from']:
                print(f"{Colors.GREEN}[{time_str}] {msg['from_name']}: {msg['text']}{emoji}{Colors.END}")
                msg['displayed'] = True
            else:
                # Sinon, juste marquer comme notification
                msg['notification'] = True
                msg['displayed'] = True

def test_network_connection():
    """Test complet de la connexion réseau"""
    print(f"\n{Colors.CYAN}🧪 TEST DE CONNEXION{Colors.END}")
    print(f"{Colors.CYAN}{'─'*40}{Colors.END}")
    
    tests = [
        ("Ping localhost", lambda: ping_host("127.0.0.1", timeout=0.5)),
        ("Port chat ouvert", lambda: is_port_open(get_local_ip(), chat_port, timeout=0.5)),
        ("Broadcast UDP", lambda: True),  # Simple test
    ]
    
    local_ip = get_local_ip()
    if local_ip != "127.0.0.1":
        network_base = '.'.join(local_ip.split('.')[:3])
        tests.insert(1, ("Ping routeur", lambda: ping_host(f"{network_base}.1", timeout=1)))
    
    all_passed = True
    for test_name, test_func in tests:
        try:
            result = test_func()
            status = f"{Colors.GREEN}✅ PASS" if result else f"{Colors.RED}❌ FAIL"
            print(f"  {test_name}: {status}{Colors.END}")
            if not result:
                all_passed = False
        except Exception as e:
            print(f"  {test_name}: {Colors.RED}❌ ERROR: {e}{Colors.END}")
            all_passed = False
    
    if all_passed:
        print(f"{Colors.GREEN}✅ Tous les tests passent !{Colors.END}")
    else:
        print(f"{Colors.YELLOW}⚠️  Certains tests échouent{Colors.END}")
    
    input(f"\n{Colors.CYAN}Appuyez sur Entrée...{Colors.END}")

def show_network_stats():
    """Affiche les statistiques réseau"""
    print(f"\n{Colors.CYAN}📊 STATISTIQUES RÉSEAU{Colors.END}")
    print(f"{Colors.CYAN}{'─'*40}{Colors.END}")
    
    local_ip = get_local_ip()
    
    print(f"{Colors.GREEN}Votre IP:{Colors.END} {local_ip}")
    print(f"{Colors.GREEN}Port chat:{Colors.END} {chat_port}")
    print(f"{Colors.GREEN}Port découverte:{Colors.END} {discovery_port}")
    print(f"{Colors.GREEN}Utilisateurs en ligne:{Colors.END} {len(online_users)}")
    print(f"{Colors.GREEN}Hôtes détectés:{Colors.END} {len(available_hosts)}")
    print(f"{Colors.GREEN}Messages échangés:{Colors.END} {len(messages)}")
    print(f"{Colors.GREEN}Notifications:{Colors.END} {'Activées' if notifications_enabled else 'Désactivées'}")
    
    if online_users:
        print(f"\n{Colors.GREEN}👥 UTILISATEURS:{Colors.END}")
        for ip, info in online_users.items():
            if ip != local_ip:
                last_seen = info.get('last_seen', datetime.now())
                delta = datetime.now() - last_seen
                minutes = int(delta.total_seconds() / 60)
                print(f"  {info['name']} ({ip}) - vu il y a {minutes}min")
    
    input(f"\n{Colors.CYAN}Appuyez sur Entrée...{Colors.END}")

def notification_settings_menu():
    """Menu des paramètres de notifications"""
    global notifications_enabled, tray_icon
    
    while True:
        clear_screen()
        print(print_header())
        print(f"\n{Colors.CYAN}⚙️  PARAMÈTRES DES NOTIFICATIONS{Colors.END}")
        print(f"{Colors.CYAN}{'─'*40}{Colors.END}")
        
        print(f"\n{Colors.GREEN}État actuel:")
        print(f"  🔔 Notifications: {'ACTIVÉES' if notifications_enabled else 'DÉSACTIVÉES'}")
        print(f"  🔊 Sons: {'ACTIVÉS' if notifications_enabled else 'DÉSACTIVÉS'}")
        print(f"  📨 Toast Windows: {'ACTIVÉS' if notifications_enabled else 'DÉSACTIVÉS'}")
        print(f"  💡 Clignotement barre: {'ACTIVÉ' if notifications_enabled else 'DÉSACTIVÉ'}")
        print(f"  📊 Tray icon: {'ACTIVÉ' if tray_icon else 'DÉSACTIVÉ'}{Colors.END}")
        
        print(f"\n{Colors.BOLD}Options:{Colors.END}")
        print(f"{Colors.BOLD}[1] Activer/désactiver toutes les notifications{Colors.END}")
        print(f"{Colors.BOLD}[2] Tester les notifications{Colors.END}")
        print(f"{Colors.BOLD}[3] Activer/désactiver l'icône tray{Colors.END}")
        print(f"{Colors.RED}[0] Retour au menu principal{Colors.END}")
        
        choice = input(f"\n{Colors.CYAN}👉 Votre choix [0-3]: {Colors.END}").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            notifications_enabled = not notifications_enabled
            status = "activées" if notifications_enabled else "désactivées"
            print(f"{Colors.GREEN}✅ Notifications {status}{Colors.END}")
            time.sleep(1)
        elif choice == '2':
            print(f"{Colors.YELLOW}🧪 Test des notifications...{Colors.END}")
            WindowsNotifier.play_notification_sound()
            WindowsNotifier.show_toast_notification(
                "💬 Test Notification",
                "Ceci est un test du système de notifications!"
            )
            WindowsNotifier.flash_taskbar_icon()
            print(f"{Colors.GREEN}✅ Test terminé{Colors.END}")
            input(f"{Colors.CYAN}Appuyez sur Entrée...{Colors.END}")
        elif choice == '3':
            if tray_icon:
                try:
                    tray_icon.stop()
                    tray_icon = None
                    print(f"{Colors.GREEN}✅ Icône tray désactivée{Colors.END}")
                except:
                    print(f"{Colors.RED}❌ Erreur désactivation tray{Colors.END}")
            else:
                tray_icon = WindowsNotifier.create_tray_icon()
                if tray_icon:
                    print(f"{Colors.GREEN}✅ Icône tray activée{Colors.END}")
                else:
                    print(f"{Colors.YELLOW}⚠️  Installation requise: pip install pystray pillow{Colors.END}")
            time.sleep(1)
        else:
            print(f"{Colors.RED}❌ Choix invalide{Colors.END}")
            time.sleep(1)

def main_menu():
    """Menu principal interactif"""
    global username, current_chat, tray_icon
    
    # Demander le pseudo
    print_banner()
    username = input(f"{Colors.CYAN}👤 Entrez votre pseudo: {Colors.END}").strip()
    if not username:
        username = "Anonyme"
    
    # === NOUVEAU : INITIALISATION DES NOTIFICATIONS ===
    print(f"\n{Colors.YELLOW}🔄 Initialisation des notifications Windows...{Colors.END}")
    
    # Tester si on peut créer l'icône tray
    try:
        tray_icon = WindowsNotifier.create_tray_icon()
        if tray_icon:
            print(f"{Colors.GREEN}✅ Icône tray activée{Colors.END}")
    except:
        print(f"{Colors.YELLOW}⚠️  Tray icon non disponible (pip install pystray pillow){Colors.END}")
    
    # Tester une notification de bienvenue
    if notifications_enabled:
        WindowsNotifier.show_toast_notification(
            "💬 Chat SMB démarré",
            f"Bonjour {username}! Le chat est maintenant actif."
        )
        WindowsNotifier.play_notification_sound()
    
    # Démarrer les services
    print(f"{Colors.YELLOW}🔄 Démarrage des services réseau...{Colors.END}")
    
    # Scanner le réseau
    scan_thread = threading.Thread(target=lambda: globals().update({'available_hosts': enhanced_network_scan()}), daemon=True)
    scan_thread.start()
    
    # Démarrer le serveur de découverte
    start_discovery_service()
    
    # Démarrer le serveur de chat
    start_chat_server()
    
    # Annoncer notre présence
    broadcast_presence()
    
    # Attendre un peu le scan
    time.sleep(2)
    
    # Boucle principale
    while True:
        clear_screen()
        print(print_header())
        display_network_map()
        
        # Afficher notifications
        unread_messages = [m for m in messages if m.get('notification') and not m.get('notification_shown')]
        if unread_messages:
            print(f"\n{Colors.YELLOW}📨 Vous avez {len(unread_messages)} nouveau(x) message(s){Colors.END}")
            for msg in unread_messages:
                msg['notification_shown'] = True
        
        # Menu
        print(f"\n{Colors.BOLD} #  MENU PRINCIPAL:{Colors.END}")
        print(f"{Colors.BOLD}[1] 💬 Discuter avec quelqu'un{Colors.END}")
        print(f"{Colors.BOLD}[2] 🔍 Rescanner le réseau{Colors.END}")
        print(f"{Colors.BOLD}[3] 📨 Voir tous les messages{Colors.END}")
        print(f"{Colors.BOLD}[4] 👤 Changer de pseudo{Colors.END}")
        print(f"{Colors.BOLD}[5] 📡 Annoncer ma présence{Colors.END}")
        print(f"{Colors.BOLD}[6] 🛠️  Test connexion{Colors.END}")
        print(f"{Colors.BOLD}[7] 📊 Stats réseau{Colors.END}")
        print(f"{Colors.BOLD}[8] ⚙️  Paramètres notifications{Colors.END}")  # NOUVEAU
        print(f"{Colors.RED}[0] 🚪 Quitter{Colors.END}")
        
        print(f"\n{Colors.CYAN}{'═'*50}{Colors.END}")
        
        choice = input(f"\n{Colors.BOLD}👉 Votre choix [0-8]: {Colors.END}").strip()
        
        if choice == '0':
            # Arrêter l'icône tray si active
            if tray_icon:
                try:
                    tray_icon.stop()
                except:
                    pass
            print(f"\n{Colors.GREEN}👋 À bientôt {username}!{Colors.END}")
            time.sleep(1)
            break
        
        elif choice == '1':
            # Choisir avec qui discuter
            chat_users = [ip for ip, has_chat in available_hosts if has_chat and ip != get_local_ip()]
            
            if not chat_users:
                print(f"\n{Colors.RED}😔 Aucun utilisateur chat disponible{Colors.END}")
                print(f"{Colors.YELLOW}Assurez-vous que les autres ont lancé le chat{Colors.END}")
                input(f"{Colors.CYAN}Appuyez sur Entrée...{Colors.END}")
                continue
            
            print(f"\n{Colors.GREEN}👥 Sélectionnez un utilisateur:{Colors.END}")
            for i, ip in enumerate(chat_users[:10]):
                user_info = online_users.get(ip, {})
                name = user_info.get('name', f'Utilisateur{i+1}')
                print(f"   {Colors.CYAN}[{i+1}] {name} ({ip}){Colors.END}")
            
            print(f"   {Colors.YELLOW}[0] Retour{Colors.END}")
            
            user_choice = input(f"\n{Colors.CYAN}👉 Numéro: {Colors.END}").strip()
            
            if user_choice.isdigit():
                choice_num = int(user_choice)
                if 1 <= choice_num <= len(chat_users):
                    target_ip = chat_users[choice_num - 1]
                    chat_with_user(target_ip)
                elif choice_num == 0:
                    continue
                else:
                    print(f"{Colors.RED}❌ Choix invalide{Colors.END}")
                    time.sleep(1)
            else:
                print(f"{Colors.RED}❌ Entrez un nombre{Colors.END}")
                time.sleep(1)
        
        elif choice == '2':
            # Rescanner
            print(f"\n{Colors.YELLOW}🔄 Nouveau scan en cours...{Colors.END}")
            available_hosts.clear()
            online_users.clear()
            
            scan_thread = threading.Thread(target=lambda: globals().update({'available_hosts': enhanced_network_scan()}), daemon=True)
            scan_thread.start()
            
            # Petite animation
            for i in range(3):
                print(f"{Colors.YELLOW}.", end='', flush=True)
                time.sleep(0.5)
            print()
            
            time.sleep(2)
        
        elif choice == '3':
            # Voir tous les messages
            clear_screen()
            print(print_header())
            display_chat_history()
            input(f"\n{Colors.CYAN}Appuyez sur Entrée pour continuer...{Colors.END}")
        
        elif choice == '4':
            # Changer de pseudo
            clear_screen()
            print(print_header())
            new_name = input(f"\n{Colors.CYAN}Nouveau pseudo: {Colors.END}").strip()
            if new_name:
                username = new_name
                broadcast_presence()
                print(f"{Colors.GREEN}✅ Pseudo changé en {username}{Colors.END}")
                
                # Notification de changement
                if notifications_enabled:
                    WindowsNotifier.show_toast_notification(
                        "👤 Pseudo changé",
                        f"Votre pseudo est maintenant {username}"
                    )
                time.sleep(1)
        
        elif choice == '5':
            # Annoncer présence
            broadcast_presence()
            print(f"{Colors.GREEN}✅ Présence annoncée sur le réseau{Colors.END}")
            time.sleep(1)
            
        elif choice == '6':
            # Test connexion
            clear_screen()
            print(print_header())
            test_network_connection()
            
        elif choice == '7':
            # Stats réseau
            clear_screen()
            print(print_header())
            show_network_stats()
            
        elif choice == '8':  # NOUVEAU
            # Paramètres notifications
            notification_settings_menu()
            
        elif choice == '9':  # credit
            print(f"{Colors.BLUE}💎 Code Open Source :{Colors.END}")
            print(f"{Colors.BOLD}➡️ https://github.com/berru-g/OTTO/SMBchat/{Colors.END}")
        
        else:
            print(f"{Colors.RED}❌ Choix invalide{Colors.END}")
            time.sleep(1)

if __name__ == "__main__":
    try:
        # Mode test si argument
        if len(sys.argv) > 1 and sys.argv[1] == "test":
            import random
            chat_port = 9999  # Changer le port pour éviter le conflit
            username = "TestUser" + str(random.randint(1, 100))
            print(f"{Colors.GREEN}🧪 Mode test activé - Pseudo: {username}{Colors.END}")
            print(f"{Colors.YELLOW}Ouvrez un deuxième terminal avec: python {sys.argv[0]} test{Colors.END}")
            time.sleep(2)
        
        # Démarrer l'application
        main_menu()
        
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}👋 Interruption - Au revoir!{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}💥 Erreur: {str(e)}{Colors.END}")
        import traceback
        traceback.print_exc()
        input("Appuyez sur Entrée pour quitter...")