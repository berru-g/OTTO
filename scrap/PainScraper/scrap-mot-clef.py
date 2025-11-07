from pyautogui import sleep
import requests
from bs4 import BeautifulSoup
from pyfiglet import Figlet
from colorama import Fore, Style
import time
from collections import Counter
import re
# Obj : 
# tester de scraper reddit pour trouver des problèmes dans une niche donnée via des mots-clés de "douleur", afin de résoudre cette problématique avec un futur tool, (SaaS).
def search_reddit_api(niche, subreddit="web_design", limit=10):
    """Solution de secours avec l'API Reddit"""
    try:
        url = f"https://www.reddit.com/r/{subreddit}/search.json?q={niche}&restrict_sr=1&sort=relevance&limit={limit}"
        headers = {'User-Agent': 'PainScraper/1.0 by berru-g'}
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            posts = []
            for post in data['data']['children'][:limit]:
                title = post['data']['title']
                selftext = post['data']['selftext']
                url = f"https://reddit.com{post['data']['permalink']}"
                posts.append({"text": f"{title} {selftext}", "url": url})
            return posts
        return []
    except Exception as e:
        print(f"   ❌ API Error: {e}")
        return []

def reddit_pain_scraper():
    f = Figlet(font='slant')
    print(f.renderText('Pain Scraper'))
    g = Figlet(font='small')
    print(g.renderText('Reddit/IndieHackers'))
    
    print(Fore.LIGHTBLUE_EX + "Reddit r/frontend")
    print(Fore.LIGHTGREEN_EX + "Reddit r/web_design") 
    print(Fore.LIGHTYELLOW_EX + "Reddit r/threejs")
    print(Fore.LIGHTMAGENTA_EX + "Reddit r/graphic_design")
    print(Fore.LIGHTWHITE_EX + "Changer les subreddit dans le code si besoin")

    # Liste de mots-clés détectant des problèmes - Version design/tech
    pain_keywords = [
        # Problèmes et difficultés
        "problème", "problèmes", "difficile", "difficulté", "difficultés", 
        "galère", "galérer", "compliqué", "complexe", "pas facile",
        "impossible", "ne marche pas", "bug", "buggé", "plantage",
        "erreur", "dysfonctionnement", "ne fonctionne pas", "crash",
        
        # Frustrations et émotions négatives
        "frustrant", "frustration", "énervant", "agaçant", "horrible",
        "nul", "nulle", "pourri", "bizarre", "étrange",
        "penible", "chiant", "insupportable", "désagréable",
        "décourageant", "démotivant", "fatiguant", "épuisant",
        
        # Temps et productivité
        "perte de temps", "trop long", "long", "chronophage", 
        "fastidieux", "répétitif", "manuel", "manuellement",
        "inefficace", "lent", "lenteur", "ralentissement",
        "duplicate", "doublon", "refaire", "recommencer",
        
        # Coûts et argent
        "cher", "chère", "trop cher", "coûteux", "coûteuse",
        "hors de prix", "abonnement", "facturation", "tarif",
        "gratuit", "payant", "trop paye", "argent", "coût",
        
        # Recherche d'alternatives
        "alternative", "remplacer", "changer", "autre solution",
        "meilleur", "meilleure", "mieux", "comparer",
        "équivalent", "similaire", "solutions", "options",
        
        # Questions et aide
        "comment", "pourquoi", "aide", "aidez", "help",
        "solution", "résoudre", "corriger", "réparer",
        "conseil", "avis", "recommandez", "suggestions",
        
        # Manques et limitations
        "manque", "il manque", "absence", "pas de", "sans",
        "limitation", "limitée", "restreint", "insuffisant",
        "incomplet", "basique", "simple", "trop simple",
        
        # Apprentissage et compréhension
        "comprendre", "comprends pas", "expliquer",
        "débutant", "nouveau", "nouvelle", "apprendre",
        "tutoriel", "guide", "formation", "documentation",
        
        # Spécifique design/tech
        "client", "clients", "révision", "modification", "feedback",
        "deadline", "inspiration", "creative block", "idées",
        "software", "outil", "adobe", "figma", "sketch", "photoshop",
        "performance", "optimisation", "loading", "seo", "accessibility",
        "animation", "scroll", "3D", "three.js", "webgl", "canvas",
        "responsive", "mobile", "cross-browser", "compatibility",
        "plugin", "extension", "library", "framework",
        "budget", "prix", "tarif", "facturation", "contrat",
        "template", "copier", "original", "unique",
        
        # Expressions courantes de plainte
        "je ne sais pas", "je sais pas", "perdu", "bloqué",
        "ça marche pas", "fonctionne pas", "sos",
        "urgence", "important", "critique", "grave",
        "normal", "anormal", "logique", "illogique",
        
        # Satisfaction négative
        "déçu", "déçue", "déception", "insatisfait", "insatisfaite",
        "regrette", "décommandé", "annulé", "abandonné",
        
        # Recherche active
        "quelqu'un", "qqun", "des gens", "personne",
        "qui", "où", "quand", "combien", "quel",
        
        # Intégration et compatibilité
        "compatible", "intégration", "import", "export",
        "connecter", "lien", "synchronisation", "sync"
    ]

    while True:
        print("╭─────────────────────────────╮")
        print("| Entrez la niche/métier:     |")
        print("╰─────────────────────────────╯")
        niche = input("").strip().lower()
        
        print("╭─────────────────────────────╮")
        print("| Combien de posts analyser?  |")
        print("╰─────────────────────────────╯")
        try:
            post_count = int(input(""))
        except:
            post_count = 10

        print(" ────────────────────────────")

        sites = [
            {
                "name": "Reddit r/web_design",
                "url": f"https://www.reddit.com/r/web_design/search/?q={niche}&restrict_sr=1&sort=relevance",
                "subreddit": "web_design",
                "color": Fore.LIGHTBLUE_EX,
            },
            {
                "name": "Reddit r/Frontend", 
                "url": f"https://www.reddit.com/r/Frontend/search/?q={niche}&restrict_sr=1&sort=relevance",
                "subreddit": "Frontend",
                "color": Fore.LIGHTGREEN_EX,
            },
            {
                "name": "Reddit r/threejs",
                "url": f"https://www.reddit.com/r/threejs/search/?q={niche}&restrict_sr=1&sort=relevance",
                "subreddit": "threejs",
                "color": Fore.LIGHTYELLOW_EX,
            },
            {
                "name": "Reddit r/graphic_design",
                "url": f"https://www.reddit.com/r/graphic_design/search/?q={niche}&restrict_sr=1&sort=relevance",
                "subreddit": "graphic_design",
                "color": Fore.LIGHTMAGENTA_EX,
            }
        ]

        all_problems = []
        
        for site in sites:
            print(site["color"] + f"\n🔍 Analyse de {site['name']}..." + Style.RESET_ALL)
            
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                
                site_search = requests.get(site["url"], headers=headers, timeout=10)
                print(f"   📡 Statut HTTP: {site_search.status_code}")
                print(f"   📏 Taille réponse: {len(site_search.text)} caractères")
                
                if site_search.status_code != 200:
                    print(f"   ❌ Reddit bloque la requête, utilisation de l'API...")
                    api_posts = search_reddit_api(niche, site["subreddit"], post_count)
                    for post_data in api_posts:
                        post_text = post_data["text"].lower()
                        found_pains = [kw for kw in pain_keywords if kw in post_text]
                        if found_pains:
                            all_problems.append({
                                'text': post_text,
                                'pains': found_pains,
                                'source': site['name'],
                                'url': post_data["url"]
                            })
                else:
                    site_soup = BeautifulSoup(site_search.text, "html.parser")
                    
                    # ESSAIE DIFFÉRENTS SÉLECTEURS (Reddit change souvent)
                    posts = (
                        site_soup.select("h3._eYtD2XCVieq6emjKBH3m") or  # Nouveau sélecteur
                        site_soup.select("a[data-click-id='body']") or    # Ancien sélecteur
                        site_soup.select("a.title") or                    # Très ancien
                        site_soup.select("shreddit-post") or              # Très récent
                        site_soup.find_all('h3') or                       # Fallback large
                        []
                    )
                    
                    if not posts:
                        print(f"   ❌ Aucun post trouvé avec le scraping, utilisation de l'API...")
                        api_posts = search_reddit_api(niche, site["subreddit"], post_count)
                        for post_data in api_posts:
                            post_text = post_data["text"].lower()
                            found_pains = [kw for kw in pain_keywords if kw in post_text]
                            if found_pains:
                                all_problems.append({
                                    'text': post_text,
                                    'pains': found_pains,
                                    'source': site['name'],
                                    'url': post_data["url"]
                                })
                    else:
                        print(f"   ✅ {len(posts)} posts trouvés via scraping")
                        
                        # Pour le scraping, on va aussi essayer de récupérer les URLs
                        site_problems = []
                        for i, post in enumerate(posts[:post_count]):
                            post_text = getattr(post, 'text', str(post)).lower()
                            
                            # Essayer de trouver l'URL associée
                            post_url = "URL non disponible (scraping)"
                            parent = post.find_parent('a')
                            if parent and parent.get('href'):
                                href = parent.get('href')
                                if href.startswith('/'):
                                    post_url = f"https://reddit.com{href}"
                                elif 'reddit.com' in href:
                                    post_url = href
                            
                            # Détection des mots de douleur
                            found_pains = []
                            for keyword in pain_keywords:
                                if keyword in post_text:
                                    found_pains.append(keyword)
                            
                            if found_pains:
                                problem_data = {
                                    'text': post_text,
                                    'pains': found_pains,
                                    'source': site['name'],
                                    'url': post_url
                                }
                                site_problems.append(problem_data)
                                
                                print(site["color"] + f"🚨 Problème détecté ({len(found_pains)} douleurs):")
                                print(f"   \"{post_text[:100]}...\"")
                                print(f"   Douleurs: {', '.join(found_pains)}")
                                print(f"   🔗 {post_url}" + Style.RESET_ALL)
                                print("   " + "─" * 50)
                        
                        all_problems.extend(site_problems)
                        print(site["color"] + f"✅ {len(site_problems)} problèmes trouvés sur {site['name']}" + Style.RESET_ALL)
                
            except Exception as e:
                print(f"❌ Erreur sur {site['name']}: {e}")
                # Fallback à l'API en cas d'erreur
                try:
                    print(f"   🚑 Tentative de sauvetage avec l'API...")
                    api_posts = search_reddit_api(niche, site["subreddit"], post_count)
                    for post_data in api_posts:
                        post_text = post_data["text"].lower()
                        found_pains = [kw for kw in pain_keywords if kw in post_text]
                        if found_pains:
                            all_problems.append({
                                'text': post_text,
                                'pains': found_pains,
                                'source': site['name'],
                                'url': post_data["url"]
                            })
                    print(site["color"] + f"✅ {len([p for p in all_problems if p['source'] == site['name']])} problèmes trouvés via API" + Style.RESET_ALL)
                except Exception as api_error:
                    print(f"   ❌ Échec de l'API aussi: {api_error}")
            
            sleep(2)  # Pause pour éviter le rate limiting

        # Analyse agrégée
        if all_problems:
            print(Fore.MAGENTA + "\n" + "═" * 60)
            print("📊 ANALYSE FINALE DES DOULEURS")
            print("═" * 60)
            
            # Comptage des douleurs les plus fréquentes
            pain_counter = Counter()
            source_counter = Counter()
            
            for problem in all_problems:
                pain_counter.update(problem['pains'])
                source_counter[problem['source']] += 1
            
            print("🎯 DOULEURS LES PLUS FRÉQUENTES:")
            for pain, count in pain_counter.most_common(8):
                print(f"   • {pain}: {count} occurrences")
            
            print(f"\n📈 RÉPARTITION PAR SOURCE:")
            for source, count in source_counter.most_common():
                print(f"   • {source}: {count} problèmes")
            
            print(f"\n🔗 LIENS VERS LES PROBLÈMES:")
            for i, problem in enumerate(all_problems[:10], 1):  # Affiche les 10 premiers
                print(f"   {i}. {problem['source']}")
                print(f"      {problem['url']}")
                if i == 10 and len(all_problems) > 10:
                    print(f"      ... et {len(all_problems) - 10} autres problèmes")
                    break
            
            print(f"\n📊 TOTAL: {len(all_problems)} problèmes identifiés")
            
            # Suggestions d'idées basées sur les douleurs
            top_pains = [pain for pain, count in pain_counter.most_common(3)]
            if top_pains:
                print(f"\n💡 IDÉES POTENTIELLES:")
                for i, pain in enumerate(top_pains, 1):
                    print(f"   {i}. Outil pour résoudre: '{pain}'")
                    
        else:
            print(Fore.RED + "\n❌ Aucun problème détecté dans cette niche." + Style.RESET_ALL)
            print("💡 Suggestions:")
            print("   • Essayez d'autres mots-clés (ex: 'animation', 'scroll', '3D performance')")
            print("   • Vérifiez votre connexion internet")
            print("   • Les subreddits peuvent être trop spécifiques")

        print(Fore.CYAN + "\n" + "?" * 50)
        user_input = input("Nouvelle recherche ? (Oui/Non): ")
        if user_input.lower() != 'oui':
            print("👋 Bonne chance pour trouver les prochaines idées!")
            break

if __name__ == "__main__":
    reddit_pain_scraper()