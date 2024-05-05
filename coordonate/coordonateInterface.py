#interface pour afficher les coordonnées X et Y 
# de la souris en temps réel et les copier.
#Aide a l automatisation
import tkinter as tk
import pyautogui
from pynput import mouse

# Liste pour stocker les coordonnées copiées
copied_coordinates = []

# Fonction pour mettre à jour les coordonnées en temps réel
def update_coordinates():
    x, y = pyautogui.position()
    coordinates_label.config(text=f"X: {x}, Y: {y}")
    root.after(100, update_coordinates)  # Mise à jour toutes les 100 millisecondes

# Fonction pour copier les coordonnées dans la liste et les afficher dans la deuxième étiquette
def copy_coordinates():
    x, y = pyautogui.position()
    copied_coordinates.append((x, y))
    update_copied_coordinates_label()

# Fonction pour mettre à jour l'étiquette des coordonnées copiées
def update_copied_coordinates_label():
    copied_coordinates_label.config(text="\n".join([f"C-{i + 1}: X {x}, Y {y}" for i, (x, y) in enumerate(copied_coordinates)]))

# Événement de clic de la souris
def on_click(x, y, button, pressed):
    if pressed and button == mouse.Button.left:  # Clic gauche activé
        copy_coordinates()

# Interface tkinter
root = tk.Tk()
root.title("Affichage des Coordonnées de la Souris")
root.geometry("300x200")

# Rend la fenêtre modale pour la conserver au premier plan
root.grab_set()

coordinates_label = tk.Label(root, text="X: 0, Y: 0", font=("Helvetica", 16))
coordinates_label.pack(pady=20)

copy_button = tk.Button(root, text="Copier", command=copy_coordinates)
copy_button.pack()

copied_coordinates_label = tk.Label(root, text="", font=("Helvetica", 12))
copied_coordinates_label.pack(pady=10)

# Démarre la mise à jour des coordonnées en temps réel
update_coordinates()

# Démarre la détection de clics de la souris en arrière-plan
listener = mouse.Listener(on_click=on_click)
listener.start()

root.mainloop()
