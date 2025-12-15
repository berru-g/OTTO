![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Security](https://img.shields.io/badge/Security-Tool-red)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)

# 📜 LISTE COMPLÈTE DES COMMANDES de nmap.py

## 🔍 **COMMANDES SYSTÈME (HELPDESK)**

**Cmd `scan-all`** - Scan complet système (CPU, RAM, processus, réseau, disques, alertes)  
*Équivalent à :* `systeminfo + tasklist /v + netstat -ano + wmic logicaldisk get`  
*Évite de faire :* 5 minutes de copier-coller dans 3 fenêtres différentes

**Cmd `proc`** - Liste détaillée des processus avec risques  
*Équivalent à :* `tasklist /v /fo csv | findstr /i "cpu memory"`  
*Évite de faire :* Chercher manuellement les processus gourmands CPU/RAM

**Cmd `net`** - Connexions réseau actives avec détection de menaces  
*Équivalent à :* `netstat -ano | findstr ESTABLISHED` + croisement PID/nom  
*Évite de faire :* Relier manuellement chaque PID à son processus

**Cmd `disk`** - Analyse espace disque + fichiers temporaires  
*Équivalent à :* `wmic logicaldisk get size,freespace,caption` + calculs Go  
*Évite de faire :* Convertir bytes en Go, calculer pourcentages manuellement

**Cmd `sys`** - Informations système détaillées (CPU, RAM, OS, uptime)  
*Équivalent à :* `systeminfo + wmic cpu get + wmic memorychip get`  
*Évite de faire :* Extraire infos pertinentes dans 50 lignes de résultats

**Cmd `monitor`** - Surveillance temps réel CPU/RAM/processus  
*Équivalent à :* `perfmon` ou `top` en continu  
*Évite de faire :* Ouvrir le gestionnaire de tâches et surveiller manuellement

**Cmd `malware`** - Analyse indicateurs de malware/ransomware  
*Équivalent à :* Recherche manuelle dans processus + services + fichiers temp  
*Évite de faire :* Scanner manuellement tous les processus suspects

**Cmd `find [NOM]`** - Recherche processus par nom/PID/utilisateur  
*Équivalent à :* `tasklist | findstr /i "NOM"`  
*Évite de faire :* Parcourir manuellement la liste des 100+ processus

**Cmd `kill [NOM]`** - Tuer un processus par nom  
*Équivalent à :* `taskkill /f /im NOM.exe`  
*Évite de faire :* Chercher le PID d'abord puis `taskkill /pid`

**Cmd `killpid [PID]`** - Tuer un processus par PID avec confirmation  
*Équivalent à :* `taskkill /f /pid PID`  
*Évite de faire :* Trouver le bon PID dans tasklist d'abord

**Cmd `alert`** - Afficher les alertes sécurité détectées  
*Équivalent à :* Revue manuelle des logs système  
*Évite de faire :* Analyser manuellement chaque événement suspect

**Cmd `log`** - Exporter tous les scans en JSON pour reporting  
*Équivalent à :* Sauvegarde manuelle des résultats dans un fichier  
*Évite de faire :* Copier-coller chaque résultat dans un document

---

## 🌐 **COMMANDES RÉSEAU (NMAP-LIKE)**

**Cmd `portscan [HOST]`** - Scan rapide des ports communs (21,22,80,443,etc.)  
*Équivalent à :* `nmap -F HOST` ou scan manuel avec telnet  
*Évite de faire :* Tester manuellement chaque port important

**Cmd `fullscan [HOST]`** - Scan complet ports 1-1024 avec détection services  
*Équivalent à :* `nmap -sS -p 1-1024 HOST`  
*Évite de faire :* Scanner chaque port un par un, récupérer les bannières

**Cmd `netscan [CIDR]`** - Scan de tout un réseau (ex: 192.168.1.0/24)  
*Équivalent à :* `nmap -sn CIDR` + scan des hôtes actifs  
*Évite de faire :* Pinger manuellement chaque adresse IP du réseau

**Cmd `vulnscan [HOST]`** - Scan basique de vulnérabilités (FTP anonyme, headers HTTP, etc.)  
*Équivalent à :* Tests manuels de sécurité par service  
*Évite de faire :* Vérifier manuellement chaque service pour vulnérabilités connues

**Cmd `service [HOST] [PORT]`** - Analyse détaillée d'un service (web, FTP, SSH, etc.)  
*Équivalent à :* `nmap -sV -p PORT HOST` + analyse manuelle  
*Évite de faire :* Tester manuellement le service, analyser les réponses

**Cmd `nmap`** - Menu interactif pour choisir le type de scan réseau  
*Équivalent à :* Lancer nmap avec différentes options selon besoin  
*Évite de faire :* Se souvenir de toutes les options de ligne de commande

---

## ⚡ **COMMANDES ADMINISTRATION**

**Cmd `history`** - Afficher l'historique des commandes exécutées  
*Équivalent à :* `doskey /history` dans CMD  
*Évite de faire :* Se souvenir des commandes précédentes

**Cmd `clear`** - Effacer l'écran (nettoie l'affichage mais garde l'historique)  
*Équivalent à :* `cls` dans CMD ou `clear` dans bash  
*Évite de faire :* Scroller manuellement pour retrouver le haut

**Cmd `help`** - Afficher l'aide complète avec toutes les commandes  
*Équivalent à :* Lire un manuel ou aide-mémoire  
*Évite de faire :* Se souvenir de toutes les commandes disponibles

**Cmd `quit` / `exit` / `q`** - Quitter l'application proprement  
*Équivalent à :* Fermer la fenêtre ou Ctrl+C  
*Évite de faire :* Fermer brutalement et perdre les logs

---

## 📊 **COMMANDES NUMÉRIQUES (MENU ORIGINAL)**

**Cmd `1`** - Identique à `scan-all` (Scan complet système)  
**Cmd `2`** - Identique à `proc` (Processus)  
**Cmd `3`** - Identique à `net` (Réseau)  
**Cmd `4`** - Identique à `disk` (Disques)  
**Cmd `5`** - Identique à `sys` (Infos système)  
**Cmd `6`** - Identique à `monitor` (Surveillance temps réel)  
**Cmd `7`** - Identique à `malware` (Analyse malware)  
**Cmd `8`** - Identique à `quit` (Quitter)

---

## 🎯 **EXEMPLES D'UTILISATION TYPIQUE HELP DESK**

1. **Problème de lenteur** : `proc` → voir processus gourmands → `kill [NOM]`
2. **Vérification sécurité** : `malware` → `alert` → analyser les détections
3. **Problème réseau** : `net` → voir connexions suspectes → `portscan [IP]`
4. **Disque plein** : `disk` → voir espace utilisé → analyser fichiers temp
5. **Scan préventif** : `scan-all` → revue complète système
6. **Investigation réseau** : `netscan 192.168.1.0/24` → cartographie réseau
7. **Audit web** : `service site.com 80` → analyse sécurité HTTP
8. **Reporting** : `log` → exporter résultats pour ticket helpdesk

---

**TOTAL : 25 commandes disponibles** - Toutes conçues pour gagner du temps en helpdesk ! 🚀

        **⚠️ Avertissements Légal, Cet outil est destiné à :**

            L'audit de VOS propres machines et réseaux

            Les environnements de test autorisés

            La formation à la sécurité offensive (éthique)

        **Interdit : Scan de systèmes sans autorisation explicite.**


## 🔍 **COMMENT LE SCAN RÉSEAU FONCTIONNE VRAIMENT**

### Lancement
    python nmap.py

### Scan rapide
    helpdesk> portscan 192.168.0.100

### reponse
    🎯 Options de scan réseau:
    [1] Scan rapide (ports communs)
    [2] Scan complet (1-1024)
    [3] Scan de vulnérabilités
    [4] Scan de réseau entier
    [5] Analyse détaillée d'un service

    Choix [1-5]: 5
    Port à analyser: 445
    🔧 Analyse du service 192.168.0.100:445
    ================================================================================
    ✅ Port 445 ouvert
    Service probable: SMB

### Que faire ?
Fermer le port 445 via Powershell
    [Voir le Guide de sécurité windows](Guide_de_Sécurisation_Windows.md)


### Scan complet
    helpdesk> fullscan 192.168.0.100

### **1. Scan de ports (TCP Connect Scan)**
```python
# Code réel du scanner (extrait)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(1.0)  # Timeout 1 seconde
result = sock.connect_ex((host, port))  # Tentative de connexion
if result == 0:  # Si connexion réussie
    port_state = 'open'
```

**Ce que ça fait :**
- Crée une vraie socket TCP
- Tente de se connecter à chaque port
- Si la connexion réussit → Port **OUVERT**
- Si échec/timeout → Port **FERMÉ** ou **FILTRÉ**

**Exemple avec `portscan 192.168.1.1` :**
```
✅ Port 22 (SSH) OPEN
✅ Port 80 (HTTP) OPEN  
✅ Port 443 (HTTPS) OPEN
✅ Port 3389 (RDP) OPEN
```

### **2. Découverte d'hôtes (Ping Sweep)**
```python
# Vérification hôte actif
command = ['ping', '-n', '1', '-w', '1000', host]
result = subprocess.run(command, timeout=2)
return result.returncode == 0  # True si ping répond
```

**Pour `netscan 192.168.1.0/24` :**
- Ping chaque adresse de 192.168.1.1 à 192.168.1.254
- Affiche seulement les IP qui répondent
- Puis scan les ports sur les hôtes actifs

### **3. Récupération de bannières (Banner Grabbing)**
```python
# Pour les services web
sock.send(b"GET / HTTP/1.0\r\n\r\n")
banner = sock.recv(1024).decode()
# Résultat : "HTTP/1.1 200 OK\nServer: Apache/2.4.41..."
```

**Ça donne ça en vrai :**
```
Port 80 - Apache/2.4.41 (Ubuntu)
Port 22 - SSH-2.0-OpenSSH_7.6p1
Port 21 - 220 FTP Server ready
```

### **4. Tests de vulnérabilités réels**
**Pour FTP :**
```python
sock.send(b"USER anonymous\r\n")
response = sock.recv(1024)
if "331" in response.decode():  # FTP accepte "anonymous"
    → Vulnérabilité détectée !
```

**Pour HTTP :**
```python
# Vérifie les headers de sécurité manquants
if 'X-Frame-Options' not in headers:
    → Clickjacking possible !
```

## 🎯 **TESTS RÉELS QUE TU PEUX FAIER**

### **Test 1 : Scan ton propre routeur**
```
helpdesk> portscan 192.168.1.1
```
Tu verras les ports ouverts de ta box (80 pour l'interface web, 443, etc.)

### **Test 2 : Scan Google (limité aux ports ouverts)**
```
helpdesk> portscan google.com
```
Tu verras : Port 443 (HTTPS) OPEN, peut-être 80 (HTTP redirect)

### **Test 3 : Scan ton réseau local**
```
helpdesk> netscan 192.168.1.0/24
```
Tu découvriras toutes les machines sur ton réseau !

### **Test 4 : Analyse d'un site web**
```
helpdesk> service google.com 443
```
Tu auras les infos SSL, les headers de sécurité, etc.

## ⚠️ **IMPORTANT - CONSIDÉRATIONS LÉGALES/ÉTHIQUES**

**✅ CE QUI EST AUTORISÉ :**
- Scanner **TON** réseau (192.168.x.x, 10.x.x.x)
- Scanner **TES** machines
- Sites avec permission (bug bounty, pentest autorisé)
- Labs de test (HackTheBox, TryHackMe avec autorisation)

**❌ CE QUI EST ILLÉGAL :**
- Scanner des réseaux qui ne t'appartiennent pas
- Scanner sans permission explicite
- Scanner des services publics/governementaux
- Utiliser pour nuire ou exploiter

**Cet outil est une ARME PUISSANTE :**
- Il peut découvrir des services exposés
- Trouver des vulnérabilités
- Cartographier des réseaux entiers
- Donc : **À UTILISER RESPONSABLEMENT !**

## 🔧 **COMMENT C'EST AUSSI PUISSANT QUE NMAP (presque 😅)**

**Ce que notre tool fait comme Nmap :**
- ✓ Scan TCP Connect (comme `nmap -sT`)
- ✓ Découverte d'hôtes (comme `nmap -sn`)
- ✓ Récupération de bannières (comme `nmap -sV`)
- ✓ Scan de vulnérabilités basiques
- ✓ Multi-threading (100 threads en parallèle)

**Ce que Nmap fait en plus :**
- Scan SYN stealth (`-sS`) - besoin de droits root
- Scan UDP complet
- NSE scripts (Nmap Scripting Engine)
- Détection OS avancée (`-O`)
- Évasion de firewall

**Mais pour le helpdesk, notre tool est PARFAIT car :**
1. **Intégré** dans l'outil helpdesk
2. **Simple** commandes mémorisables
3. **Résultats clairs** avec couleurs/explications
4. **Export JSON** pour reporting
5. **Historique** intégré

## **EXEMPLE DE SESSION RÉELLE**

```
helpdesk> netscan 192.168.1.0/24
🌐 Scan du réseau: 192.168.1.0/24
Plage: 192.168.1.1 - 192.168.1.254
Hôtes à scanner: 254

⏳ Recherche d'hôtes actifs...
✓ 192.168.1.1    (Routeur - Box SFR)
✓ 192.168.1.25   (PC Thomas - Windows)
✓ 192.168.1.50   (NAS Synology)
✓ 192.168.1.100  (Serveur Dev)

🔍 Analyse des hôtes actifs:
  Hôte: 192.168.1.50 (NAS)
    ✓ Port 22 (SSH)
    ✓ Port 80 (HTTP)
    ✓ Port 443 (HTTPS)
    ✓ Port 445 (SMB) ⚠️ DANGER
```

**Teste-le sur ta box et tu verras !** (Mais que sur TON réseau, hein 😉)



graph TD
    A[Interface CLI] --> B[Command Router]
    B --> C[SystemScanner]
    B --> D[NetworkScanner]
    C --> E[Process Analysis]
    C --> F[Disk Monitoring]
    D --> G[Port Scanner]
    D --> H[Vulnerability Detection]
    E --> I[JSON Report]
    F --> I
    G --> I
    H --> I