
# LOCAL NETWORK _ SMB chat v_1.2  

**Chat & transfert de fichiers en réseau local • Sécurisé • Open Source • Sans serveur**  

[![Version](https://img.shields.io/badge/version-2.0.0-blue)](https://github.com/berru-g/OTTO/SMBchat/releases)
[![Python](https://img.shields.io/badge/python-3.8+-green?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)
[![Security](https://img.shields.io/badge/security-AES--128%2BHMAC--SHA256-orange)](SECURITY.md)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)](https://github.com/berru-g/OTTO/SMBchat)
[![Status](https://img.shields.io/badge/status-stable-brightgreen)](https://github.com/berru-g/OTTO/SMBchat)

[![Encryption](https://img.shields.io/badge/encryption-Fernet%20(AES-128)-informational)](https://cryptography.io/)
[![GUI](https://img.shields.io/badge/GUI-CustomTkinter-9cf)](https://github.com/TomSchimansky/CustomTkinter)
[![Protocol](https://img.shields.io/badge/protocol-SMB%2FTCP-important)](https://docs.microsoft.com/en-us/windows/win32/fileio/microsoft-smb-protocol)
[![Messages](https://img.shields.io/badge/messages-auto--destruct%2024h-red)](https://github.com/berru-g/OTTO/SMBchat#security)
[![Code Style](https://img.shields.io/badge/code%20style-pep--8-black)](https://www.python.org/dev/peps/pep-0008/)

---

## 🎯 Pitch en 2 lignes  
**SMB chat v_1.2** est l'outil de communication interne autonome pour petites structures. Chat en temps réel, transfert de fichiers ultra-rapide et messages éphémères chiffrés, le tout directement sur votre réseau local — sans serveur externe ni configuration complexe.

---

## 📦 Installation Rapide
```bash
# 1. Téléchargez l'exécutable Windows
curl -LO https://github.com/berru-g/OTTO/SMBchat/releases/latest/LocalNetworkSuite.exe

# 2. Ou installez depuis le code source
git clone https://github.com/berru-g/OTTO/SMBchat.git
cd SMBchat
pip install -r requirements.txt
python SMBchatV2.py
```

## ✨ Fonctionnalités Clés
- 💬 **Chat P2P temps réel** avec détection automatique des utilisateurs
- 📁 **Transfert de fichiers SMB** rapide sans limite de taille
- 🔐 **Messages chiffrés** (AES-128 + HMAC-SHA256) auto-destructifs après 24h
- 🖥️ **Double interface** : Graphique moderne (CustomTkinter) + Console pro
- 🌐 **Scan réseau intelligent** (ARP + ping + ports) sans configuration
- 🚫 **Zéro serveur externe** - tout reste sur votre réseau local

## 🛡️ Sécurité
| Couche | Technologie | Protection |
|--------|------------|------------|
| Stockage | Fernet (AES-128-CBC + HMAC-SHA256) | Fichiers illisibles sur disque |
| Transport | TCP brut (LAN) | Rapidité maximale sur réseau interne |
| Vie privée | Messages éphémères 24h | Auto-nettoyage quotidien |
| Authentification | Pseudo + IP réseau | Simple pour petites équipes |

## 📖 Utilisation Basique
```python
# 1. Lancez l'application
# 2. Choisissez votre pseudo
# 3. L'app scanne automatiquement votre réseau
# 4. Cliquez sur un contact pour chatter
# 5. Glissez-déposez des fichiers pour les partager
```

## 🧩 Architecture Technique
```
SMB chat v_1.2/
├── Core/           # Moteur réseau et chat
│   ├── network.py           # Scan ARP + ping
│   ├── chat_protocol.py     # Communication P2P
│   ├── encryption.py        # AES-128 + HMAC-SHA256
│   └── message_store.py     # Gestion messages volatils
├── UI/             # Interfaces
│   ├── gui_app.py          # Interface CustomTkinter
│   └── console_app.py      # Mode terminal
└── Utils/          # Services
    ├── notifications.py    # Alertes système
    └── file_transfer.py    # Transfert SMB optimisé
```

## 🔧 Pour les Développeurs
```bash
# Environnement de développement
python -m venv .venv
source .venv/bin/activate  # ou .venv\Scripts\activate sur Windows
pip install -r requirements-dev.txt

# Exécuter les tests
pytest tests/ -v

# Builder l'exécutable
pyinstaller --onefile --windowed SMBchatV2.py
```

## 🤝 Contribuer
Les contributions sont les bienvenues ! Consultez notre [guide de contribution](CONTRIBUTING.md) pour :
- 🐛 Signaler un bug
- 💡 Proposer une fonctionnalité
- 🔧 Soumettre une pull request
- 📖 Améliorer la documentation

## 📄 Licence
Ce projet est sous licence **MIT** - voir le fichier [LICENSE](LICENSE) pour plus de détails.

---
**⭐ Un projet de [berru-g](https://github.com/berru-g) • [Signaler un problème](https://github.com/berru-g/OTTO/SMBchat/issues) • [Discuter des idées](https://github.com/berru-g/OTTO/SMBchat/discussions)**
```
