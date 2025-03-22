from fastapi import FastAPI, HTTPException, Query
from sentence_transformers import SentenceTransformer, util
import pandas as pd
from pathlib import Path

app = FastAPI()
EXCEL_PATH = Path(__file__).parent / "Rejestr_zastosowanie.xlsx"
model = SentenceTransformer("paraphrase-MiniLM-L6-v2")

def load_excel():
    if not EXCEL_PATH.exists():
        raise FileNotFoundError(f"Brak pliku: {EXCEL_PATH}")
    df = pd.read_excel(EXCEL_PATH, sheet_name="Rejestr_zastosowanie")
    df["opis"] = df.astype(str).agg(" ".join, axis=1)
    df["vector"] = df["opis"].apply(lambda x: model.encode(x, convert_to_tensor=True))
    return df

try:
    df = load_excel()
except Exception as e:
    df = None
    print(f"Błąd przy ładowaniu danych: {e}")

@app.get("/")
def root():
    return {"message": "Witaj w API SOR z wyszukiwarką AI!"}

@app.get("/recommend")
def recommend(query: str = Query(...), show_all: bool = False):
    if df is None:
        raise HTTPException(500, "Dane z Excela nie zostały wczytane")
    q_vec = model.encode(query, convert_to_tensor=True)
    df["similarity"] = df["vector"].apply(lambda v: util.pytorch_cos_sim(q_vec, v).item())
    result = df[df["similarity"] > 0.5].sort_values("similarity", ascending=False)
    output = result.to_dict(orient="records")
    return {"recommendations": output if show_all else output[:5]}
