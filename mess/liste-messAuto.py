from http.client import PROXY_AUTHENTICATION_REQUIRED
import pyautogui as pg
import time

time.sleep(2)

txt = open('liste.txt','r')

a = "n-"

for i in txt:
    pg.write(a+''+i)
    pg.sleep(1)
    pg.press('enter')
pg.sleep(3)
pg.typewrite("Good day ")
pg.sleep(1)
pg.press('enter')
pg.typewrite("Tob le bot")
pg.sleep(1)
pg.press('enter')



