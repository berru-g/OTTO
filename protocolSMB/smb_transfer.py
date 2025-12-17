#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMART SMB TRANSFER TOOL PRO - Version améliorée
Scan réseau automatique + Interface fluide
"""

import os
import sys
import socket
import subprocess
import threading
import time
import queue
from pathlib import Path
import ipaddress
import select

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
available_hosts = []
scan_complete = False
current_menu = "main"

def clear_screen():
    """Efface l'écran selon l'OS"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    """Affiche une belle bannière"""
    clear_screen()
    banner = f"""
{Colors.CYAN}{'='*70}
{Colors.BOLD}🚀 SMART SMB TRANSFER TOOL PRO v2.0{Colors.END}
{Colors.CYAN}{'='*70}
{Colors.YELLOW}📁 Partage de fichiers simplifié via réseau local
{Colors.MAGENTA}✨ Scan auto du réseau + Interface fluide
{Colors.GREEN}👥 Parfait pour partager avec ton coloc!
{Colors.CYAN}{'='*70}{Colors.END}
    """
    print(banner)

def get_local_ip():
    """Récupère l'IP locale et le réseau"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        
        # Trouver le réseau /24 par défaut
        ip_parts = ip.split('.')
        network = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24"
        
        return ip, network
    except:
        return "127.0.0.1", "192.168.1.0/24"

def scan_network_async(network_cidr):
    """Scan le réseau en arrière-plan"""
    global available_hosts, scan_complete
    
    hosts = []
    
    try:
        network = ipaddress.ip_network(network_cidr, strict=False)
        
        print(f"{Colors.YELLOW}🔍 Scan du réseau {network_cidr}...{Colors.END}")
        print(f"{Colors.CYAN}(Scan en arrière-plan - continue pendant que tu navigues){Colors.END}\n")
        
        # Scan rapide des hôtes actifs (multi-threadé)
        def ping_host(host, result_queue):
            try:
                # Ping simple
                param = '-n' if os.name == 'nt' else '-c'
                timeout = '1000' if os.name == 'nt' else '1'
                
                command = ['ping', param, '1', '-w', timeout, str(host)]
                
                with subprocess.Popen(command, stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE) as proc:
                    out, _ = proc.communicate(timeout=2)
                    
                if proc.returncode == 0:
                    # Test SMB sur port 445
                    if test_smb_connection(str(host)):
                        result_queue.put(('smb', str(host)))
                    else:
                        result_queue.put(('active', str(host)))
                        
            except:
                pass
        
        # Scanner les 50 premières IPs (suffisant pour réseau local)
        result_queue = queue.Queue()
        threads = []
        hosts_to_scan = list(network.hosts())[:100]  # Limité pour rapidité
        
        for host in hosts_to_scan:
            t = threading.Thread(target=ping_host, args=(host, result_queue))
            t.daemon = True
            t.start()
            threads.append(t)
            time.sleep(0.01)  # Éviter le flood
        
        # Attendre un peu les résultats
        time.sleep(2)
        
        # Collecter les résultats
        smb_hosts = []
        active_hosts = []
        
        while not result_queue.empty():
            try:
                host_type, ip = result_queue.get_nowait()
                if host_type == 'smb':
                    smb_hosts.append(ip)
                else:
                    active_hosts.append(ip)
            except:
                break
        
        # Combiner et trier
        available_hosts = sorted(smb_hosts) + sorted(active_hosts)
        scan_complete = True
        
    except Exception as e:
        print(f"{Colors.RED}Erreur scan: {e}{Colors.END}")
        available_hosts = []
        scan_complete = True

def display_network_info(local_ip, network_cidr):
    """Affiche les infos réseau avec les hôtes disponibles"""
    print(f"{Colors.CYAN}{'═'*70}{Colors.END}")
    print(f"{Colors.BOLD}🌐 VOTRE RÉSEAU:{Colors.END}")
    print(f"   {Colors.GREEN}📍 Votre IP: {Colors.BOLD}{local_ip}{Colors.END}")
    print(f"   {Colors.BLUE}📡 Réseau: {network_cidr}{Colors.END}")
    
    if not scan_complete:
        print(f"   {Colors.YELLOW}⏳ Scan en cours...{Colors.END}")
    elif available_hosts:
        print(f"\n{Colors.GREEN}✅ HÔTES DÉTECTÉS ({len(available_hosts)}):{Colors.END}")
        
        # Afficher d'abord les hôtes avec SMB
        smb_hosts = [h for h in available_hosts if test_smb_connection(h)]
        other_hosts = [h for h in available_hosts if h not in smb_hosts]
        
        if smb_hosts:
            print(f"   {Colors.GREEN}📁 Avec SMB (partage possible):{Colors.END}")
            for i, host in enumerate(smb_hosts[:10]):  # Limite à 10
                hostname = get_hostname(host)
                display = f"{hostname} ({host})" if hostname else host
                print(f"      {Colors.CYAN}{i+1}. {display}{Colors.END}")
        
        if other_hosts:
            print(f"   {Colors.YELLOW}📶 Actifs (sans SMB détecté):{Colors.END}")
            for i, host in enumerate(other_hosts[:5]):
                hostname = get_hostname(host)
                display = f"{hostname} ({host})" if hostname else host
                print(f"      {Colors.YELLOW}{i+len(smb_hosts)+1}. {display}{Colors.END}")
        
        if len(smb_hosts) + len(other_hosts) < len(available_hosts):
            print(f"   {Colors.MAGENTA}... et {len(available_hosts) - (len(smb_hosts)+len(other_hosts))} autres{Colors.END}")
    else:
        print(f"   {Colors.RED}⚠️  Aucun hôte détecté{Colors.END}")
    
    print(f"{Colors.CYAN}{'═'*70}{Colors.END}\n")

def get_hostname(ip):
    """Essaie de récupérer le nom d'hôte"""
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return None

def test_smb_connection(target_ip):
    """Teste la connexion SMB"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((target_ip, 445))
        sock.close()
        return result == 0
    except:
        return False

def input_timeout(prompt, timeout=0.1):
    """Input avec timeout pour éviter les blocages"""
    print(prompt, end='', flush=True)
    
    if os.name == 'nt':
        # Windows
        import msvcrt
        import time
        
        start_time = time.time()
        input_buffer = []
        
        while True:
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
            
            if timeout > 0 and (time.time() - start_time) > timeout:
                return None
                
            time.sleep(0.01)
    else:
        # Unix/Linux/Mac
        import select
        
        ready, _, _ = select.select([sys.stdin], [], [], timeout)
        if ready:
            return sys.stdin.readline().strip()
        return None

def quick_menu_navigation():
    """Permet la navigation rapide sans appuyer sur Entrée"""
    print(f"{Colors.BOLD}🎯 MENU PRINCIPAL - Tapez le chiffre puis ENTRÉE:{Colors.END}")
    print(f"{Colors.GREEN}[1] 📤 Envoyer un fichier{Colors.END}")
    print(f"{Colors.BLUE}[2] 📥 Configurer réception{Colors.END}")
    print(f"{Colors.YELLOW}[3] 🔍 Rescanner réseau{Colors.END}")
    print(f"{Colors.MAGENTA}[4] ⚙️  Infos SMB{Colors.END}")
    print(f"{Colors.CYAN}[5] 🎯 Choisir IP depuis liste{Colors.END}")
    print(f"{Colors.RED}[0] 🚪 Quitter{Colors.END}")
    
    print(f"\n{Colors.YELLOW}💡 Astuce: Tapez directement '1' puis Entrée{Colors.END}")
    print(f"{Colors.CYAN}{'═'*70}{Colors.END}")

def send_file_menu(local_ip):
    """Menu d'envoi de fichier optimisé"""
    global current_menu
    
    current_menu = "send"
    
    while True:
        print_banner()
        local_ip, network = get_local_ip()
        display_network_info(local_ip, network)
        
        print(f"{Colors.BOLD}🚀 ENVOYER UN FICHIER{Colors.END}")
        print(f"{Colors.CYAN}(Tapez 'back' pour retour, 'list' pour voir IPs){Colors.END}\n")
        
        # 1. Fichier source
        file_path = input(f"{Colors.CYAN}📂 Chemin du fichier (ou drag & drop): {Colors.END}").strip()
        file_path = file_path.strip('"\'').strip()
        
        if file_path.lower() == 'back':
            current_menu = "main"
            return
        elif file_path.lower() == 'list':
            show_detailed_hosts()
            input(f"\n{Colors.CYAN}Appuyez sur Entrée pour continuer...{Colors.END}")
            continue
        
        if not os.path.exists(file_path):
            print(f"{Colors.RED}❌ Fichier introuvable!{Colors.END}")
            time.sleep(1)
            continue
        
        filename = os.path.basename(file_path)
        filesize = os.path.getsize(file_path)
        
        print(f"\n{Colors.GREEN}✅ Fichier: {filename} ({filesize:,} bytes){Colors.END}")
        
        # 2. IP destination (avec auto-complétion)
        while True:
            print(f"\n{Colors.CYAN}🌐 Destination - Options:{Colors.END}")
            print(f"   {Colors.GREEN}• Tapez une IP (ex: 192.168.1.101){Colors.END}")
            print(f"   {Colors.BLUE}• Tapez 'scan' pour rescanner{Colors.END}")
            print(f"   {Colors.YELLOW}• Tapez 'list' pour voir la liste{Colors.END}")
            print(f"   {Colors.MAGENTA}• Tapez 'back' pour annuler{Colors.END}")
            
            target_ip = input(f"\n{Colors.CYAN}👉 IP/Nom de la machine: {Colors.END}").strip()
            
            if target_ip.lower() == 'back':
                current_menu = "main"
                return
            elif target_ip.lower() == 'scan':
                rescan_network()
                continue
            elif target_ip.lower() == 'list':
                show_detailed_hosts()
                continue
            elif target_ip.isdigit() and 1 <= int(target_ip) <= len(available_hosts):
                # Si l'utilisateur tape un numéro de la liste
                target_ip = available_hosts[int(target_ip)-1]
                print(f"{Colors.GREEN}✓ Sélection: {target_ip}{Colors.END}")
            
            # Test de connexion
            print(f"\n{Colors.YELLOW}🔍 Test de connexion...{Colors.END}")
            if test_smb_connection(target_ip):
                print(f"{Colors.GREEN}✅ SMB accessible sur {target_ip}{Colors.END}")
                break
            else:
                print(f"{Colors.RED}⚠️  SMB non accessible sur {target_ip}{Colors.END}")
                retry = input(f"{Colors.YELLOW}Essayer quand même? (o/n): {Colors.END}").lower()
                if retry == 'o':
                    break
        
        # 3. Nom du partage
        share_name = input(f"\n{Colors.CYAN}📁 Nom du partage distant [TransferShare]: {Colors.END}").strip()
        if not share_name:
            share_name = "TransferShare"
        
        # 4. Confirmation rapide
        print(f"\n{Colors.BOLD}📋 RÉSUMÉ:{Colors.END}")
        print(f"   📤 De: {local_ip}")
        print(f"   📥 Vers: {target_ip}")
        print(f"   📄 Fichier: {filename}")
        print(f"   💾 Taille: {filesize/1024/1024:.2f} MB")
        
        confirm = input(f"\n{Colors.YELLOW}⚠️  Lancer le transfert? (o/n): {Colors.END}").lower()
        
        if confirm == 'o':
            # Transfert
            success, message = send_file_via_smb(file_path, target_ip, share_name)
            
            if success:
                print(f"\n{Colors.GREEN}✅ {message}{Colors.END}")
            else:
                print(f"\n{Colors.RED}❌ {message}{Colors.END}")
            
            # Proposer une nouvelle action
            print(f"\n{Colors.CYAN}Prochaine action:{Colors.END}")
            print(f"   {Colors.GREEN}[1] Envoyer un autre fichier{Colors.END}")
            print(f"   {Colors.BLUE}[2] Retour au menu principal{Colors.END}")
            print(f"   {Colors.YELLOW}[3] Quitter{Colors.END}")
            
            choice = input(f"\n{Colors.CYAN}👉 Choix [1-3]: {Colors.END}").strip()
            
            if choice == '2':
                current_menu = "main"
                return
            elif choice == '3':
                print(f"\n{Colors.GREEN}👋 À bientôt!{Colors.END}")
                sys.exit(0)
            # Sinon, continue (envoi autre fichier)
        else:
            # Annulation
            print(f"\n{Colors.YELLOW}⚠️  Transfert annulé{Colors.END}")
            time.sleep(1)

def show_detailed_hosts():
    """Affiche la liste détaillée des hôtes"""
    print(f"\n{Colors.CYAN}{'═'*70}{Colors.END}")
    print(f"{Colors.BOLD}📡 HÔTES DÉTECTÉS DANS LE RÉSEAU:{Colors.END}")
    
    if not available_hosts:
        print(f"{Colors.RED}Aucun hôte détecté{Colors.END}")
        return
    
    for i, host in enumerate(available_hosts[:15]):  # Limite à 15
        hostname = get_hostname(host)
        smb_status = test_smb_connection(host)
        
        if smb_status:
            status = f"{Colors.GREEN}[SMB OK]"
            icon = "📁"
        else:
            status = f"{Colors.YELLOW}[SMB N/A]"
            icon = "📶"
        
        display = f"{hostname} ({host})" if hostname else host
        print(f"   {Colors.CYAN}{i+1:2d}. {icon} {display} {status}{Colors.END}")
    
    if len(available_hosts) > 15:
        print(f"   {Colors.MAGENTA}... et {len(available_hosts)-15} autres{Colors.END}")
    
    print(f"{Colors.CYAN}{'═'*70}{Colors.END}")

def rescan_network():
    """Relance un scan du réseau"""
    global available_hosts, scan_complete
    
    print(f"\n{Colors.YELLOW}🔄 Nouveau scan en cours...{Colors.END}")
    
    local_ip, network = get_local_ip()
    available_hosts = []
    scan_complete = False
    
    # Lance le scan dans un thread
    scan_thread = threading.Thread(target=scan_network_async, args=(network,))
    scan_thread.daemon = True
    scan_thread.start()
    
    # Petite animation
    for i in range(3):
        print(f"{Colors.YELLOW}.", end='', flush=True)
        time.sleep(0.5)
    print()
    
    # Attendre un peu le scan
    time.sleep(2)

def send_file_via_smb(source_file, target_ip, target_share="TransferShare"):
    """Envoie un fichier via SMB"""
    try:
        filename = os.path.basename(source_file)
        file_size = os.path.getsize(source_file)
        
        print(f"\n{Colors.GREEN}🚀 Démarrage du transfert...{Colors.END}")
        print(f"{Colors.CYAN}De: {source_file}{Colors.END}")
        print(f"{Colors.CYAN}Vers: \\\\{target_ip}\\{target_share}\\{filename}{Colors.END}")
        
        # Simulation de progression (remplacer par vrai code SMB)
        print(f"\n{Colors.BLUE}[{'░'*40}] 0%{Colors.END}")
        
        for percent in range(10, 101, 10):
            time.sleep(0.3)  # Simulation
            filled = int(percent / 100 * 40)
            bar = '█' * filled + '░' * (40 - filled)
            print(f"\r{Colors.BLUE}[{bar}] {percent}%{Colors.END}", end='', flush=True)
        
        print(f"\n\n{Colors.GREEN}✅ Transfert simulé réussi!{Colors.END}")
        
        # En vrai, utiliser robocopy ou smbclient ici
        return True, f"Fichier '{filename}' envoyé à {target_ip}"
        
    except Exception as e:
        return False, f"Erreur: {str(e)}"

def receive_file_setup(local_ip, share_name="ReceiveShare"):
    """Configure la réception"""
    try:
        receive_folder = os.path.join(os.path.expanduser("~"), "SMB_Receive")
        Path(receive_folder).mkdir(exist_ok=True)
        
        print(f"\n{Colors.GREEN}✅ Dossier créé: {receive_folder}{Colors.END}")
        
        # Pour Windows
        if os.name == 'nt':
            # Créer un partage temporaire
            cmd = f'net share {share_name}="{receive_folder}" /grant:Everyone,full'
            subprocess.run(cmd, shell=True, capture_output=True)
            
            print(f"\n{Colors.CYAN}📌 Votre adresse de partage:{Colors.END}")
            print(f"   {Colors.BOLD}\\\\{local_ip}\\{share_name}{Colors.END}")
            print(f"\n{Colors.YELLOW}⚠️  Le partage sera accessible à tous sur le réseau{Colors.END}")
            
        return True, receive_folder
    except Exception as e:
        return False, str(e)

def main():
    """Fonction principale avec interface fluide"""
    global current_menu
    
    # Récupérer l'IP et réseau local
    local_ip, network = get_local_ip()
    
    # Démarrer le scan réseau en arrière-plan
    scan_thread = threading.Thread(target=scan_network_async, args=(network,))
    scan_thread.daemon = True
    scan_thread.start()
    
    # Boucle principale
    while True:
        if current_menu == "main":
            print_banner()
            display_network_info(local_ip, network)
            quick_menu_navigation()
            
            # Input avec possibilité de timeout pour rafraîchissement auto
            try:
                choice = input(f"\n{Colors.BOLD}👉 Votre choix: {Colors.END}").strip()
            except KeyboardInterrupt:
                print(f"\n\n{Colors.YELLOW}👋 Au revoir!{Colors.END}")
                break
            
            if choice == '0' or choice.lower() in ['quit', 'exit', 'q']:
                print(f"\n{Colors.GREEN}👋 À bientôt!{Colors.END}")
                break
            elif choice == '1':
                send_file_menu(local_ip)
            elif choice == '2':
                # Configuration réception
                print_banner()
                print(f"{Colors.BOLD}📥 CONFIGURER LA RÉCEPTION{Colors.END}\n")
                
                share_name = input(f"{Colors.CYAN}Nom du partage [ReceiveShare]: {Colors.END}").strip()
                if not share_name:
                    share_name = "ReceiveShare"
                
                success, folder = receive_file_setup(local_ip, share_name)
                
                if success:
                    print(f"\n{Colors.GREEN}✅ Configuration réussie!{Colors.END}")
                    print(f"\n{Colors.BOLD}🎯 Donnez cette info à votre coloc:{Colors.END}")
                    print(f"   Adresse: {Colors.CYAN}\\\\{local_ip}\\{share_name}{Colors.END}")
                    print(f"   Dossier: {Colors.CYAN}{folder}{Colors.END}")
                else:
                    print(f"\n{Colors.RED}❌ Erreur: {folder}{Colors.END}")
                
                input(f"\n{Colors.CYAN}Appuyez sur Entrée pour continuer...{Colors.END}")
                
            elif choice == '3':
                rescan_network()
            elif choice == '4':
                # Infos SMB
                print_banner()
                print(f"{Colors.BOLD}⚙️  INFORMATIONS SMB{Colors.END}\n")
                
                if os.name == 'nt':
                    # Vérifier les partages
                    result = subprocess.run(["net", "share"], capture_output=True, text=True)
                    print(f"{Colors.CYAN}Partages actifs:{Colors.END}")
                    print(result.stdout)
                else:
                    print(f"{Colors.YELLOW}Sur Linux, vérifiez Samba avec:{Colors.END}")
                    print(f"   sudo systemctl status smbd")
                
                input(f"\n{Colors.CYAN}Appuyez sur Entrée pour continuer...{Colors.END}")
                
            elif choice == '5':
                show_detailed_hosts()
                if available_hosts:
                    ip_choice = input(f"\n{Colors.CYAN}Numéro de l'IP à utiliser: {Colors.END}").strip()
                    if ip_choice.isdigit() and 1 <= int(ip_choice) <= len(available_hosts):
                        selected_ip = available_hosts[int(ip_choice)-1]
                        print(f"\n{Colors.GREEN}✅ IP sélectionnée: {selected_ip}{Colors.END}")
                        
                        # Demander directement un fichier à envoyer
                        file_path = input(f"\n{Colors.CYAN}Chemin du fichier à envoyer: {Colors.END}").strip()
                        if os.path.exists(file_path):
                            send_file_via_smb(file_path, selected_ip)
                        else:
                            print(f"{Colors.RED}❌ Fichier introuvable{Colors.END}")
                        
                        time.sleep(2)
                else:
                    print(f"{Colors.RED}Aucune IP disponible{Colors.END}")
                    time.sleep(1)
            else:
                print(f"\n{Colors.RED}❌ Choix invalide!{Colors.END}")
                time.sleep(0.5)
        
        # Petit délai pour éviter la surcharge CPU
        time.sleep(0.1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}👋 Interruption - Au revoir!{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}💥 Erreur: {str(e)}{Colors.END}")
        import traceback
        traceback.print_exc()
        input("Appuyez sur Entrée pour quitter...")