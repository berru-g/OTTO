# clicker automatique
import pyautogui
import tkinter as tk
from tkinter import messagebox

def run_script():
    for n in range(100):
        pyautogui.click(1841, 850)
        pyautogui.sleep(0.6)
        pyautogui.click(452, 841)
        pyautogui.sleep(0.6)
        pyautogui.click(1147, 844)
        pyautogui.sleep(0.9)
    
    # Afficher un pop-up de confirmation
    messagebox.showinfo("OTTO", "Session terminée")

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Cacher la fenêtre principale

    run_script()
