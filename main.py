import os
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from sentence_transformers import SentenceTransformer, util
from pathlib import Path

app = FastAPI()

# Ścieżka do pliku Excel
EXCEL_FILE_PATH = Path(__file__).parent / "Rejestr_zastosowanie.xlsx"

# Mapowanie nazw kolumn
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

def load_excel_data():
    print(f"Checking if the Excel file exists at {EXCEL_FILE_PATH}")
    if not EXCEL_FILE_PATH.exists():
        print(f"File not found: {EXCEL_FILE_PATH}")
        raise Exception(f"Plik Excel nie został znaleziony: {EXCEL_FILE_PATH}")
    
    try:
        # Wczytanie danych z arkusza "Rejestr_zastosowanie"
        print(f"Loading Excel file from {EXCEL_FILE_PATH}")
        df = pd.read_excel(EXCEL_FILE_PATH, sheet_name="Rejestr_zastosowanie")
        print("Excel file loaded successfully")
        print(f"Columns in the Excel file: {df.columns.tolist()}")
        return df
    except FileNotFoundError:
        print("Excel file not found")
        raise Exception("Plik Excel nie został znaleziony.")
    except ValueError as e:
        print(f"ValueError loading Excel file: {e}")
        raise Exception(f"Nie udało się załadować danych z Excela: {e}")
    except Exception as e:
        print(f"Unknown error loading Excel file: {e}")
        raise Exception(f"Nieznany błąd podczas ładowania Excela: {e}")

# Wczytaj dane
try:
    df = load_excel_data()
    # Zmapuj nazwy kolumn na bardziej opisowe
    df.rename(columns=COLUMN_MAPPING, inplace=True)
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
        print(f"Error in /recommend endpoint: {e}")
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
            fields = ['Uprawa', 'Agrofag', 'Zastosowanie', 'Nazwa', 'Substancja czynna']
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
        print(f"Error in /search endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
