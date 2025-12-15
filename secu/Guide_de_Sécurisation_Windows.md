# HelpDesk - Guide de Sécurisation Windows avec nmap.py

## 🎯 Objectif
Automatiser la détection et la correction des ports Windows dangereux (SMB, NetBIOS, RPC).

## 📊 Problème Détecté
Scan initial révélant 3 ports à risque sur une machine Windows :
- Port 445/tcp (SMB) - Vulnérabilités EternalBlue/WannaCry
- Port 139/tcp (NetBIOS) - Fuite d'informations système  
- Port 135/tcp (MSRPC) - Service RPC exposé

## 🛠️ Solution Implémentée
Création de règles de pare-feu Windows ciblées pour bloquer l'accès réseau local.

### Commandes PowerShell (Administrateur)
```powershell
# Blocage SMB (Port 445)
New-NetFirewallRule -DisplayName "SECU-BLOCK-SMB-445" -Direction Inbound -Protocol TCP -LocalPort 445 -Action Block -RemoteAddress 192.168.0.0/24 -Profile Any

# Blocage NetBIOS (Port 139)  
New-NetFirewallRule -DisplayName "SECU-BLOCK-NetBIOS-139" -Direction Inbound -Protocol TCP -LocalPort 139 -Action Block -RemoteAddress 192.168.0.0/24 -Profile Any

# Blocage MSRPC (Port 135)
New-NetFirewallRule -DisplayName "SECU-BLOCK-MS-RPC-135" -Direction Inbound -Protocol TCP -LocalPort 135 -Action Block -RemoteAddress 192.168.0.0/24 -Profile Any