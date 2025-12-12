#!/usr/bin/env python3
"""
hacker_troll.py - Pour embêter un peu le hacker avant le formatage
⚠️ À utiliser avec modération et humour
"""

import random
import time
import os
from datetime import datetime

def fake_error_messages():
    """Affiche des messages d'erreur aléatoires"""
    messages = [
        "🚨 DÉTECTION : Antivirus de l'utilisateur activé",
        "⚠️  ALERTE : Outils de reverse engineering détectés",
        "🔍 Traceur d'IP activé - Transmission aux autorités",
        "💾 Suppression des logs en cours... ÉCHEC",
        "🌐 Connexion au serveur de commande... PERDUE",
        f"📡 Signalement automatique : {datetime.now()}",
        "🛡️  Pare-feu Windows a bloqué le port 4444",
        "👮‍♂️ Notification envoyée à l'ANSSI"
    ]
    
    for _ in range(3):
        print(random.choice(messages))
        time.sleep(2)

def create_fake_forensic_files():
    """Crée des fichiers qui font "pro" pour inquiéter"""
    fake_files = [
        ("evidence_log.txt", f"Rapport forensique - {datetime.now()}\nIP Source: TOR Exit Node\nTechnique: PowerShell Empire\nIndicateurs de compromission: HIGH"),
        ("wireshark_capture.pcap", "# Fake capture - looks technical"),
        ("malware_analysis.md", "## Analyse du sample\nSHA256: fake_hash\nComportement: Coin miner + RAT"),
        ("report_to_authorities.txt", "Dossier #2024-{random.randint(1000,9999)}\nTransmis: Oui")
    ]
    
    for filename, content in fake_files:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"📄 Créé: {filename}")
    
    print("\n🎣 Leurre posé : fichiers 'forensiques' créés")

def main():
    print("""
    ╔═══════════════════════════════════════╗
    ║    OPERATION 'CYBER BLUFF'           ║
    ║    Petit troll éducatif              ║
    ╚═══════════════════════════════════════╝
    
    Parce qu'un peu d'humour dans la sécurité,
    ça ne fait pas de mal...
    """)
    
    input("Appuie sur Entrée pour lancer le bluff...")
    
    fake_error_messages()
    print("\n" + "="*50)
    create_fake_forensic_files()
    
    print("""
    ===========================================
    🎭 Bluff terminé !
    
    Maintenant, sérieusement :
    1. Ces fichiers sont FAUX
    2. Ils ne protègent pas ton PC
    3. Le seul vrai remède : formatage
    
    Mais au moins, ça fait du bien 😉
    """)

if __name__ == "__main__":
    main()