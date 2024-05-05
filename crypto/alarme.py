import requests
from bs4 import BeautifulSoup
import time
import winsound
from pyfiglet import Figlet
import winsound

# Définissez des notes (fréquence en Hz) et des durées (en millisecondes)
notes = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25]
durations = [500, 500, 500, 500, 500, 500, 500, 500]

# Jouez la mélodie en utilisant les notes et les durées définies
for note, duration in zip(notes, durations):
    winsound.Beep(int(note), duration)


f = Figlet(font='slant')
print(f.renderText('Crypto'))
print("*         Alarm          *")
time.sleep(1)
winsound.Beep(500, 500)
winsound.Beep(1000, 500)
winsound.Beep(1500, 500)
winsound.Beep(1000, 500)
winsound.Beep(440, 500)

def fetch_price():
    url = "https://www.binance.com/fr/trade/BITCOIN_USDT?type=spot"
    headers = {"User-Agent": "Mozilla/5.0"}  # Utilisation d'un User-Agent pour éviter le blocage par le site
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            price_element = soup.find(class_="showPrice")
            if price_element:
                return price_element.text.strip()
    except Exception as e:
        print(f"Erreur : {e}")
    return None
print("* site ok ---")
def main():
    while True:
        print("loop**")
        price = fetch_price()
        if price:
            print(f"Prix actuel : {price}")

            # Convertir le prix en nombre à virgule flottante (float)
            try:
                price_float = float(price)
            except ValueError:
                price_float = 0.0  # En cas d'erreur de conversion

            # Vérifier les conditions et produire une alerte sonore si nécessaire
            if 4.60 <= price_float <= 4.1:
                winsound.Beep(1000, 500)  # Produire une alerte sonore (1 kHz pendant 500 ms)
                print("vendre ou acheter NOW")
        time.sleep(60)  # Attendre 60 secondes avant la prochaine vérification

if __name__ == "__main__":
    main()
