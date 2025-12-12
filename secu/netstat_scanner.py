#!/usr/bin/env python3
"""
Scanner de sécurité réseau pour détecter les menaces communes
Usage : python3 netstat_scanner.py
"""

import subprocess
import re
import socket
from collections import defaultdict
import json
import warnings
import sys
import os

# Désactiver les warnings SSL si on fait des requêtes HTTP
warnings.filterwarnings('ignore')

# Base de données des ports suspects (à étendre)
SUSPECT_PORTS = {
    3333: "Pool de minage (Monero, CryptoNight)",
    4444: "Metasploit/Reverse Shell",
    5555: "Android Debug Bridge (potentiellement malveillant)",
    6666: "IRC Bot (UnrealIRCd)",
    6667: "IRC Bot",
    6668: "IRC Bot",
    6669: "IRC Bot",
    7777: "Pool de minage alternatif",
    8080: "Proxy malveillant (peut être légitime)",
    8333: "Bitcoin (peut être légitime si tu mines)",
    8443: "SSL malveillant",
    8888: "Minage/Backdoor",
    9000: "Port souvent utilisé par des malwares",
    9050: "Tor (peut être légitime)",
    9333: "Litecoin pool (minage)",
    9999: "Backdoor",
    12345: "NetBus Trojan",
    12346: "NetBus Trojan",
    20000: "Usermin/Backdoor",
    31337: "Back Orifice (classique)",
    44444: "Port courant pour miners",
    49152: "Ports dynamiques souvent utilisés par malwares"
}

# Pools de minage connus (IP/domaines)
MINING_POOLS = [
    "xmrpool.eu", "minexmr.com", "supportxmr.com", "nanopool.org",
    "cryptonight", "monero", "ethereum", "ethpool", "f2pool",
    "nicehash", "minergate"
]

# Services Windows légitimes
LEGIT_SERVICES = [
    "svchost.exe", "lsass.exe", "wininit.exe", "csrss.exe",
    "winlogon.exe", "services.exe", "explorer.exe", "chrome.exe",
    "firefox.exe", "msedge.exe", "steam.exe", "discord.exe",
    "system", "dwm.exe", "taskhostw.exe", "sihost.exe"
]

def run_netstat():
    """Exécute netstat et retourne les résultats"""
    try:
        # Pour Windows
        if os.name == 'nt':
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        # Pour Linux/Mac
        else:
            result = subprocess.run(
                ['netstat', '-tunap'],
                capture_output=True,
                text=True
            )
        return result.stdout
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution de netstat: {e}")
        sys.exit(1)

def parse_netstat_windows(output):
    """Parse la sortie de netstat pour Windows"""
    connections = []
    
    for line in output.split('\n'):
        # Recherche les lignes avec des connexions TCP/UDP
        if 'TCP' in line or 'UDP' in line:
            # Netstat Windows format: Proto AdresseLocale AdresseDistante Etat PID
            parts = line.strip().split()
            if len(parts) >= 5:
                # Reconstruire les adresses qui peuvent contenir des espaces
                proto = parts[0]
                local_addr = parts[1]
                remote_addr = parts[2] if len(parts) > 2 else ''
                state = parts[3] if len(parts) > 3 else ''
                pid = parts[4] if len(parts) > 4 else ''
                
                # Extraire le port de l'adresse distante
                remote_port = None
                if ':' in remote_addr:
                    try:
                        remote_port = int(remote_addr.split(':')[-1])
                    except:
                        pass
                
                connections.append({
                    'proto': proto,
                    'local': local_addr,
                    'remote': remote_addr,
                    'state': state,
                    'pid': pid,
                    'remote_port': remote_port,
                    'process_name': get_process_name(pid) if pid else 'N/A'
                })
    
    return connections

def get_process_name(pid):
    """Récupère le nom du processus à partir du PID (Windows)"""
    try:
        if os.name == 'nt':
            result = subprocess.run(
                ['tasklist', '/FI', f'PID eq {pid}', '/FO', 'CSV', '/NH'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.stdout.strip():
                # Format CSV: "nom.exe","PID","session","#session","mémoire"
                parts = result.stdout.strip().split(',')
                if len(parts) > 0:
                    name = parts[0].strip('"')
                    return name
    except:
        pass
    return f"PID:{pid}"

def analyze_connections(connections):
    """Analyse les connexions pour détecter des menaces"""
    alerts = []
    stats = defaultdict(int)
    
    # Statistiques par processus
    process_conns = defaultdict(list)
    
    for conn in connections:
        remote_port = conn['remote_port']
        process = conn['process_name']
        remote_addr = conn['remote']
        
        # 1. Détection par port suspect
        if remote_port in SUSPECT_PORTS:
            alert = {
                'level': '⚠️ HAUTE',
                'type': 'PORT_SUSPECT',
                'message': f"Port suspect détecté: {remote_port} ({SUSPECT_PORTS[remote_port]})",
                'process': process,
                'connection': f"{conn['local']} -> {remote_addr}",
                'state': conn['state']
            }
            alerts.append(alert)
            stats['ports_suspects'] += 1
        
        # 2. Détection de minage (beaucoup de connexions sur ports minage)
        if remote_port and (remote_port in [3333, 4444, 7777, 8888, 9333]):
            stats['ports_minage'] += 1
        
        # 3. Regrouper par processus pour détecter les bots
        process_conns[process].append(conn)
    
    # 4. Détection de botnet (même processus, nombreuses connexions)
    for process, conns in process_conns.items():
        if len(conns) > 10:  # Seuil arbitraire
            # Vérifier si c'est un processus légitime
            is_legit = any(legit in process.lower() for legit in [l.lower() for l in LEGIT_SERVICES])
            
            if not is_legit and 'chrome' not in process.lower() and 'firefox' not in process.lower():
                # Vérifier si les connexions sont vers des ports variés
                unique_ports = len(set([c['remote_port'] for c in conns if c['remote_port']]))
                if unique_ports > 3:
                    alert = {
                        'level': '🚨 CRITIQUE',
                        'type': 'BOTNET_SUSPICION',
                        'message': f"Processus suspect avec {len(conns)} connexions actives (possible botnet)",
                        'process': process,
                        'connections_count': len(conns),
                        'unique_ports': unique_ports
                    }
                    alerts.append(alert)
                    stats['botnet_suspect'] += 1
    
    # 5. Détection de mining (connexions multiples sur ports de minage)
    if stats['ports_minage'] >= 3:
        alert = {
            'level': '🔥 URGENT',
            'type': 'CRYPTOMINING',
            'message': f"{stats['ports_minage']} connexions vers des ports de minage détectées!",
            'details': "Votre PC est probablement en train de miner de la crypto-monnaie pour un pirate."
        }
        alerts.append(alert)
    
    # 6. Détection de backdoor (port en écoute élevé)
    listening_high_ports = []
    for conn in connections:
        if conn['state'] == 'LISTENING':
            try:
                port = int(conn['local'].split(':')[-1])
                if port > 10000 and port < 49152:
                    listening_high_ports.append((port, conn['process_name']))
            except:
                pass
    
    if listening_high_ports:
        for port, process in listening_high_ports[:3]:  # Afficher les 3 premiers
            if not any(legit in process.lower() for legit in LEGIT_SERVICES):
                alert = {
                    'level': '⚠️ MOYENNE',
                    'type': 'BACKDOOR_POSSIBLE',
                    'message': f"Port élevé en écoute: {port} (possible backdoor)",
                    'process': process
                }
                alerts.append(alert)
                stats['backdoor_suspect'] += 1
    
    return alerts, stats, process_conns

def display_results(connections, alerts, stats, process_conns):
    """Affiche les résultats de l'analyse"""
    print("\n" + "="*80)
    print("🔍 SCANNER DE SÉCURITÉ RÉSEAU - RAPPORT D'ANALYSE")
    print("="*80)
    
    print(f"\n📊 Statistiques globales:")
    print(f"   Connexions analysées: {len(connections)}")
    print(f"   Processus uniques: {len(process_conns)}")
    
    if alerts:
        print(f"\n🚨 ALERTES DE SÉCURITÉ ({len(alerts)} détectées):")
        print("-"*80)
        
        # Trier par niveau de criticité
        level_order = {'🚨 CRITIQUE': 0, '🔥 URGENT': 1, '⚠️ HAUTE': 2, '⚠️ MOYENNE': 3}
        alerts.sort(key=lambda x: level_order.get(x['level'], 999))
        
        for alert in alerts:
            print(f"\n{alert['level']} {alert['type']}")
            print(f"   📝 {alert['message']}")
            if 'process' in alert:
                print(f"   🖥️  Processus: {alert['process']}")
            if 'connection' in alert:
                print(f"   🔗 Connexion: {alert['connection']}")
            if 'connections_count' in alert:
                print(f"   🔢 Connexions: {alert['connections_count']}")
            print("-"*40)
    else:
        print("\n✅ Aucune alerte de sécurité critique détectée.")
    
    # Afficher les connexions suspectes par processus
    print(f"\n🔎 Top des processus avec connexions actives:")
    print("-"*80)
    
    # Trier par nombre de connexions
    sorted_procs = sorted(process_conns.items(), key=lambda x: len(x[1]), reverse=True)
    
    for process, conns in sorted_procs[:15]:  # Top 15 seulement
        legit = any(legit in process.lower() for legit in [l.lower() for l in LEGIT_SERVICES])
        marker = "✅" if legit else "❓"
        
        # Compter les états
        states = defaultdict(int)
        for c in conns:
            states[c['state']] += 1
        
        state_str = ", ".join([f"{k}:{v}" for k, v in states.items()])
        
        print(f"\n{marker} {process}")
        print(f"   Connexions totales: {len(conns)}")
        print(f"   États: {state_str}")
        
        # Afficher quelques connexions distantes uniques
        unique_remotes = set()
        for c in conns[:5]:  # 5 premières max
            if c['remote'] and c['remote'] != '0.0.0.0:0':
                unique_remotes.add(c['remote'].split(':')[0])
        
        if unique_remotes:
            print(f"   IP distantes uniques: {', '.join(list(unique_remotes)[:3])}" + 
                  ("..." if len(unique_remotes) > 3 else ""))
    
    # Recommendations
    print(f"\n💡 RECOMMANDATIONS:")
    print("-"*80)
    
    if any('CRYPTOMINING' in a['type'] for a in alerts):
        print("""
    🚨 PROBABLE MINAGE DE CRYPTOMONNAIE DÉTECTÉ:
    1. Ouvrez le Gestionnaire des tâches (Ctrl+Maj+Echap)
    2. Triez par utilisation CPU
    3. Identifiez le processus qui utilise le plus de CPU
    4. Terminez-le et supprimez son fichier exécutable
    5. Scannez avec Malwarebytes et AdwCleaner
    """)
    
    if any('BOTNET_SUSPICION' in a['type'] for a in alerts):
        print("""
    🤖 SUSPICION DE BOTNET:
    1. Notez le nom du processus suspect
    2. Recherchez-le sur Internet (depuis votre téléphone)
    3. Utilisez 'Autoruns' pour vérifier son démarrage automatique
    4. Considérez une réinstallation propre de Windows
    """)
    
    print(f"""
    🔧 ACTIONS GÉNÉRALES:
    1. Mettez à jour Windows et vos antivirus
    2. Changez tous vos mots de passe
    3. Activez l'authentification à deux facteurs
    4. Sauvegardez vos données importantes
    5. En cas de doute, réinstallez Windows proprement
    """)

def main():
    """Fonction principale"""
    print("🔄 Capture des connexions réseau en cours...")
    
    # 1. Capturer les connexions
    output = run_netstat()
    
    # 2. Parser les résultats
    if os.name == 'nt':
        connections = parse_netstat_windows(output)
    else:
        print("⚠️ Version Linux/Mac non implémentée dans ce script")
        print("Utilisez plutôt: netstat -tunap | grep -i est")
        connections = []
    
    if not connections:
        print("❌ Aucune connexion analysée. Vérifiez les permissions (admin requis).")
        sys.exit(1)
    
    # 3. Analyser les menaces
    alerts, stats, process_conns = analyze_connections(connections)
    
    # 4. Afficher les résultats
    display_results(connections, alerts, stats, process_conns)
    
    # 5. Sauvegarder le rapport
    try:
        with open('scan_securite_rapport.txt', 'w', encoding='utf-8') as f:
            f.write(f"Rapport de scan de sécurité\n")
            f.write(f"Connexions analysées: {len(connections)}\n")
            f.write(f"Alertes détectées: {len(alerts)}\n\n")
            for alert in alerts:
                f.write(f"{alert['level']}: {alert['message']}\n")
        print(f"\n📄 Rapport sauvegardé: scan_securite_rapport.txt")
    except:
        pass

if __name__ == "__main__":
    # Vérifier les privilèges admin sur Windows
    if os.name == 'nt':
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin:
                print("⚠️ ATTENTION: Exécutez ce script en tant qu'administrateur!")
                print("   Clic droit -> Exécuter en tant qu'administrateur")
                input("Appuyez sur Entrée pour continuer quand même...")
        except:
            pass
    
    main()
    
    print("\n" + "="*80)
    print("✅ Analyse terminée. Vérifiez les alertes ci-dessus.")
    print("="*80)