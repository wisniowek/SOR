import os
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from sentence_transformers import SentenceTransformer, util
from pathlib import Path

app = FastAPI()

# Ścieżka do pliku Excel
EXCEL_FILE_PATH = Path(__file__).parent / "Rejestr_zastosowanie.xlsx"

def load_excel_data():
    try:
        # Wczytanie danych z arkusza "Rejestr_zastosowanie"
        df = pd.read_excel(EXCEL_FILE_PATH, sheet_name="Rejestr_zastosowanie")
        return df
    except FileNotFoundError:
        raise Exception("Plik Excel nie został znaleziony.")
    except ValueError as e:
        raise Exception(f"Nie udało się załadować danych z Excela: {e}")
    except Exception as e:
        raise Exception(f"Nieznany błąd podczas ładowania Excela: {e}")

# Wczytaj dane
try:
    df = load_excel_data()
except Exception as e:
    df = None
    print(f"Błąd podczas ładowania Excela: {e}")

# Inicjalizacja modelu do generowania wektorów
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

# Łączenie wszystkich kolumn w jedną kolumnę 'opis'
if df is not None:
    df['opis'] = df.apply(lambda row: " ".join(str(x) for x in row.values), axis=1)

# Precompute embeddingów dla opisów w danych
if df is not None:
    df['vector'] = df['opis'].apply(lambda x: model.encode(str(x), convert_to_tensor=True))

@app.get("/")
def read_root():
    return {"message": "Witaj w API SOR z wyszukiwarką AI!"}

@app.get("/recommend")
def recommend(query: str, show_all: bool = Query(False, description="Czy wyświetlić wszystkie wyniki, jeśli jest ich więcej niż 5")):
    """
    Endpoint przyjmujący zapytanie w parametrze 'query'.
    Używa modelu SentenceTransformer do generowania wektora zapytania.
    Następnie oblicza kosinusowe podobieństwo pomiędzy zapytaniem a opisami i zwraca
    top 5 wyników o podobieństwie równym lub większym niż 0.5.
    """
    if df is None:
        raise HTTPException(status_code=500, detail="Dane z Excela nie zostały wczytane")
    try:
        query_vector = model.encode(query, convert_to_tensor=True)
        recommendations = []
        for idx, row in df.iterrows():
            similarity = util.pytorch_cos_sim(query_vector, row['vector']).item()
            recommendations.append((similarity, row.to_dict()))
        
        # Sortowanie wyników malejąco według podobieństwa
        recommendations.sort(key=lambda x: x[0], reverse=True)

        # Ustal próg podobieństwa
        filtered = [rec for rec in recommendations if rec[0] >= 0.5]
        
        # Zwróć top 5 wyników lub wszystkie, jeśli użytkownik wybrał show_all
        if len(filtered) > 5 and not show_all:
            return {"message": "Jest więcej dopasowań, wyświetlić wszystkie?", "recommendations": [{"similarity": sim, "data": data} for sim, data in filtered[:5]]}
        
        return {"recommendations": [{"similarity": sim, "data": data} for sim, data in filtered]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search")
def search(query: str):
    """
    Endpoint do wyszukiwania po różnych polach, takich jak uprawa, agrofag, zastosowanie,
    nazwy środków oraz substancje czynne.
    """
    if df is None:
        raise HTTPException(status_code=500, detail="Dane z Excela nie zostały wczytane")
    try:
        query_vector = model.encode(query, convert_to_tensor=True)
        search_results = []
        
        for idx, row in df.iterrows():
            fields = ['uprawa', 'agrofag', 'zastosowanie/uzytkownik', 'nazwa', 'Substancja_czynna']
            for field in fields:
                if field in row:
                    field_vector = model.encode(str(row[field]), convert_to_tensor=True)
                    similarity = util.pytorch_cos_sim(query_vector, field_vector).item()
                    search_results.append((field, similarity, row.to_dict()))
        
        # Sortowanie wyników malejąco według podobieństwa
        search_results.sort(key=lambda x: x[1], reverse=True)
        
        # Filtruj wyniki, aby zwrócić tylko te z podobieństwem >= 0.5
        filtered_results = [result for result in search_results if result[1] >= 0.5]
        
        return {"search_results": [{"field": field, "similarity": sim, "data": data} for field, sim, data in filtered_results]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
