# 📜 LISTE COMPLÈTE DES COMMANDES - helpdesk.py + nmap.py

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