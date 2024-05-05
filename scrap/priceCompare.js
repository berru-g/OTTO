// Importer la bibliothèque Axios pour effectuer des requêtes HTTP
const axios = require('axios');
// Importer la bibliothèque Cheerio pour analyser le HTML
const cheerio = require('cheerio');

// Fonction pour effectuer une recherche sur Leroy Merlin
async function searchOnLeroyMerlin(product) {
  const leroyMerlinURL = `https://www.leroymerlin.fr/search?q=${product}`;
  try {
    // Effectuer une requête HTTP GET
    const response = await axios.get(leroyMerlinURL);
    if (response.status === 200) {
      // Analyser le HTML de la page
      const $ = cheerio.load(response.data);
      const titles = $('.km-tile-designation');
      const subtitles = $('.mu-ml-050');
      const prices = $('.js-main-price');

      // Afficher les résultats
      console.log('Résultats de la recherche du concurrent 1:');
      titles.each((index, element) => {
        const title = $(element).text();
        const subtitle = $(subtitles[index]).text();
        const price = $(prices[index]).text();
        console.log(title);
        console.log(subtitle);
        console.log(price);
        console.log('__________');
      });
    } else {
      console.log('Erreur lors de la requête HTTP.');
    }
  } catch (error) {
    console.error('Une erreur s\'est produite :', error);
  }
}

// Obtenir l'entrée de l'utilisateur
const readline = require('readline');
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

rl.question('Entrez le produit recherché: ', (product) => {
  searchOnLeroyMerlin(product);
  rl.close();
});
