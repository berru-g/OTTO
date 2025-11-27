import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from collections import Counter
import time
import re
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="Pain Scraper - Reddit",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé pour une app plus moderne
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(45deg, #FF4B4B, #FF6B6B);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #FF6B6B;
        margin: 1rem 0;
    }
    .problem-card {
        background: #1E1E1E;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #FF6B6B;
        margin: 1rem 0;
    }
    .metric-card {
        background: #2E2E2E;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
    .source-tag {
        background: #FF6B6B;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.8rem;
        margin: 0.2rem;
    }
</style>
""", unsafe_allow_html=True)

# Liste de mots-clés de douleur (gardée de ton code original)
PAIN_KEYWORDS = [
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
        st.error(f"❌ Erreur API: {e}")
        return []

def scrape_reddit_posts(niche, subreddits, post_count):
    """Fonction principale de scraping"""
    all_problems = []
    
    for site in subreddits:
        with st.spinner(f"🔍 Analyse de {site['name']}..."):
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                
                site_search = requests.get(site["url"], headers=headers, timeout=10)
                
                if site_search.status_code != 200:
                    st.warning(f"Reddit bloque {site['name']}, utilisation de l'API...")
                    api_posts = search_reddit_api(niche, site["subreddit"], post_count)
                    for post_data in api_posts:
                        post_text = post_data["text"].lower()
                        found_pains = [kw for kw in PAIN_KEYWORDS if kw in post_text]
                        if found_pains:
                            all_problems.append({
                                'text': post_text,
                                'pains': found_pains,
                                'source': site['name'],
                                'url': post_data["url"],
                                'title': post_data["text"][:100] + "..."
                            })
                else:
                    site_soup = BeautifulSoup(site_search.text, "html.parser")
                    
                    posts = (
                        site_soup.select("h3._eYtD2XCVieq6emjKBH3m") or
                        site_soup.select("a[data-click-id='body']") or
                        site_soup.select("shreddit-post") or
                        site_soup.find_all('h3') or
                        []
                    )
                    
                    if not posts:
                        st.warning(f"Aucun post trouvé sur {site['name']}, utilisation de l'API...")
                        api_posts = search_reddit_api(niche, site["subreddit"], post_count)
                        for post_data in api_posts:
                            post_text = post_data["text"].lower()
                            found_pains = [kw for kw in PAIN_KEYWORDS if kw in post_text]
                            if found_pains:
                                all_problems.append({
                                    'text': post_text,
                                    'pains': found_pains,
                                    'source': site['name'],
                                    'url': post_data["url"],
                                    'title': post_data["text"][:100] + "..."
                                })
                    else:
                        for i, post in enumerate(posts[:post_count]):
                            post_text = getattr(post, 'text', str(post)).lower()
                            
                            post_url = "URL non disponible"
                            parent = post.find_parent('a')
                            if parent and parent.get('href'):
                                href = parent.get('href')
                                if href.startswith('/'):
                                    post_url = f"https://reddit.com{href}"
                                elif 'reddit.com' in href:
                                    post_url = href
                            
                            found_pains = [kw for kw in PAIN_KEYWORDS if kw in post_text]
                            
                            if found_pains:
                                problem_data = {
                                    'text': post_text,
                                    'pains': found_pains,
                                    'source': site['name'],
                                    'url': post_url,
                                    'title': post_text[:100] + "..."
                                }
                                all_problems.append(problem_data)
                
                time.sleep(2)  # Pause anti-rate limiting
                
            except Exception as e:
                st.error(f"❌ Erreur sur {site['name']}: {e}")
                # Fallback API
                try:
                    api_posts = search_reddit_api(niche, site["subreddit"], post_count)
                    for post_data in api_posts:
                        post_text = post_data["text"].lower()
                        found_pains = [kw for kw in PAIN_KEYWORDS if kw in post_text]
                        if found_pains:
                            all_problems.append({
                                'text': post_text,
                                'pains': found_pains,
                                'source': site['name'],
                                'url': post_data["url"],
                                'title': post_data["text"][:100] + "..."
                            })
                except Exception as api_error:
                    st.error(f"❌ Échec de l'API aussi: {api_error}")
    
    return all_problems

def main():
    # Header principal
    st.markdown('<div class="main-header">🔍 PAIN SCRAPER</div>', unsafe_allow_html=True)
    st.markdown("### Découvrez les problèmes réels des designers & développeurs sur Reddit")
    
    # Sidebar pour les paramètres
    with st.sidebar:
        st.header("⚙️ Paramètres de recherche")
        
        niche = st.text_input(
            "**Niche/Métier à analyser**",
            placeholder="ex: animation, 3D, responsive design...",
            help="Le domaine dans lequel vous cherchez des problèmes"
        )
        
        post_count = st.slider(
            "**Nombre de posts à analyser par subreddit**",
            min_value=5,
            max_value=50,
            value=15,
            help="Plus de posts = analyse plus complète mais plus longue"
        )
        
        # Sélection des subreddits
        st.subheader("🎯 Subreddits à analyser")
        subreddit_options = {
            "Reddit r/web_design": "web_design",
            "Reddit r/Frontend": "Frontend", 
            "Reddit r/threejs": "threejs",
            "Reddit r/graphic_design": "graphic_design"
        }
        
        selected_subreddits = []
        for name, sub in subreddit_options.items():
            if st.checkbox(name, value=True):
                selected_subreddits.append({
                    "name": name,
                    "subreddit": sub,
                    "url": f"https://www.reddit.com/r/{sub}/search/?q={niche if niche else 'design'}&restrict_sr=1&sort=relevance"
                })
        
        st.markdown("---")
        st.info("""
        **💡 Comment ça marche:**
        - Le scraper analyse les posts Reddit
        - Détecte les mots-clés de "douleur"
        - Identifie les problèmes récurrents
        - Vous donne des idées de solutions SaaS
        """)
    
    # Bouton de recherche principal
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Lancer l'analyse des douleurs", type="primary", use_container_width=True):
            if not niche:
                st.error("❌ Veuillez entrer une niche à analyser")
                return
                
            if not selected_subreddits:
                st.error("❌ Veuillez sélectionner au moins un subreddit")
                return
            
            # Lancement du scraping
            with st.spinner("🔎 Analyse en cours... Cette opération peut prendre quelques minutes"):
                problems = scrape_reddit_posts(niche, selected_subreddits, post_count)
            
            # Affichage des résultats
            if problems:
                display_results(problems, niche)
            else:
                st.error("""
                ❌ Aucun problème détecté dans cette niche.
                
                **💡 Suggestions:**
                - Essayez d'autres mots-clés (ex: 'animation', 'scroll', '3D performance')
                - Vérifiez l'orthographe
                - Les subreddits peuvent être trop spécifiques
                """)
    
    # Section d'exemples si pas de recherche
        else:
            st.markdown("---")
            st.subheader("🎯 Exemples de niches à tester")
        
            examples_col1, examples_col2, examples_col3 = st.columns(3)
        
        with examples_col1:
            if st.button("🎨 Animation Web", use_container_width=True):
                st.session_state.niche_example = "animation"
            if st.button("📱 Responsive Design", use_container_width=True):
                st.session_state.niche_example = "responsive design"
                
        with examples_col2:
            if st.button("⚡ Performance", use_container_width=True):
                st.session_state.niche_example = "performance"
            if st.button("🎭 3D Web", use_container_width=True):
                st.session_state.niche_example = "3D"
                
        with examples_col3:
            if st.button("🔍 SEO", use_container_width=True):
                st.session_state.niche_example = "SEO"
            if st.button("🎯 UX Design", use_container_width=True):
                st.session_state.niche_example = "UX"
        
        if hasattr(st.session_state, 'niche_example'):
            st.info(f"💡 Exemple sélectionné: **{st.session_state.niche_example}** - Modifiez dans la sidebar si besoin")

def display_results(problems, niche):
    """Affiche les résultats de l'analyse"""
    
    st.success(f"✅ **{len(problems)} problèmes identifiés** dans la niche: **{niche}**")
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Problèmes trouvés", len(problems))
    
    with col2:
        # Compter les douleurs uniques
        all_pains = [pain for problem in problems for pain in problem['pains']]
        st.metric("Douleurs détectées", len(set(all_pains)))
    
    with col3:
        # Sources uniques
        sources = set(problem['source'] for problem in problems)
        st.metric("Subreddits actifs", len(sources))
    
    with col4:
        # Douleur la plus fréquente
        pain_counter = Counter([pain for problem in problems for pain in problem['pains']])
        if pain_counter:
            top_pain = pain_counter.most_common(1)[0]
            st.metric("Douleur principale", f"{top_pain[0]} ({top_pain[1]})")
    
    # Analyse des douleurs
    st.markdown("---")
    st.subheader("📊 Analyse des douleurs les plus fréquentes")
    
    pain_counter = Counter([pain for problem in problems for pain in problem['pains']])
    source_counter = Counter(problem['source'] for problem in problems)
    
    # Graphiques
    col1, col2 = st.columns(2)
    
    with col1:
        if pain_counter:
            top_pains_df = pd.DataFrame(pain_counter.most_common(10), columns=['Douleur', 'Fréquence'])
            st.bar_chart(top_pains_df.set_index('Douleur'))
    
    with col2:
        if source_counter:
            sources_df = pd.DataFrame(source_counter.most_common(), columns=['Source', 'Problèmes'])
            st.bar_chart(sources_df.set_index('Source'))
    
    # Liste détaillée des problèmes
    st.markdown("---")
    st.subheader("🔍 Problèmes détectés")
    
    for i, problem in enumerate(problems):
        with st.container():
            st.markdown(f"""
            <div class="problem-card">
                <h4>🚨 Problème #{i+1} - <span class="source-tag">{problem['source']}</span></h4>
                <p><strong>Post:</strong> {problem['title']}</p>
                <p><strong>Douleurs détectées:</strong> {', '.join(problem['pains'])}</p>
                <p><strong>🔗 </strong><a href="{problem['url']}" target="_blank">{problem['url']}</a></p>
            </div>
            """, unsafe_allow_html=True)
    
    # Suggestions d'idées SaaS
    st.markdown("---")
    st.subheader("💡 Idées de solutions SaaS potentielles")
    
    if pain_counter:
        top_pains = [pain for pain, count in pain_counter.most_common(5)]
        
        for i, pain in enumerate(top_pains, 1):
            with st.expander(f"🚀 Idée #{i}: Solution pour **'{pain}'**"):
                st.markdown(f"""
                **Problème:** Les utilisateurs rencontrent fréquemment des difficultés avec **{pain}**
                
                **Solution potentielle:**
                - Outil automatisé pour résoudre les problèmes de {pain}
                - Plugin/extension qui simplifie le processus
                - Service qui élimine la frustration liée à {pain}
                - Template/boilerplate pour éviter {pain}
                
                **Marché:** {len([p for p in problems if pain in p['pains']])} posts Reddit identifiés
                """)
    
    # Export des données
    st.markdown("---")
    st.subheader("📤 Export des données")
    
    if problems:
        # Préparation des données pour export
        export_data = []
        for problem in problems:
            export_data.append({
                'Source': problem['source'],
                'Titre': problem['title'],
                'Douleurs': ', '.join(problem['pains']),
                'URL': problem['url'],
                'Texte_complet': problem['text'][:500] + "..."
            })
        
        df = pd.DataFrame(export_data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Télécharger CSV",
                data=csv,
                file_name=f"reddit_pains_{niche}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            json_str = df.to_json(orient='records', indent=2)
            st.download_button(
                label="📥 Télécharger JSON",
                data=json_str,
                file_name=f"reddit_pains_{niche}_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )

if __name__ == "__main__":
    main()