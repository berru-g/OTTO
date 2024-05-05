from pyautogui import sleep
import requests
from bs4 import BeautifulSoup
from pyfiglet import Figlet

def poleemploi_search_job():
    f = Figlet(font='slant')
    print(f.renderText('PolAmploa scrap basic'))
    print("╭─────────────────────────────╮")
    print("| Entrez le titre du poste:   |")
    print("╰─────────────────────────────╯")
    job = input("")
    print("╭─────────────────────────────╮")
    print("| Entrez l emplacement:       |")
    print("╰─────────────────────────────╯")
    location = input("")
    print(" ────────────────────────────")

    poleemploi_url = "https://candidat.pole-emploi.fr/offres/recherche?&motsCles={}&lieux{}&offresPartenaires=true&rayon=10&tri=0"

    while True:
        poleemploi_search = requests.get(poleemploi_url.format(job, location))
        poleemploi_soup = BeautifulSoup(poleemploi_search.text, "html.parser")
        poleemploi_titles = poleemploi_soup.find_all(class_="media-heading-title")
        subtitles = poleemploi_soup.find_all(class_="subtext")
        dates = poleemploi_soup.find_all(class_="date")

        print("Résultats de la recherche sur Pole Emploi:")

        for title, subtitle, date in zip(poleemploi_titles, subtitles, dates):
            print(title.text)
            print(subtitle.text)
            print(date.text)
            print("__________")

        sleep(1)

        f = Figlet(font='slant')
        print(f.renderText('PolAmploa'))
        print("Nouvelle recherche")
        print("╭─────────────────────────────╮")
        print("| Entrez le titre du poste:   |")
        print("╰─────────────────────────────╯")
        job = input("")
        print("╭─────────────────────────────╮")
        print("| Entrez l emplacement:       |")
        print("╰─────────────────────────────╯")
        location = input("")

        user_input = input("Voulez-vous effectuer une nouvelle recherche ? (Oui/Non): ")
        if user_input.lower() != 'oui':
            break  # Quitte la boucle si l'utilisateur ne veut pas effectuer une nouvelle recherche

    sleep(20)

poleemploi_search_job()
exit()
