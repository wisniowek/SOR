from fastapi import FastAPI, HTTPException, Query
from sentence_transformers import SentenceTransformer, util
import pandas as pd
from pathlib import Path

app = FastAPI()

# Ścieżka do pliku Excel
EXCEL_PATH = Path(__file__).parent / "Rejestr_zastosowanie.xlsx"

# Model AI do podobieństw tekstu
model = SentenceTransformer("paraphrase-MiniLM-L6-v2")

# Funkcja do wczytania danych
def load_excel():
    if not EXCEL_PATH.exists():
        raise FileNotFoundError(f"Brak pliku: {EXCEL_PATH}")
    
    # Wczytaj dane z arkusza
    df = pd.read_excel(EXCEL_PATH, sheet_name="Rejestr_zastosowanie")

    # Połącz wszystkie kolumny w jedną kolumnę 'opis' jako tekst
    df["opis"] = df.astype(str).agg(" ".join, axis=1)

    # Zakoduj każdy opis do wektora
    df["vector"] = df["opis"].apply(lambda x: model.encode(x, convert_to_tensor=True))

    return df

# Wczytaj dane na start
try:
    df = load_excel()
    print("✅ Dane z Excela i model AI zostały załadowane")
except Exception as e:
    df = None
    print(f"❌ Błąd przy ładowaniu danych: {e}")

# Endpoint testowy
@app.get("/")
def root():
    return {"message": "Witaj w API SOR z wyszukiwarką AI!"}

# Endpoint rekomendacji
@app.get("/recommend")
def recommend(query: str = Query(...), show_all: bool = False):
    if df is None:
        raise HTTPException(500, "Dane z Excela nie zostały wczytane")

    # Wektor zapytania użytkownika
    q_vec = model.encode(query, convert_to_tensor=True)

    # Oblicz podobieństwo kosinusowe między zapytaniem a każdym opisem
    df["similarity"] = df["vector"].apply(lambda v: util.pytorch_cos_sim(q_vec, v).item())

    # Filtrowanie wyników z similarity > 0.5
    result = df[df["similarity"] > 0.5].sort_values("similarity", ascending=False)

    # Konwertuj do listy słowników
    output = result.to_dict(orient="records")

    return {"recommendations": output if show_all else output[:5]}
