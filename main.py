from fastapi import FastAPI, HTTPException, Query
from typing import List
from pathlib import Path
import pandas as pd
from sentence_transformers import SentenceTransformer, util

app = FastAPI()

print("🔥 STARTUJE APLIKACJA NA RENDER 🔥")

# Ścieżka do pliku Excel
EXCEL_PATH = Path(__file__).parent / "Rejestr_zastosowanie.xlsx"

# Funkcja do ładowania danych z Excela
def load_excel():
    print("📥 Próba wczytania Excela...")
    print("📁 Szukam pliku:", EXCEL_PATH)

    df = pd.read_excel(EXCEL_PATH, sheet_name="Rejestr_zastosowanie")
    df = df.dropna(subset=["nazwa", "uprawa"])
    df["tekst"] = df["nazwa"].astype(str) + " " + df["uprawa"].astype(str)
    return df

# Inicjalizacja modelu i danych
model = SentenceTransformer("sentence-transformers/paraphrase-MiniLM-L6-v2")

try:
    df = load_excel()
    print("✅ Dane z Excela załadowane:", len(df), "wierszy")
    teksty = df["tekst"].tolist()
    embeddings = model.encode(teksty, convert_to_tensor=True)
except Exception as e:
    df = None
    embeddings = None
    print("❌ Błąd ładowania danych:", e)

@app.get("/")
def root():
    return {"message": "Witaj w API SOR z wyszukiwarką AI!"}

@app.get("/recommend")
def recommend(query: str = Query(...), top_k: int = 5, show_all: bool = False):
    if df is None or embeddings is None:
        raise HTTPException(status_code=500, detail="Dane z Excela nie zostały wczytane")

    query_embedding = model.encode(query, convert_to_tensor=True)
    similarities = util.pytorch_cos_sim(query_embedding, embeddings)[0]

    results = []
    for idx in similarities.argsort(descending=True):
        score = similarities[idx].item()
        row = df.iloc[idx]
        results.append({
            "nazwa": row["nazwa"],
            "uprawa": row["uprawa"],
            "zalecane_substancje": row.get("zalecane_substancje", ""),
            "substancje_czynne": row.get("substancje_czynne", ""),
            "substancje_biologiczne": row.get("substancje_biologiczne", ""),
            "grupa": row.get("grupa", ""),
            "odstepstwo": row.get("odstepstwo", ""),
            "similarity": round(score, 4)
        })

    if not show_all:
        results = results[:top_k]

    return {"recommendations": results}
