#  Ce script utilise BlueStacks comme émulateur Android
import pyautogui
import schedule
import time

# Coordonnées de l'icône WhatsApp sur BlueStacks
whatsapp_icon_x = 100
whatsapp_icon_y = 200

# Coordonnées de l'endroit où écrire le message
message_box_x = 500
message_box_y = 800


def send_whatsapp_message():
    # Ouvrir BlueStacks
    pyautogui.click(whatsapp_icon_x, whatsapp_icon_y)
    time.sleep(5) 
    
    # Sélectionner le contact
    pyautogui.click(100, 300) 
    time.sleep(5)
    
    # Écrire et envoyer le message
    pyautogui.click(message_box_x, message_box_y)
    pyautogui.write("https://www.youtube.com/watch?v=-LLkOCZVl3c&list=LL&index=1")
    pyautogui.press('enter')

# Planifier l'exécution de la fonction chaque jour à la même heure
schedule.every().day.at("07:30").do(send_whatsapp_message)

while True:
    schedule.run_pending()
    time.sleep(1)
