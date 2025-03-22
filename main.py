from fastapi import FastAPI, HTTPException
import pandas as pd
from sentence_transformers import SentenceTransformer, util

# 🔥 TEST 3 – MODEL + EXCEL 🔥
print("📁 Ścieżka do pliku Excel: /opt/render/project/src/Rejestr_zastosowanie.xlsx")
print("📥 Wczytywanie Excela...")
excel_path = "Rejestr_zastosowanie.xlsx"
df = pd.read_excel(excel_path, sheet_name="Rejestr_zastosowanie")
df.columns = df.columns.str.strip()
print(f"✅ Wczytano Excel – liczba wierszy: {len(df)}")

# Model AI
print("🧠 Wczytywanie modelu AI...")
model = SentenceTransformer("sentence-transformers/paraphrase-MiniLM-L6-v2")
print("✅ Model załadowany")

# Teksty do porównania
texts = df["nazwa"].astype(str).tolist()
embeddings = model.encode(texts, convert_to_tensor=True)

# FastAPI
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Witaj w API SOR z wyszukiwarką AI!"}

@app.get("/recommend")
def recommend(query: str):
    if not query:
        raise HTTPException(status_code=400, detail="Brak zapytania")

    query_embedding = model.encode(query, convert_to_tensor=True)
    hits = util.semantic_search(query_embedding, embeddings, top_k=5)[0]

    results = [texts[hit["corpus_id"]] for hit in hits]
    return {"query": query, "results": results}
