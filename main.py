from fastapi import FastAPI, HTTPException
from sentence_transformers import SentenceTransformer, util
import pandas as pd
import os

app = FastAPI()

# 🔍 Ścieżka do Excela
excel_path = os.path.join(os.path.dirname(__file__), "Rejestr_zastosowanie.xlsx")

# 📥 Wczytanie danych z Excela
print("📁 Ścieżka do pliku Excel:", excel_path)
print("📅 Wczytywanie Excela...")

try:
    df = pd.read_excel(excel_path)
    print("✅ Wczytano Excel – liczba wierszy:", len(df))
except Exception as e:
    df = None
    print("❌ Błąd podczas wczytywania Excela:", e)

# 🧠 Załaduj model SentenceTransformer
print("🧠 Wczytywanie modelu AI...")
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
print("✅ Model załadowany")

# ✨ Przygotuj embeddingi z kolumny 'nazwa'
if df is not None:
    try:
        texts = df["nazwa"].astype(str).tolist()
        embeddings = model.encode(texts, convert_to_tensor=True)
    except Exception as e:
        print("❌ Błąd przy generowaniu embeddingów:", e)
        df = None
        embeddings = None

@app.get("/")
def root():
    return {"message": "Witaj w API SOR z wyszukiwarką AI!"}

@app.get("/recommend")
def recommend(query: str):
    if df is None or embeddings is None:
        raise HTTPException(status_code=500, detail="Dane z Excela nie zostały wczytane")

    # 🔍 Przetwórz zapytanie
    query_embedding = model.encode(query, convert_to_tensor=True)
    hits = util.semantic_search(query_embedding, embeddings, top_k=5)[0]

    results = []
    for hit in hits:
        idx = hit["corpus_id"]
        score = hit["score"]
        row = df.iloc[idx].to_dict()
        row["score"] = round(float(score), 3)
        results.append(row)

    return {"results": results}
