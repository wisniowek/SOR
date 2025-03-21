import pandas as pd
from fastapi import FastAPI, HTTPException
from sentence_transformers import SentenceTransformer, util
from pathlib import Path

app = FastAPI()

# Określ ścieżkę do pliku Excel
EXCEL_FILE_PATH = Path(__file__).parent / "rejestr_sor_20250319.xlsx"

def load_excel_data():
    try:
        # Przyjmujemy, że dane znajdują się w arkuszu "Rejestr śor"
        df = pd.read_excel(EXCEL_FILE_PATH, sheet_name="Rejestr śor")
        return df
    except Exception as e:
        raise Exception(f"Could not load Excel data: {e}")

# Ładujemy dane z Excela
try:
    df = load_excel_data()
except Exception as e:
    df = None
    print(f"Error loading excel: {e}")

# Inicjalizujemy model do generowania wektorów
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

# Jeśli nie istnieje kolumna 'opis', spróbuj stworzyć ją z pozostałych danych (możesz to dostosować)
if df is not None and 'opis' not in df.columns:
    df['opis'] = df.apply(lambda row: " ".join(str(x) for x in row.values), axis=1)

# Precompute embeddingów dla wszystkich wpisów
if df is not None:
    df['vector'] = df['opis'].apply(lambda x: model.encode(str(x), convert_to_tensor=True))

@app.get("/")
def read_root():
    return {"message": "Witaj w API SOR z AI wyszukiwarką!"}

@app.get("/recommend")
def recommend(query: str):
    """
    Endpoint przyjmujący parametr query.
    Generuje wektor zapytania i oblicza kosinusową miarę podobieństwa z opisami środków.
    Zwraca listę rekomendacji spełniających ustalony próg podobieństwa.
    """
    if df is None:
        raise HTTPException(status_code=500, detail="Excel data not loaded")
    try:
        query_vector = model.encode(query, convert_to_tensor=True)
        recommendations = []
        for idx, row in df.iterrows():
            similarity = util.pytorch_cos_sim(query_vector, row['vector']).item()
            recommendations.append((similarity, row.to_dict()))

        # Sortujemy wyniki malejąco według podobieństwa
        recommendations.sort(key=lambda x: x[0], reverse=True)

        # Ustal próg podobieństwa, np. 0.5 – możesz dostosować
        filtered = [rec for rec in recommendations if rec[0] >= 0.5]
        if not filtered:
            return {"recommendations": "No matching records found"}
        
        # Zwracamy top 5 rekomendacji
        top = filtered[:5]
        return {"recommendations": [{"similarity": sim, "data": data} for sim, data in top]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
