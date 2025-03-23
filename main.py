from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import os
import pandas as pd
import numpy as np

app = FastAPI()

excel_path = os.path.join(os.path.dirname(__file__), "Rejestr_zastosowanie.xlsx")

print("🔥 Start – proste wyszukiwanie, konwersja dat i Infinity -> None")
print("📁 Ścieżka do pliku Excel:", excel_path)

try:
    df = pd.read_excel(excel_path, sheet_name="Rejestr_zastosowanie")
    df.columns = df.columns.str.strip()
    print(f"✅ Wczytano Excel: {len(df)} wierszy, kolumny: {df.columns.tolist()}")
except Exception as e:
    print("❌ Błąd wczytywania Excela:", e)
    df = None

@app.get("/")
def home():
    if df is None:
        content = {"message": "Brak danych Excel. Sprawdź logi."}
    else:
        content = {"message": "API SOR – proste wyszukiwanie (ą, ś, ć, ź, ż)"}
    return JSONResponse(content=content, media_type="application/json; charset=utf-8")

@app.get("/search")
def search(q: str = Query(..., description="np. ziemniak, pszenica...")):
    if df is None:
        raise HTTPException(500, "Dane z Excela nie zostały wczytane.")

    mask_nazwa = df["nazwa"].str.contains(q, case=False, na=False)
    mask_uprawa = df["uprawa"].str.contains(q, case=False, na=False)
    results = df[mask_nazwa | mask_uprawa].copy()

    # 1) Konwersja dat → string
    for col in results.columns:
        if pd.api.types.is_datetime64_any_dtype(results[col]):
            results[col] = results[col].apply(lambda x: x.isoformat() if pd.notnull(x) else None)

    # 2) Zamień Infinity, -Infinity na NaN
    results = results.replace([np.inf, -np.inf], np.nan)

    # 3) Zamień NaN na None (dla JSON)
    results = results.where(pd.notnull(results), None)

    data_list = results.to_dict(orient="records")

    content = {
        "zapytanie": q,
        "liczba_wynikow": len(data_list),
        "wyniki": data_list
    }
    return JSONResponse(content=content, media_type="application/json; charset=utf-8")
