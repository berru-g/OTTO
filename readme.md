# Tool-Kit 

    This repository contains a collection of security tools and utilities for network reconnaissance and system monitoring.
    Please refer to the individual scripts for detailed usage instructions and functionalities.


# OTTO

Ce dépôt rassemble plusieurs projets et scripts d'automatisation, d'outils de sécurité et d'utilitaires en Python/JS. 

## Arborescence et rôles des dossiers

- Gestionnaire de mdp
  - Projet/outil de gestion de mots de passe (stockage chiffré, interface, export/import). Créer, lire et gérer des mots de passe de manière sécurisée.

- coordonate
  - Scripts liés aux coordonnées ( calculs de positions de la souris à l'écran pour automation via pygame par exemple ou pyautogui). 

- crypto
  - Fonctions et utilitaires cryptographiques : chiffrement, déchiffrement, gestion de clés, hashing et outils sécuritaires réutilisables par d'autres composants du dépôt.

- front-end-files-auto
  - Fichiers vbs pour créer un template basic (base de travail) front‑end (HTML/CSS/JS) en un simple double clic

- instagram-auto
  - Scripts d'automatisation pour Instagram (like auto, etc)

- kl
  - Keylogger local (enregistre les frappes clavier et les enregistre dans un.txt local only). Projet éducatif, à utiliser uniquement à des fins légales et éthiques.

- klm
  - V2

- mess
  - Outils et scripts pour messagerie (bots, envoi de messages en mode brut)

- preset
  - Presets, pour ouvrir un set upcomplet avec un simple clic (exemple : front-end-files-auto)

- pyauto
  - Scripts Python d'automatisation (interaction avec l'interface, automatisation de tâches système, utilisation de librairies comme pyautogui, selenium, etc.).

- scrap
- Tool pour builder de saas. Chercher un probleme, compiler les resultats, creer un mini saas pour repondre a ce probleme.
  - Scripts de scraping de sub/Reddit.

- secu
  - Outils et scripts HELP DESK liés à la sécurité : audits, tests, exemples d'outils de sécurisation ou d'analyse réseau, Nmap Like.

- task
  - Tâches automatisées, gestionnaires de tâches, scripts planifiés (cron jobs, workflow automation) et utilitaires pour organiser le travail.




# 🚀 **TRIFECTA SECURITE/RÉSEAU - Kit Complet HelpDesk/Admin**

## 📋 **PRÉSENTATION DES 3 OUTILS COMPLÉMENTAIRES**
    - `nmap.py` : Scanner réseau et analyse système
    - `transfert_SMB.py` : Transfert de fichiers rapide via SMB
    - `server_FTP.py` : Serveur FTP local avec interface web

### **1. 🎯 `nmap.py` - LE SCANNER/PROTECTEUR**
**Rôle:** *"Les yeux et les oreilles de ton réseau"*

```
🔍 Ce que c'est:
   → Un couteau suisse réseau en Python
   → Scanner de vulnérabilités + analyse système
   → Interface CLI style "helpdesk" intuitive

🛡️ Son super-pouvoir:
   "Voir l'invisible" sur ton réseau
   Détecter les ports ouverts, services exposés
   Analyser les processus suspects, connexions réseaux

🎯 Cas typique:
   "Pourquoi mon PC est lent?"
   → scan-all → trouve processus malware
   → kill [malware.exe] → problème résolu
```

### **2. 📁 `transfert_SMB.py` - LE COURRIER INTERNE**
**Rôle:** *"Le livreur de fichiers entre collègues"*

```
🔗 Ce que c'est:
   → Interface simplifiée pour partager via SMB
   → Scan auto du réseau + sélection visuelle
   → Transfert sécurisé local sans cloud

🚚 Son super-pouvoir:
   "Envoyer 10Go en 2 clics" sur le réseau local
   Pas de compte, pas d'upload, direct machine→machine
   Interface user-friendly pour non-techos

🎯 Cas typique:
   "J'ai un film de 8Go pour mon coloc"
   → Lance transfert_SMB.py
   → Choisit son PC dans la liste
   → Drag&drop le fichier → Transfert à 100MB/s
```

### **3. 🌐 `server_FTP.py` - L'ENTREPÔT CENTRAL**
**Rôle:** *"Le drive d'entreprise maison"*

```
🗄️ Ce que c'est:
   → Serveur FTP maison avec interface web
   → Stockage centralisé accessible à tous
   → Gestion des utilisateurs, quotas, logs

📦 Son super-pouvoir:
   "Un Dropbox local et gratuit"
   Fichiers accessibles même si une machine est éteinte
   Historique, backup automatique, partage contrôlé

🎯 Cas typique:
   "On a 5 collocs, chacun ses fichiers"
   → Serveur FTP sur le NAS
   → Chacun a son compte/mot de passe
   → Fichiers projets perso accessibles 24/7
```

---

## 🔗 **LE LIEN ENTRE LES 3 OUTILS - L'ÉCOSYSTÈME COMPLET**

### **📊 Tableau de correspondance:**

| Besoin | Outil à utiliser | Alternative | Pourquoi choisir l'un ou l'autre |
|--------|------------------|-------------|-----------------------------------|
| **Scanner mon réseau** | `nmap.py` | - | Le seul qui scanne |
| **Envoyer un fichier rapide** | `transfert_SMB.py` | USB/clé | Plus rapide que USB (1Gb/s vs 50MB/s) |
| **Partager un dossier perso** | `transfert_SMB.py` | Google Drive | Pas de limite taille, pas d'upload internet |
| **Stockage central équipe** | `server_FTP.py` | `transfert_SMB.py` | FTP = toujours dispo, SMB = besoin machine allumée |
| **Audit de sécurité** | `nmap.py` | - | Détecte ports ouverts, services vulnérables |
| **Vérifier qui est sur le wifi** | `nmap.py` | `transfert_SMB.py` | nmap montre TOUTES les IP, SMB que les partages |

### **🔄 Comment ils communiquent:**

```
nmap.py (découverte) → transfert_SMB.py (action) → server_FTP.py (stockage)
      ↓                       ↓                           ↓
"Je vois que le NAS"  "J'envoie le fichier"   "Je le sauvegarde"
"a le port 445 ouvert"  "au NAS via SMB"       "sur le serveur FTP"
```

---

## 🎬 **CAS PRATIQUE COMPLET - SCÉNARIO RÉEL**

### **Situation:** 
Tu es admin système dans une petite entreprise (ou colocation tech). Une nouvelle recrue arrive.

### **Jour 1 - Audit et configuration:**

```bash
# 1. Audit du réseau avec nmap.py
$ python nmap.py
helpdesk> netscan 192.168.1.0/24
→ Découvre toutes les machines, leurs ports ouverts
→ Trouve le NAS (192.168.1.50) avec SMB et FTP activés
→ Note les vulnérabilités potentielles

# 2. Configuration du partage pour la recrue
$ python transfert_SMB.py
→ Menu [2] "Configurer réception"
→ Crée un partage "Bienvenue_Jean"
→ Donne l'adresse \\TON-PC\Bienvenue_Jean à la recrue

# 3. Mise en place du stockage commun
$ python server_FTP.py start
→ Démarre le serveur FTP sur le NAS
→ Crée un compte "jean" avec mot de passe
→ Configure un dossier /commun pour l'équipe
```

### **Jour 2 - Transfert des documents de formation:**

```bash
# 1. La recrue a les documents sur son PC
# Elle utilise transfert_SMB.py depuis SON poste:
$ python transfert_SMB.py
→ [1] "Envoyer un fichier"
→ Sélectionne le manuel.pdf (50Mo)
→ Choisit TON-PC dans la liste auto
→ Transfert en 5 secondes

# 2. Tu veux sauvegarder ces docs sur le serveur central
# Depuis TON poste:
$ python transfert_SMB.py
→ [5] "Choisir IP depuis liste"
→ Sélectionne le NAS (192.168.1.50)
→ Envoie vers le dossier /formations

# Alternative via FTP direct:
$ ftp 192.168.1.50
→ login: admin, password: ****
→ put manuel.pdf /commun/formations/
```

### **Jour 15 - Problème de performance réseau:**

```bash
# Un collègue se plaint de lenteur
$ python nmap.py
helpdesk> net
→ Voir toutes les connexions actives
→ Trouve un PC avec 1000+ connexions vers l'internet
→ Suspect: malware ou téléchargement abusif

helpdesk> proc
→ Liste les processus
→ Identifie "torrent_client.exe" gourmand en bande passante

helpdesk> kill torrent_client.exe
→ Problème résolu en 30 secondes

# Pour prévenir à l'avenir:
$ python server_FTP.py
→ Active le quota de 5Go/utilisateur
→ Logge toutes les connexions
```

---

## 🎯 **QUAND UTILISER QUEL OUTIL - ARBRE DE DÉCISION**

```
"J'ai besoin de..."
      ↓
"Partager un fichier rapidement" → Fichier < 2Go? → OUI → transfert_SMB.py
      ↓                                           ↓
      NON                                         NON
      ↓                                    "server_FTP.py"
"Scanner/Auditer" → Sécurité? → OUI → nmap.py
      ↓                    ↓
      NON                 NON
      ↓              "transfert_SMB.py (mode scan)"
"Stocker centralement" → server_FTP.py
```

### **Règle du pouce:**
- **nmap.py:** Quand tu te poses des questions ("qui est sur mon réseau?", "pourquoi c'est lent?")
- **transfert_SMB.py:** Quand tu veux donner/recevoir un fichier MAINTENANT
- **server_FTP.py:** Quand tu veux un endroit permanent pour des fichiers d'équipe

---

## 🔧 **INTÉGRATION AVANCÉE - SCÉNARIO PRO**

### **Pour une petite entreprise (5 personnes):**

```yaml
Infrastructure:
  - Routeur: 192.168.1.1
  - NAS (server_FTP.py): 192.168.1.50 → Stockage documents clients
  - PC Admin: nmap.py → Surveillance quotidienne
  - Tous les PCs: transfert_SMB.py → Transferts internes

Workflow typique:
  1. Client envoie fichier par email
  2. Réceptionnaire le met sur server_FTP.py dans /clients/
  3. Comptable le récupère via transfert_SMB.py
  4. nmap.py scan hebdomadaire vérifie la sécurité
  5. Backup automatique sur NAS via scripts
```

### **Pour une colocation de gamers:**

```yaml
Utilisation:
  - transfert_SMB.py: Échanger les jeux crackés (100+ Go)
  - nmap.py: Vérifier qui flood le réseau (torrents)
  - server_FTP.py: Serveur de mods/maps pour serveur Minecraft

Exemple:
  "J'ai téléchargé Cyberpunk 2077 (70Go)"
  1. transfert_SMB.py vers le PC du pote
  2. Vitesse: 1-2 heures (réseau 1Gb/s)
  3. Alternative: USB = 4-5 heures + déplacement physique
```

---

## ⚠️ **ATTENTION - LES PIÈGES À ÉVITER**

### **Ne pas confondre:**
- ❌ `nmap.py` ≠ outil de transfert (c'est un scanner de reseau)
- ❌ `transfert_SMB.py` ≠ stockage permanent (fichier disparaît si machine éteinte)
- ❌ `server_FTP.py` ≠ solution backup (manque de redondance)

### **Bonnes pratiques:**
1. **nmap.py:** Scanner seulement TON réseau, jamais sans autorisation
2. **transfert_SMB.py:** Toujours mettre un mot de passe sur les partages
3. **server_FTP.py:** Changer les mots de passe par défaut, faire des backups

---
## A implementer quand j'aurai le temps :
# 2. Interface web unifiée
# Un seul lanceur pour les 3 outils
$ python network_toolkit.py
→ [1] Scanner (nmap)
→ [2] Transférer (SMB)
→ [3] Stocker (FTP)
→ [4] Dashboard (vue globale)

# 3. Automatisation
# Script qui fait tout automatiquement:
$ python setup_new_user.py "Jean"
→ Crée compte FTP
→ Crée partage SMB
→ Configure les quotas
→ Envoie les docs de bienvenue
```

---

## 📞 **SUPPORT D'URGENCE - "ÇA MARCHE PAS!"**

### **Problèmes courants et solutions:**

1. **"transfert_SMB.py ne voit pas les autres PCs"**
   → Vérifier avec `nmap.py` si les PCs sont sur le réseau
   → Vérifier le firewall (port 445 bloqué)

2. **"server_FTP.py inaccessible"**
   → nmap.py scan 192.168.1.50:21 → Port ouvert?
   → Vérifier les credentials

3. **"nmap.py trouve des choses bizarres"**
   → Google l'IP + port (ex: "192.168.1.50:8080")
   → Vérifier si c'est un service connu

### **Checklist de dépannage:**
```bash
# 1. Tout est-il connecté au même réseau?
ipconfig /all | findstr "192.168"

# 2. Les services sont-ils démarrés?
netstat -an | findstr :445  # SMB
netstat -an | findstr :21   # FTP

# 3. nmap.py voit-il les machines?
python nmap.py
helpdesk> netscan 192.168.1.0/24
```

---

## 🎖️ **CONCLUSION - TA TRIFECTA GAGNANTE**

Avec ces 3 outils, tu couvres **90% des besoins réseau d'une petite structure**:

- ✅ **Découverte/résolution problèmes** → nmap.py
- ✅ **Transfert rapide local** → transfert_SMB.py  
- ✅ **Stockage collaboratif** → server_FTP.py


