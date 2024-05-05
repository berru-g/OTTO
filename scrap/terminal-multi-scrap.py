from pyautogui import sleep
import requests
from bs4 import BeautifulSoup
from pyfiglet import Figlet
from colorama import Fore, Style

def poleemploi_search_job():
    f = Figlet(font='larry3D')
    print(f.renderText('Scrap'))
    g = Figlet(font='slant')
    print(g.renderText('*  emploi'))
    
    print(Fore.LIGHTBLUE_EX + "Pole emploi")
    print(Fore.LIGHTGREEN_EX + "Les jeudis")
    print(Fore.LIGHTYELLOW_EX + "Indeed")

    while True:
        print("╭─────────────────────────────╮")
        print("| Entrez le titre du poste:   |")
        print("╰─────────────────────────────╯")
        job = input("")
        print("╭─────────────────────────────╮")
        print("| Entrez l emplacement:       |")
        print("╰─────────────────────────────╯")
        location = input("")
        print(" ────────────────────────────")

        sites = [
            {
                "name": "Pôle Emploi",
                "url": "https://candidat.pole-emploi.fr/offres/recherche?&motsCles={}&lieux{}&offresPartenaires=true&rayon=10&tri=0",
                "selectors": {
                    "title": ".media-heading-title",
                    "subtitle": ".subtext",
                    "date": ".date",
                },
                "color": Fore.LIGHTBLUE_EX,
            },
            {
                "name": "Site Web 2",
                "url": "https://lesjeudis.com/jobs?title={}&location={}",
                "selectors": {
                    "title": ".h4 JobCard_text__2DNt5",
                    "subtitle": ".h6 JobCard_name__9_LXl",
                    "date": ".small-body-text",
                },
                "color": Fore.LIGHTGREEN_EX,
            },
            {
                "name": "Site Web 3",
                "url": "https://fr.indeed.com/jobs?q={}&l={}",
                "selectors": {
                    "title": ".jobTitle css-1u6tfqq eu4oa1w0",
                    "subtitle": ".companyName",
                    "date": ".date",
                },
                "color": Fore.LIGHTYELLOW_EX,
            },
        ]

        for site in sites:
            print(site["color"] + f"Résultats de la recherche sur {site['name']}:" + Style.RESET_ALL)
            site_url = site["url"].format(job, location)
            site_search = requests.get(site_url)
            site_soup = BeautifulSoup(site_search.text, "html.parser")
            site_titles = site_soup.select(site["selectors"]["title"])
            subtitles = site_soup.select(site["selectors"]["subtitle"])
            dates = site_soup.select(site["selectors"]["date"])

            for title, subtitle, date in zip(site_titles, subtitles, dates):
                print(site["color"] + title.text + Style.RESET_ALL)
                print(site["color"] + subtitle.text + Style.RESET_ALL)
                print(site["color"] + date.text + Style.RESET_ALL)
                print("__________")

            sleep(1)

        f = Figlet(font='slant')
        print(f.renderText('?'))
        print("Nouvelle recherche")

        user_input = input("Voulez-vous effectuer une nouvelle recherche ? (Oui/Non): ")
        if user_input.lower() != 'oui':
            exit()  # Quitte la boucle si l'utilisateur ne veut pas effectuer une nouvelle recherche


if __name__ == "__main__":
    poleemploi_search_job()
    exit()
