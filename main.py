<!DOCTYPE html>
<html lang="pl">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TEST KRUKOWSKI SOR</title>
  <!-- Google Fonts -->
  <link href="https://fonts.googleapis.com/css?family=Roboto:400,500&display=swap" rel="stylesheet">
  <style>
    /* Animowane tło – podmień URL-e na własne */
    body::before, body::after {
      content: "";
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background-size: cover;
      background-position: center;
      z-index: -2;
      opacity: 0;
      animation: bgFade 30s infinite;
    }
    body::before {
      background-image: url('https://example.com/apple_orchard.gif'); /* filmik sadownika opryskującego sad jabłkowy */
      animation-delay: 0s;
    }
    body::after {
      background-image: url('https://example.com/grain_field.gif'); /* filmik oprysku wielkich połaci zboża */
      animation-delay: 15s;
    }
    @keyframes bgFade {
      0%, 40% { opacity: 1; }
      50%, 90% { opacity: 0; }
      100% { opacity: 1; }
    }

    /* Globalny ciemny motyw i czcionki */
    body {
      font-family: 'Roboto', sans-serif;
      background-color: #121212;
      color: #e0e0e0;
      margin: 20px;
      max-width: 800px;
      line-height: 1.6;
      position: relative;
    }
    h1, p {
      text-align: center;
    }
    /* Kontenery dla inputów z własnym autouzupełnianiem */
    .input-container {
      position: relative;
      margin-bottom: 20px;
    }
    label {
      display: block;
      margin-top: 15px;
      font-weight: 500;
    }
    input {
      width: 300px;
      padding: 8px;
      margin-top: 5px;
      border: 1px solid #333;
      border-radius: 4px;
      background-color: #1e1e1e;
      color: #e0e0e0;
      transition: border-color 0.3s;
    }
    input:focus {
      border-color: #bb86fc;
      outline: none;
    }
    button {
      margin-top: 20px;
      padding: 10px 20px;
      cursor: pointer;
      border: none;
      border-radius: 4px;
      background-color: #bb86fc;
      color: #121212;
      font-weight: 500;
      transition: background-color 0.3s, transform 0.2s;
    }
    button:hover {
      background-color: #9b68ea;
      transform: scale(1.02);
    }
    /* Własny dropdown autouzupełniania */
    .autocomplete-suggestions {
      position: absolute;
      top: 100%;
      left: 0;
      right: 0;
      background-color: #1e1e1e;
      border: 1px solid #333;
      border-top: none;
      z-index: 10;
      max-height: 200px;
      overflow-y: auto;
    }
    .suggestion-item {
      padding: 8px;
      cursor: pointer;
      transition: background 0.2s;
    }
    .suggestion-item:hover {
      background-color: #333;
    }
    /* Style kart wyników */
    .result-card {
      background-color: #1e1e1e;
      padding: 15px;
      margin-bottom: 15px;
      border-radius: 6px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.6);
    }
    .summary-row {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 10px;
      border-bottom: 1px solid #333;
      padding-bottom: 10px;
    }
    .primary-field {
      background: rgba(187, 134, 252, 0.2);
      padding: 5px 10px;
      border-radius: 4px;
      margin-bottom: 5px;
    }
    .result-card button {
      background-color: #bb86fc;
      border: none;
      border-radius: 4px;
      padding: 4px 8px;
      cursor: pointer;
      margin-left: auto;
    }
    .result-card button:hover {
      background-color: #9b68ea;
    }
    .detail-row {
      display: none;
      padding-top: 10px;
      margin-top: 10px;
    }
    .detail-row p {
      margin: 4px 0;
      font-size: 0.9em;
    }
    /* Styl dla przycisku "Oszacuj cenę" i pola z wynikiem */
    .price-container {
      margin-top: 10px;
    }
    .price-result {
      margin-top: 5px;
      font-style: italic;
      color: #bb86fc;
    }
    /* Responsywność */
    @media (max-width: 600px) {
      body {
        margin: 10px;
      }
      input {
        width: 100%;
        box-sizing: border-box;
      }
      button {
        width: 100%;
      }
    }
  </style>
</head>
<body>
  <h1>Interaktywna wyszukiwarka SOR</h1>
  <p>Wpisz fragment w jednym lub kilku polach. Wybierz podpowiedź, kliknij wyszukaj – wyniki pojawią się jako interaktywne karty.</p>

  <!-- Pola wyszukiwania z własnym autouzupełnianiem -->
  <div class="input-container">
    <label for="uprawaInput">Uprawa:</label>
    <input type="text" id="uprawaInput" placeholder="np. ziemniak">
    <div class="autocomplete-suggestions" id="uprawaSuggestions"></div>
  </div>
  <div class="input-container">
    <label for="agrofagInput">Agrofag:</label>
    <input type="text" id="agrofagInput" placeholder="np. stonka ziemniaczana">
    <div class="autocomplete-suggestions" id="agrofagSuggestions"></div>
  </div>
  <div class="input-container">
    <label for="nazwaInput">Nazwa środka:</label>
    <input type="text" id="nazwaInput" placeholder="np. Aceplan">
    <div class="autocomplete-suggestions" id="nazwaSuggestions"></div>
  </div>
  <div class="input-container">
    <label for="subInput">Substancja czynna:</label>
    <input type="text" id="subInput" placeholder="np. acetamipryd">
    <div class="autocomplete-suggestions" id="subSuggestions"></div>
  </div>

  <!-- Przycisk wyszukiwania -->
  <button onclick="wyszukaj()">Wyszukaj</button>

  <!-- Kontener na wyniki -->
  <div id="results"></div>

  <script>
    // USTAW: Adres Twojego API (bez końcowego slash)
    const API_BASE = "https://sor.onrender.com";

    // Globalne tablice z danymi do autouzupełniania
    let uprawaValues = [];
    let agrofagValues = [];
    let nazwaValues = [];
    let subValues = [];

    // Po załadowaniu strony pobieramy dane z API oraz inicjujemy autouzupełnianie
    window.addEventListener('DOMContentLoaded', async () => {
      await fetchDistinctValues();
      setupAutocomplete(document.getElementById("uprawaInput"), document.getElementById("uprawaSuggestions"), uprawaValues);
      setupAutocomplete(document.getElementById("agrofagInput"), document.getElementById("agrofagSuggestions"), agrofagValues);
      setupAutocomplete(document.getElementById("nazwaInput"), document.getElementById("nazwaSuggestions"), nazwaValues);
      setupAutocomplete(document.getElementById("subInput"), document.getElementById("subSuggestions"), subValues);
    });

    // Funkcja pobierająca dane distinct z API
    async function fetchDistinctValues() {
      try {
        const up = await fetch(`${API_BASE}/distinct?col=uprawa`).then(res => res.json());
        const ag = await fetch(`${API_BASE}/distinct?col=agrofag`).then(res => res.json());
        const na = await fetch(`${API_BASE}/distinct?col=nazwa`).then(res => res.json());
        const su = await fetch(`${API_BASE}/distinct?col=Substancja_czynna`).then(res => res.json());
        uprawaValues = up.distinct_values || [];
        agrofagValues = ag.distinct_values || [];
        nazwaValues = na.distinct_values || [];
        subValues = su.distinct_values || [];
      } catch(e) {
        console.error("Błąd pobierania danych distinct:", e);
      }
    }

    // Funkcja do ustawienia autouzupełniania dla danego inputa
    function setupAutocomplete(input, container, suggestions) {
      input.addEventListener("input", function() {
        const value = input.value.toLowerCase();
        container.innerHTML = "";
        if (!value) return;
        const filtered = suggestions.filter(s => s.toLowerCase().includes(value));
        filtered.forEach(s => {
          const div = document.createElement("div");
          div.classList.add("suggestion-item");
          div.textContent = s;
          div.addEventListener("mousedown", function(e) {
            input.value = s;
            container.innerHTML = "";
          });
          container.appendChild(div);
        });
      });
      input.addEventListener("blur", function() {
        setTimeout(() => { container.innerHTML = ""; }, 150);
      });
    }

    // Funkcja wyszukująca – buduje zapytanie do API i wyświetla wyniki jako karty
    async function wyszukaj() {
      const up = document.getElementById("uprawaInput").value.trim();
      const ag = document.getElementById("agrofagInput").value.trim();
      const na = document.getElementById("nazwaInput").value.trim();
      const su = document.getElementById("subInput").value.trim();
      let qs = [];
      if (up) qs.push(`uprawa=${encodeURIComponent(up)}`);
      if (ag) qs.push(`agrofag=${encodeURIComponent(ag)}`);
      if (na) qs.push(`nazwa=${encodeURIComponent(na)}`);
      if (su) qs.push(`Substancja_czynna=${encodeURIComponent(su)}`);
      let url = `${API_BASE}/search-all`;
      if (qs.length > 0) url += "?" + qs.join("&");
      try {
        const response = await fetch(url);
        const json = await response.json();
        displayResults(json);
      } catch(e) {
        document.getElementById("results").innerHTML = "<p>Błąd podczas wyszukiwania.</p>";
      }
    }

    // Funkcja wyświetlająca wyniki jako interaktywne karty
    function displayResults(data) {
      const resultsDiv = document.getElementById("results");
      resultsDiv.innerHTML = "";
      if (!data.results || data.results.length === 0) {
        resultsDiv.innerHTML = "<p>Brak wyników (0)</p>";
        return;
      }
      data.results.forEach(rec => {
        const card = document.createElement("div");
        card.classList.add("result-card");
        // Wiersz podsumowania z głównymi polami
        const summary = document.createElement("div");
        summary.classList.add("summary-row");
        const primaryFields = ["Nazwa", "Rodzaj", "Agrofag", "Uprawa"];
        primaryFields.forEach(field => {
          const fieldDiv = document.createElement("div");
          fieldDiv.classList.add("primary-field");
          fieldDiv.textContent = rec[field] || "";
          summary.appendChild(fieldDiv);
        });
        // Przycisk rozwijania szczegółów
        const toggleBtn = document.createElement("button");
        toggleBtn.textContent = "+";
        toggleBtn.addEventListener("click", () => {
          if(detail.style.display === "none" || detail.style.display === "") {
            detail.style.display = "block";
            toggleBtn.textContent = "-";
          } else {
            detail.style.display = "none";
            toggleBtn.textContent = "+";
          }
        });
        summary.appendChild(toggleBtn);
        card.appendChild(summary);
        // Sekcja szczegółów – pozostałe dane
        const detail = document.createElement("div");
        detail.classList.add("detail-row");
        detail.style.display = "none";
        for (const key in rec) {
          if (primaryFields.indexOf(key) === -1) {
            const p = document.createElement("p");
            p.textContent = `${key}: ${rec[key]}`;
            detail.appendChild(p);
          }
        }
        // Dodaj przycisk "Oszacuj cenę" oraz kontener na wynik
        const priceContainer = document.createElement("div");
        priceContainer.classList.add("price-container");
        const priceBtn = document.createElement("button");
        priceBtn.textContent = "Oszacuj cenę";
        const priceResult = document.createElement("div");
        priceResult.classList.add("price-result");
        priceContainer.appendChild(priceBtn);
        priceContainer.appendChild(priceResult);
        detail.appendChild(priceContainer);
        // Obsługa przycisku "Oszacuj cenę"
        priceBtn.addEventListener("click", () => {
          // Upewnij się, że pobieramy właściwą nazwę z pola "Nazwa"
          const effectiveName = rec["Nazwa"] && rec["Nazwa"].trim() ? rec["Nazwa"] : "nieznany środek";
          oszacujCene(effectiveName, priceResult);
        });
        card.appendChild(detail);
        resultsDiv.appendChild(card);
      });
    }

    // Funkcja symulująca wywołanie AI do oszacowania ceny
    function oszacujCene(nazwa, resultDiv) {
      if (!nazwa || nazwa.trim() === "") {
        resultDiv.textContent = "Nie znaleziono nazwy środka. Sprawdź dane.";
        return;
      }
      console.log("Oszacowywana nazwa:", nazwa);
      const promptText = `Jaka jest cena środka "${nazwa}" na polskim internecie w różnych opakowaniach? Zwróć średnią dla danych opakowań z rynku polskiego. Jeżeli brak takich informacji, zwróć: skontaktuj się z lokalnym dystrybutorem SOR.`;
      console.log("Prompt dla AI:", promptText);
      resultDiv.textContent = "Oszacowywanie ceny...";
      setTimeout(() => {
        if (Math.random() > 0.5) {
          let price = (Math.random() * 150 + 50).toFixed(2);
          resultDiv.textContent = `Średnia cena: ${price} PLN`;
        } else {
          resultDiv.textContent = "Skontaktuj się z lokalnym dystrybutorem SOR";
        }
      }, 1500);
    }
  </script>
</body>
</html>
