from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import os
import pandas as pd

app = FastAPI()

# Ścieżka do pliku Excel
excel_path = os.path.join(os.path.dirname(__file__), "Rejestr_zastosowanie.xlsx")

print("🔥 Start – proste wyszukiwanie (bez AI), z konwersją dat w JSON")
print("📁 Ścieżka do pliku Excel:", excel_path)

try:
    # Wczytanie Excela
    df = pd.read_excel(excel_path, sheet_name="Rejestr_zastosowanie")
    df.columns = df.columns.str.strip()
    print(f"✅ Wczytano Excel: {len(df)} wierszy, kolumny: {df.columns.tolist()}")
except Exception as e:
    print("❌ Błąd wczytywania Excela:", e)
    df = None

@app.get("/")
def home():
    """
    Strona główna API
    """
    if df is None:
        content = {"message": "Brak danych Excel. Sprawdź logi."}
    else:
        content = {"message": "API SOR – proste wyszukiwanie (ą, ś, ć, ź, ż)"}
    return JSONResponse(content=content, media_type="application/json; charset=utf-8")

@app.get("/search")
def search(q: str = Query(..., description="np. ziemniak, pszenica, rzepak...")):
    """
    Proste wyszukiwanie w kolumnach 'nazwa' i 'uprawa'.
    - Używamy substring match (case-insensitive).
    - Konwertujemy daty w DataFrame do formatu ISO, aby uniknąć błędów serializacji.
    """
    if df is None:
        raise HTTPException(
            status_code=500,
            detail="Dane z Excela nie zostały wczytane."
        )

    # Filtr po 'nazwa' OR 'uprawa' (ignorujemy wielkość liter)
    mask_nazwa = df["nazwa"].str.contains(q, case=False, na=False)
    mask_uprawa = df["uprawa"].str.contains(q, case=False, na=False)

    results = df[mask_nazwa | mask_uprawa].copy()

    # UWAGA: używamy date_format="iso", by Timestamps były JSON-serializable
    data_list = results.to_dict(orient="records", date_format="iso")

    content = {
        "zapytanie": q,
        "liczba_wynikow": len(data_list),
        "wyniki": data_list
    }
    return JSONResponse(content=content, media_type="application/json; charset=utf-8")
