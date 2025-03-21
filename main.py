from fastapi import FastAPI, Query
import pandas as pd
from datetime import datetime

app = FastAPI()

# Ścieżka do pliku w repozytorium GitHub
FILE_PATH = "rejestr_sor_20250319.xlsx"
df_sor = pd.read_excel(FILE_PATH, sheet_name="Rejestr śor")

def filter_products(problem: str, uprawa: str):
    """Filtruje środki ochrony roślin na podstawie problemu i uprawy."""
    df = df_sor.astype(str).apply(lambda x: x.str.lower())
    problem = problem.lower()
    uprawa = uprawa.lower()
    
    filtered_df = df[(df["Rodzaj środka"].str.contains(problem, na=False)) &
                     (df["Zakres stosowania"].str.contains(uprawa, na=False))]
    
    today = datetime.today().strftime('%Y-%m-%d')
    if "Termin ważności zezwolenia" in filtered_df.columns:
        filtered_df = filtered_df[pd.to_datetime(filtered_df["Termin ważności zezwolenia"], errors='coerce') > today]
    
    return filtered_df[["Nazwa środka", "Substancja czynna", "Rodzaj środka", "Termin ważności zezwolenia"]].to_dict(orient="records")

@app.get("/recommend")
def recommend(problem: str = Query(..., description="Problem (np. chwasty, mszyce)"),
              uprawa: str = Query(..., description="Uprawa (np. pszenica, jabłoń)")):
    """Zwraca listę rekomendowanych środków ochrony roślin."""
    results = filter_products(problem, uprawa)
    if results:
        return {"status": "success", "recommendations": results}
    return {"status": "error", "message": "Brak dostępnych środków dla podanych kryteriów."}
