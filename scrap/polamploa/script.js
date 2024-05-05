document.getElementById('searchButton').addEventListener('click', function () {
    var jobTitle = document.getElementById('jobTitle').value;
    var location = document.getElementById('location').value;
    var resultsDiv = document.getElementById('results');

    // URL du site à scraper
    var siteUrl = "https://candidat.pole-emploi.fr/offres/recherche?&motsCles=" + jobTitle + "&lieux=" ;

    // Effectuer une requête AJAX pour obtenir le contenu de la page web
    var xhr = new XMLHttpRequest();
    xhr.open("GET", siteUrl, true);
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            var responseText = xhr.responseText;
            var parser = new DOMParser();
            var doc = parser.parseFromString(responseText, "text/html");

            // Utilisez des sélecteurs CSS pour extraire les données du DOM
            var titles = doc.querySelectorAll(".media-heading-title");
            var subtitles = doc.querySelectorAll(".subtext");
            var dates = doc.querySelectorAll(".date");

            // Afficher les résultats dans la page HTML
            var resultsHTML = "<h2>Résultats de la recherche :</h2>";

            for (var i = 0; i < titles.length; i++) {
                resultsHTML += "<p>" + titles[i].textContent + "</p>";
                resultsHTML += "<p>" + subtitles[i].textContent + "</p>";
                resultsHTML += "<p>" + dates[i].textContent + "</p>";
                resultsHTML += "__________";
            }

            resultsDiv.innerHTML = resultsHTML;
        }
    };

    xhr.send();
});