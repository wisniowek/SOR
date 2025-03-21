import pandas as pd
from fastapi import FastAPI, HTTPException
from pathlib import Path

app = FastAPI()

# Ścieżka do pliku Excel ( upewnij się, że plik jest w repozytorium )
EXCEL_FILE_PATH = Path(__file__).parent / "rejestr_sor_20250319.xlsx"

def load_excel_data():
    try:
        # Zakładam, że dane znajdują się w arkuszu "Rejestr śor"
        df = pd.read_excel(EXCEL_FILE_PATH, sheet_name="Rejestr śor")
        return df
    except Exception as e:
        # Loguj błąd przy ładowaniu danych
        raise Exception(f"Could not load Excel data: {e}")

# Ładowanie danych przy starcie aplikacji
try:
    excel_data = load_excel_data()
except Exception as e:
    excel_data = None
    print(f"Error loading Excel data: {e}")

@app.get("/")
def read_root():
    return {"message": "Witaj w API SOR!"}

@app.get("/recommend")
def recommend(uprawa: str, problem: str):
    if excel_data is None:
        raise HTTPException(status_code=500, detail="Excel data not loaded")
    try:
        # Prosty przykład filtrowania – należy dostosować do struktury pliku Excel
        mask = excel_data.apply(
            lambda row: (uprawa.lower() in str(row).lower()) and (problem.lower() in str(row).lower()),
            axis=1
        )
        results = excel_data[mask].to_dict(orient="records")
        if not results:
            return {"recommendations": "No matching records found"}
        return {"recommendations": results}
    except Exception as e:
        # Złapanie ewentualnych błędów podczas filtrowania
        raise HTTPException(status_code=500, detail=str(e))
