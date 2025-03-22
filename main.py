from fastapi import FastAPI
from pathlib import Path
import pandas as pd
from sentence_transformers import SentenceTransformer

app = FastAPI()

print("🔥 TEST 3 – MODEL + EXCEL 🔥")

EXCEL_PATH = Path(__file__).parent / "Rejestr_zastosowanie.xlsx"
print("📁 Ścieżka do pliku Excel:", EXCEL_PATH)

def load_excel():
    print("📥 Wczytywanie Excela...")
    if not EXCEL_PATH.exists():
        raise FileNotFoundError(f"Plik nie istnieje: {EXCEL_PATH}")
    df = pd.read_excel(EXCEL_PATH, sheet_name="Rejestr_zastosowanie")
    print("✅ Wczytano Excel – liczba wierszy:", len(df))
    return df

try:
    df = load_excel()
except Exception as e:
    print("❌ Błąd ładowania Excela:", e)
    df = None

try:
    print("🧠 Wczytywanie modelu AI...")
    model = SentenceTransformer("sentence-transformers/paraphrase-MiniLM-L6-v2")
    print("✅ Model załadowany")
except Exception as e:
    print("❌ Błąd ładowania modelu:", e)
    model = None

@app.get("/")
def root():
    return {"excel_rows": len(df) if df is not None else 0, "model_loaded": model is not None}
