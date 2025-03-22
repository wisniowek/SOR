import os
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from sentence_transformers import SentenceTransformer, util
from pathlib import Path

app = FastAPI()

# Lokalna ścieżka i URL (zmień na swój publiczny link)
EXCEL_FILE_PATH = Path(__file__).parent / "Rejestr_zastosowanie.xlsx"
EXCEL_FILE_URL  = "https://raw.githubusercontent.com/<USER>/<REPO>/main/Rejestr_zastosowanie.xlsx"

COLUMN_MAPPING = {
    "nazwa": "Nazwa",
    "NrZezw": "Numer zezwolenia",
    "TerminZezw": "Termin zezwolenia",
    "TerminDoSprzedazy": "Termin do sprzedaży",
    "TerminDoStosowania": "Termin do stosowania",
    "Rodzaj": "Rodzaj",
    "Substancja_czynna": "Substancja czynna",
    "uprawa": "Uprawa",
    "agrofag": "Agrofag",
    "dawka": "Dawka",
    "termin": "Termin",
    "nazwa_grupy": "Nazwa grupy",
    "maloobszarowe": "Użytek małoobszarowy",
    "zastosowanie/uzytkownik": "Zastosowanie",
    "srodek_mikrobiologiczny": "Środek mikrobiologiczny"
}

def load_excel_data() -> pd.DataFrame:
    try:
        if EXCEL_FILE_PATH.exists():
            path = EXCEL_FILE_PATH
            print(f"Loading Excel from disk: {path}")
        else:
            path = EXCEL_FILE_URL
            print(f"Local file not found, loading Excel from URL: {path}")
        df = pd.read_excel(path, sheet_name="Rejestr_zastosowanie")
        df.rename(columns=COLUMN_MAPPING, inplace=True)
        df["opis"] = df.astype(str).agg(" ".join, axis=1)
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load Excel: {e}")

try:
    df = load_excel_data()
    model = SentenceTransformer("paraphrase-MiniLM-L6-v2")
    df["vector"] = df["opis"].apply(lambda t: model.encode(t, convert_to_tensor=True))
    print("✅ Data and model ready")
except Exception as e:
    df = None
    print(f"❌ Initialization error: {e}")

@app.get("/")
def root():
    return {"message": "SOR API is alive!"}

def cosine_recs(query: str, threshold=0.5, limit=5):
    q_vec = model.encode(query, convert_to_tensor=True)
    sims = df["vector"].apply(lambda v: util.pytorch_cos_sim(q_vec, v).item())
    df_out = df.assign(similarity=sims).query("similarity >= @threshold")
    df_out = df_out.sort_values("similarity", ascending=False)
    return df_out.head(limit if len(df_out)>limit else len(df_out)).to_dict(orient="records")

@app.get("/recommend")
def recommend(query: str = Query(...), show_all: bool = False):
    if df is None:
        raise HTTPException(500, "Excel data not loaded")
    recs = cosine_recs(query)
    if not show_all and len(recs) > 5:
        return {"message": "More results available", "recommendations": recs[:5]}
    return {"recommendations": recs}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
