# SMB chat V2 whit interface

## Messagerie privé et éphemaire. Transfert de fichier crypté sur réseau local via protocole SMB

Version amélioré de SMBchat avec:

    *Mode Console* (amélioré) - conservé intact

    *Mode Interface Tkinter* - nouveau, user-friendly

    *Système de fichiers cryptés auto-destructifs*
    Toutes les fonctionnalités des 2 scripts

*Cette V2 fait :*

    Système de messages auto-destructifs : Fichiers JSON chiffrés qui s'auto-nettoient

    Dual-mode : Console + Interface graphique

    Store unifié : Mêmes messages dans les deux modes

    Interface console complète : Menu complet avec couleurs

    Interface GUI basique : Structure avec CustomTkinter


## Structure du projet

```bash


smb_suite/
├── __main__.py
├── core/
│   ├── network.py           # Scan réseau unifié
│   ├── chat_protocol.py     # Chat P2P
│   ├── file_transfer.py     # Transfert SMB
│   ├── encryption.py        # Chiffrement fichiers JSON
│   └── message_store.py     # Gestion messages auto-destructifs
├── ui/
│   ├── console_app.py       # Mode console
│   ├── gui_app.py           # Mode interface
│   └── components/          # Widgets CustomTkinter
│       ├── chat_window.py
│       ├── contact_list.py
│       └── file_transfer_ui.py
└── utils/
    ├── notifications.py
    └── audio_alerts.py