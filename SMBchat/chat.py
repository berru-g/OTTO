#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LOCAL NETWORK CHAT WITH SMB protocol - Chat en réseau local avec scan automatique
Basé sur transfert_SMB.py mais pour le chat P2P
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

def clear_screen():
    """Efface l'écran"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    """Affiche la bannière"""
    clear_screen()
    banner = f"""
{Colors.CYAN}{'='*70}
{Colors.BOLD}💬 LOCAL NETWORK CHAT SMB - Chat Local P2P{Colors.END}
{Colors.CYAN}{'='*70}
{Colors.YELLOW}📡 Scan réseau automatique + Chat en temps réel
{Colors.MAGENTA}✨ Basé sur le protocol SMB 
{Colors.GREEN}👥 Discute avec les personnes sur ton réseau WiFi!
{Colors.MAGENTA}💎 Projet open source github.com/berru-g/OTTO/SMBchat/
{Colors.CYAN}{'='*70}{Colors.END}
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

def scan_network_async():
    """Scan le réseau en arrière-plan"""
    global available_hosts
    
    local_ip = get_local_ip()
    network_base = '.'.join(local_ip.split('.')[:3])
    
    print(f"{Colors.YELLOW}🔍 Scan du réseau {network_base}.0/24...{Colors.END}")
    
    hosts = []
    
    # Scanner les 100 premières IPs
    for i in range(1, 101):
        ip = f"{network_base}.{i}"
        if ip == local_ip:
            continue
            
        # Vérifier si l'hôte est actif (ping rapide)
        if ping_host(ip):
            # Vérifier si le chat est disponible (port 9998)
            if is_chat_available(ip):
                hosts.append((ip, True))  # (ip, chat_available)
            else:
                hosts.append((ip, False))
    
    available_hosts = hosts
    print(f"{Colors.GREEN}✅ Scan terminé: {len(hosts)} hôtes trouvés{Colors.END}")
    time.sleep(1)

def ping_host(ip, timeout=1):
    """Ping une IP pour vérifier si elle est active"""
    try:
        param = '-n' if os.name == 'nt' else '-c'
        timeout_str = '1000' if os.name == 'nt' else '1'
        
        command = ['ping', param, '1', '-w', timeout_str, ip]
        
        with subprocess.Popen(command, stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE) as proc:
            out, _ = proc.communicate(timeout=timeout)
        
        return proc.returncode == 0
    except:
        return False

def is_chat_available(ip, port=chat_port):
    """Vérifie si le service chat est disponible sur l'IP"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
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
                    message = json.loads(data.decode())
                    
                    if message.get('type') == 'hello':
                        # Mettre à jour la liste des utilisateurs
                        online_users[ip] = {
                            'name': message.get('name', 'Inconnu'),
                            'status': message.get('status', 'En ligne'),
                            'last_seen': datetime.now(),
                            'chat_port': message.get('chat_port', chat_port)
                        }
                        
                except:
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
        'status': 'Disponible',
        'chat_port': chat_port,
        'ip': local_ip,
        'timestamp': time.time()
    }
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    try:
        sock.sendto(json.dumps(message).encode(), ('255.255.255.255', discovery_port))
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
        data = client_socket.recv(4096).decode()
        message = json.loads(data)
        
        # Ajouter le message à l'historique
        messages.append({
            'from': addr[0],
            'from_name': message.get('sender_name', 'Inconnu'),
            'text': message.get('text', ''),
            'timestamp': datetime.now(),
            'type': 'received'
        })
        
        # Afficher notification si on est pas en train de chatter avec cette personne
        if current_chat != addr[0]:
            print(f"\n{Colors.YELLOW}📨 Nouveau message de {message.get('sender_name', addr[0])}{Colors.END}")
        
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
        response = sock.recv(1024).decode()
        sock.close()
        
        # Ajouter à notre historique
        messages.append({
            'from': get_local_ip(),
            'from_name': username,
            'text': text,
            'timestamp': datetime.now(),
            'type': 'sent',
            'to': target_ip
        })
        
        return True, "Message envoyé"
        
    except ConnectionRefusedError:
        return False, "L'utilisateur n'a pas le chat actif"
    except Exception as e:
        return False, f"Erreur: {str(e)}"

def display_network_map():
    """Affiche la carte du réseau avec les utilisateurs"""
    local_ip = get_local_ip()
    
    print(f"{Colors.CYAN}{'═'*70}{Colors.END}")
    print(f"{Colors.BOLD}🗺️  CARTE DU RÉSEAU LOCAL{Colors.END}")
    print(f"{Colors.CYAN}{'─'*70}{Colors.END}")
    
    print(f"{Colors.GREEN}📍 Vous: {username} ({local_ip}){Colors.END}")
    print(f"{Colors.BLUE}📡 Port chat: {chat_port}{Colors.END}")
    
    # Afficher les hôtes avec chat
    chat_users = [ip for ip, has_chat in available_hosts if has_chat and ip != local_ip]
    other_hosts = [ip for ip, has_chat in available_hosts if not has_chat and ip != local_ip]
    
    if chat_users:
        print(f"\n{Colors.GREEN}💬 UTILISATEURS CHAT ({len(chat_users)}):{Colors.END}")
        for i, ip in enumerate(chat_users[:10]):  # Limiter à 10 affichages
            user_info = online_users.get(ip, {})
            name = user_info.get('name', f'Utilisateur{i+1}')
            status = user_info.get('status', '?')
            
            status_color = Colors.GREEN if status == 'En ligne' else Colors.YELLOW
            print(f"   {Colors.CYAN}{i+1:2d}. {name} {Colors.END}({ip}) - {status_color}{status}{Colors.END}")
    
    if other_hosts:
        print(f"\n{Colors.YELLOW}📶 HÔTES ACTIFS SANS CHAT ({len(other_hosts)}):{Colors.END}")
        for i, ip in enumerate(other_hosts[:5]):
            print(f"   {Colors.YELLOW}{i+len(chat_users)+1:2d}. {ip}{Colors.END}")
    
    if not chat_users and not other_hosts:
        print(f"\n{Colors.RED}😔 Aucun hôte trouvé sur le réseau{Colors.END}")
        print(f"   Vérifiez que vous êtes sur le même WiFi")
    
    print(f"{Colors.CYAN}{'═'*70}{Colors.END}")

def display_chat_history(target_ip=None):
    """Affiche l'historique de chat"""
    if not messages:
        return
    
    print(f"\n{Colors.BOLD}💬 HISTORIQUE DES MESSAGES:{Colors.END}")
    print(f"{Colors.CYAN}{'─'*70}{Colors.END}")
    
    # Filtrer par IP si spécifiée
    filtered_messages = messages
    if target_ip:
        filtered_messages = [
            m for m in messages 
            if m['from'] == target_ip or m.get('to') == target_ip
        ]
    
    for msg in filtered_messages[-10:]:  # 10 derniers messages
        time_str = msg['timestamp'].strftime("%H:%M")
        
        if msg['type'] == 'sent':
            print(f"{Colors.BLUE}[{time_str}] Vous → {msg.get('to', '?')}:{Colors.END} {msg['text']}")
        else:
            print(f"{Colors.GREEN}[{time_str}] {msg['from_name']}:{Colors.END} {msg['text']}")
    
    print(f"{Colors.CYAN}{'─'*70}{Colors.END}")

def get_user_input(prompt, timeout=30):
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
                
                if char == '\r':  # Enter
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
    
    print(f"\n{Colors.GREEN}💬 Discussion avec {target_name} ({target_ip}){Colors.END}")
    print(f"{Colors.YELLOW}Tapez '/quit' pour quitter, '/clear' pour effacer{Colors.END}")
    print(f"{Colors.CYAN}{'─'*70}{Colors.END}")
    
    # Afficher les derniers messages avec cette personne
    display_chat_history(target_ip)
    
    # Boucle de chat
    while True:
        # Vérifier les nouveaux messages (non bloquant)
        check_new_messages()
        
        # Input utilisateur
        user_input = get_user_input(f"\n{Colors.BOLD}Vous: {Colors.END}", timeout=1)
        
        if user_input is not None:
            user_input = user_input.strip()
            
            if not user_input:
                continue
            
            # Commandes spéciales
            if user_input.lower() == '/quit':
                print(f"{Colors.YELLOW}👋 Fin de la discussion{Colors.END}")
                current_chat = None
                time.sleep(1)
                break
            
            elif user_input.lower() == '/clear':
                clear_screen()
                print_banner()
                print(f"\n{Colors.GREEN}💬 Discussion avec {target_name} ({target_ip}){Colors.END}")
                display_chat_history(target_ip)
                continue
            
            elif user_input.lower() == '/help':
                print(f"\n{Colors.CYAN}Commandes disponibles:{Colors.END}")
                print(f"  /quit   - Quitter le chat")
                print(f"  /clear  - Effacer l'écran")
                print(f"  /help   - Afficher l'aide")
                print(f"  /status - Voir statut connexion")
                continue
            
            elif user_input.lower() == '/status':
                if ping_host(target_ip):
                    print(f"{Colors.GREEN}✅ {target_ip} est en ligne{Colors.END}")
                else:
                    print(f"{Colors.RED}❌ {target_ip} est hors ligne{Colors.END}")
                continue
            
            # Envoyer le message
            success, message = send_chat_message(target_ip, user_input)
            
            if success:
                # Afficher notre message immédiatement
                time_str = datetime.now().strftime("%H:%M")
                print(f"{Colors.BLUE}[{time_str}] Vous: {user_input}{Colors.END}")
            else:
                print(f"{Colors.RED}❌ {message}{Colors.END}")
        
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
            
            # Si on est en chat avec cette personne, afficher directement
            if current_chat == msg['from']:
                print(f"{Colors.GREEN}[{time_str}] {msg['from_name']}: {msg['text']}{Colors.END}")
            else:
                # Sinon, juste marquer comme notification
                msg['notification'] = True
            
            msg['displayed'] = True

def main_menu():
    """Menu principal interactif"""
    global username, current_chat
    
    # Demander le pseudo
    print_banner()
    username = input(f"{Colors.CYAN}👤 Entrez votre pseudo: {Colors.END}").strip()
    if not username:
        username = "Anonyme"
    
    # Démarrer les services
    print(f"\n{Colors.YELLOW}🔄 Démarrage des services...{Colors.END}")
    
    # Scanner le réseau
    scan_thread = threading.Thread(target=scan_network_async, daemon=True)
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
        print_banner()
        display_network_map()
        
        # Afficher notifications
        unread_messages = [m for m in messages if m.get('notification') and not m.get('notification_shown')]
        if unread_messages:
            print(f"\n{Colors.YELLOW}📨 Vous avez {len(unread_messages)} nouveau(x) message(s){Colors.END}")
            for msg in unread_messages:
                msg['notification_shown'] = True
        
        # Menu
        print(f"\n{Colors.BOLD}🎯 MENU PRINCIPAL:{Colors.END}")
        print(f"{Colors.GREEN}[1] 💬 Discuter avec quelqu'un{Colors.END}")
        print(f"{Colors.BLUE}[2] 🔍 Rescanner le réseau{Colors.END}")
        print(f"{Colors.YELLOW}[3] 📨 Voir tous les messages{Colors.END}")
        print(f"{Colors.MAGENTA}[4] 👤 Changer de pseudo{Colors.END}")
        print(f"{Colors.CYAN}[5] 📡 Annoncer ma présence{Colors.END}")
        print(f"{Colors.RED}[0] 🚪 Quitter{Colors.END}")
        
        print(f"\n{Colors.CYAN}{'═'*70}{Colors.END}")
        
        choice = input(f"\n{Colors.BOLD}👉 Votre choix [0-5]: {Colors.END}").strip()
        
        if choice == '0':
            print(f"\n{Colors.GREEN}👋 À bientôt {username}!{Colors.END}")
            time.sleep(1)
            break
        
        elif choice == '1':
            # Choisir avec qui discuter
            chat_users = [ip for ip, has_chat in available_hosts if has_chat and ip != get_local_ip()]
            
            if not chat_users:
                print(f"\n{Colors.RED}😔 Aucun utilisateur chat disponible{Colors.END}")
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
            
            scan_thread = threading.Thread(target=scan_network_async, daemon=True)
            scan_thread.start()
            
            # Attendre un peu
            for i in range(3):
                print(f"{Colors.YELLOW}.", end='', flush=True)
                time.sleep(0.5)
            print()
            
            time.sleep(2)
        
        elif choice == '3':
            # Voir tous les messages
            print_banner()
            display_chat_history()
            input(f"\n{Colors.CYAN}Appuyez sur Entrée pour continuer...{Colors.END}")
        
        elif choice == '4':
            # Changer de pseudo
            new_name = input(f"\n{Colors.CYAN}Nouveau pseudo: {Colors.END}").strip()
            if new_name:
                username = new_name
                broadcast_presence()
                print(f"{Colors.GREEN}✅ Pseudo changé en {username}{Colors.END}")
                time.sleep(1)
        
        elif choice == '5':
            # Annoncer présence
            broadcast_presence()
            print(f"{Colors.GREEN}✅ Présence annoncée sur le réseau{Colors.END}")
            time.sleep(1)
        
        else:
            print(f"{Colors.RED}❌ Choix invalide{Colors.END}")
            time.sleep(1)

# Fonction pour tester rapidement
def quick_test():
    """Mode test rapide"""
    print(f"{Colors.BOLD}🧪 MODE TEST RAPIDE{Colors.END}")
    print(f"{Colors.YELLOW}Ce mode simule 2 utilisateurs sur la même machine{Colors.END}")
    
    import random
    
    # Créer un deuxième "utilisateur" simulé
    test_ip = "127.0.0.1"
    test_port = chat_port + 1
    
    print(f"\n{Colors.CYAN}Pour tester:{Colors.END}")
    print(f"1. Lancez ce script dans un autre terminal avec:")
    print(f"   {Colors.GREEN}python {sys.argv[0]} test{Colors.END}")
    print(f"2. Utilisez un pseudo différent")
    print(f"3. Essayez de vous envoyer des messages")
    
    input(f"\n{Colors.CYAN}Appuyez sur Entrée pour démarrer le chat normal...{Colors.END}")

if __name__ == "__main__":
    try:
        # Mode test si argument
        if len(sys.argv) > 1 and sys.argv[1] == "test":
            chat_port = 9999  # Changer le port pour éviter le conflit
            username = "TestUser" + str(random.randint(1, 100))
            print(f"{Colors.GREEN}🧪 Mode test activé - Pseudo: {username}{Colors.END}")
        
        # Démarrer l'application
        main_menu()
        
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}👋 Interruption - Au revoir!{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}💥 Erreur: {str(e)}{Colors.END}")
        import traceback
        traceback.print_exc()
        input("Appuyez sur Entrée pour quitter...")