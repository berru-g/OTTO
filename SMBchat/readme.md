# Chat P2P en Réseau Local via le protocol SMB

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![Windows](https://img.shields.io/badge/Windows-supported-green.svg)](https://windows.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Application de chat décentralisé pour réseau local avec fonctionnalités...

## ✨ Fonctionnalités
- 🔍 Scan réseau automatique (ARP, ping, ports)
- 💬 Chat temps réel P2P
- 🔔 Notifications système Windows (Toast + Sons)
- 📁 Transfert fichiers intégré
- 🛡️ Détection de sécurité

## 🚀 Installation
```bash
pip install -r requirements.txt
python chatSMB.py
```

## 🌐 Architecture du Système

[Client] ←TCP→ [Client]
    ↑            ↑
    UDP Broadcast


## MENU principales

        ======================================================================
        💬 LOCAL NETWORK CHAT P2P
        ======================================================================
        📡 Scan réseau automatique + Chat en temps réel
        ✨ Basé sur le protocol SMB
        👥 Discute avec les personnes sur ton réseau WiFi!
        💎 Projet open source https://github.com/berru-g/OTTO/SMBchat/
        ======================================================================

        ══════════════════════════════════════════════════════════════════════
        🗺️  CARTE DU RÉSEAU LOCAL
        ──────────────────────────────────────────────────────────────────────
        📍 Vous: noname (192.168.1.xx)
        📡 Port chat: xxxx

        😔 Aucun hôte trouvé sur le réseau
        Vérifiez que vous êtes sur le même WiFi
        ══════════════════════════════════════════════════════════════════════

        🎯 MENU PRINCIPAL:
        [1] 💬 Discuter avec quelqu'un
        [2] 🔍 Rescanner le réseau
        [3] 📨 Voir tous les messages
        [4] 👤 Changer de pseudo
        [5] 📡 Annoncer ma présence
        [0] 🚪 Quitter

        ══════════════════════════════════════════════════════════════════════

        👉 Votre choix [0-5]:


## 🏆 POURQUOI CE PROJET EST GÉNIAL POUR APPRENDRE
Tu pratiques:

    Réseau: Sockets UDP/TCP, broadcast, P2P

    Sécurité: Chiffrement, permissions, firewall

    UI/UX: Interface terminal, expérience utilisateur

    Système: Multi-threading, gestion fichiers

    Protocoles: HTTP, FTP, SMB, custom protocols

### Disclaimer :
Ce projet est à but éducatif uniquement. Utilisez-le de manière responsable et respectez la vie privée des autres utilisateurs sur le réseau local.

    - Je vous conseille de compiler vous meme vos scripts pour eviter les malwares.
    - pyinstaller --onefile --icon=chat_icon.ico --version-file=version_info.txt SMBchat.py    