import pyautogui as pt
from time import sleep
import cv2  # Assurez-vous que opencv-python-headless est installé

class Clicker:
    def __init__(self, target_png, speed):
        self.target_png = target_png
        self.speed = speed
        pt.FAILSAFE = True

    def nav_to_image(self):
        try:
            position = pt.locateOnScreen(self.target_png, confidence=0.9)
            if position is not None:
                print(f"Image found at: {position}")
                pt.moveTo(position[0] + 15, position[1] + 15, duration=self.speed)
                pt.click()
                print("Clicked on the image.")
                sleep(0.5)
            else:
                print("Image not found on screen.")
                return 0
        except Exception as e:
            print(f"Error: {e}")
            return 0

if __name__ == '__main__':
    clicker = Clicker('like.png', speed=0.5)
    sleep(1)
    end = 0

    while True:
        if clicker.nav_to_image() == 0:
            end += 1
            pt.scroll(-1200)
            sleep(0.8)

        # End the loop
        if end > 100:
            break

    print("Session terminée")
