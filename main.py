from fastapi import FastAPI, HTTPException, Query
import os
import pandas as pd

app = FastAPI()

# Ścieżka do Excela
excel_path = os.path.join(os.path.dirname(__file__), "Rejestr_zastosowanie.xlsx")

print("🔥 Start prostej wersji (bez AI)")
print("📁 Ścieżka do pliku Excel:", excel_path)

try:
    df = pd.read_excel(excel_path, sheet_name="Rejestr_zastosowanie")
    df.columns = df.columns.str.strip()
    print(f"✅ Wczytano Excel – liczba wierszy: {len(df)}, kolumny: {df.columns.tolist()}")
except Exception as e:
    print("❌ Błąd wczytywania Excela:", e)
    df = None

@app.get("/")
def home():
    if df is None:
        return {"message": "Brak danych Excel. Sprawdź logi."}
    return {"message": "API SOR – proste wyszukiwanie bez AI (test polskich znaków: ą, ś, ć, ź, ż)"}

@app.get("/search")
def search(q: str = Query(..., description="Wpisz np. ziemniaki, truskawki itp.")):
    """
    Proste wyszukiwanie w kolumnach 'nazwa' i 'uprawa'.
    Wyszukiwanie case-insensitive, na zasadzie substring match.
    """
    if df is None:
        raise HTTPException(status_code=500, detail="Dane z Excela nie zostały wczytane.")

    # Filtr po kolumnie 'nazwa' i 'uprawa' (case-insensitive)
    mask_nazwa = df["nazwa"].str.contains(q, case=False, na=False)
    mask_uprawa = df["uprawa"].str.contains(q, case=False, na=False)

    # Rekordy pasujące w 'nazwa' LUB w 'uprawa'
    results = df[mask_nazwa | mask_uprawa].copy()

    # Konwertuj do listy słowników
    data = results.to_dict(orient="records")

    return {
        "zapytanie": q,
        "liczba_wynikow": len(data),
        "wyniki": data
    }
