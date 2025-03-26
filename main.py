# -*- coding: utf-8 -*-

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import pandas as pd
import numpy as np
import os

app = FastAPI()

# Ścieżka do pliku Excel (musi być w tym samym katalogu co main.py)
EXCEL_PATH = os.path.join(os.path.dirname(__file__), "Rejestr_zastosowanie.xlsx")

# Kolumny, które chcesz w wyniku (pomijamy te z "NIE ŁADUJ")
KEEP_COLS = [
    "nazwa",
    "NrZezw",
    "TerminZezw",
    "TerminDoSprzedazy",
    "TerminDoStosowania",
    "Rodzaj",
    "Substancja_czynna",
    "uprawa",
    "agrofag",
    "dawka",
    "termin",
]

# Mapa: nazwy kolumn -> docelowe nazwy w JSON
COLUMN_MAPPING = {
    "nazwa": "Nazwa",
    "NrZezw": "Numer zezwolenia",
    "TerminZezw": "Termin zezwolenia",
    "TerminDoSprzedazy": "Termin dopuszczenia do sprzedaży",
    "TerminDoStosowania": "Termin dopuszczenia do sprzedaży",
    "Rodzaj": "Rodzaj",
    "Substancja_czynna": "Substancja czynna",
    "uprawa": "Uprawa",
    "agrofag": "Agrofag",
    "dawka": "Dawka",
    "termin": "Termin stosowania",
}

try:
    # 1) Wczytanie pliku
    df = pd.read_excel(EXCEL_PATH, sheet_name="Rejestr_zastosowanie")
    # 2) Usuwamy spacje w nagłówkach
    df.columns = df.columns.str.strip()

    # 3) Sprawdź duplikaty
    dup_cols = df.columns[df.columns.duplicated()].unique()
    if len(dup_cols) > 0:
        print("⚠️ Wykryto duplikaty kolumn:", dup_cols)
        # Usuwamy powtórki (zostanie pierwsza kolumna o danej nazwie)
        df = df.loc[:, ~df.columns.duplicated()]

    print("✅ Wczytano Excel – liczba wierszy:", len(df), ", kolumny:", df.columns.tolist())
except Exception as e:
    print("❌ Błąd wczytywania Excela:", e)
    df = None

@app.get("/")
def home():
    """
    Strona główna – proste info, czy dane wczytane.
    """
    if df is None:
        content = {"message": "Brak danych Excel. Sprawdź logi."}
    else:
        content = {"message": "API SOR działa – filtry (ręczne parametry), polskie znaki (ą, ś, ć, ź, ż)"}
    return JSONResponse(content=content, media_type="application/json; charset=utf-8")

@app.get("/search-all")
def search_all(
    nazwa: Optional[str] = None,
    NrZezw: Optional[str] = None,
    TerminZezw: Optional[str] = None,
    TerminDoSprzedazy: Optional[str] = None,
    TerminDoStosowania: Optional[str] = None,
    Rodzaj: Optional[str] = None,
    Substancja_czynna: Optional[str] = None,
    uprawa: Optional[str] = None,
    agrofag: Optional[str] = None,
    dawka: Optional[str] = None,
    termin: Optional[str] = None
):
    """
    Filtrowanie w kolumnach:
      - nazwa
      - NrZezw
      - TerminZezw
      - TerminDoSprzedazy
      - TerminDoStosowania
      - Rodzaj
      - Substancja_czynna
      - uprawa
      - agrofag
      - dawka
      - termin

    Jeśli parametr jest podany, filtrujemy .str.contains(...).
    Jeśli nie – pomijamy filtr dla tej kolumny.
    """
    if df is None:
        raise HTTPException(status_code=500, detail="Dane z Excela nie zostały wczytane.")

    results = df.copy()

    # Filtry – każdy parametr jest sprawdzany
    if nazwa:
        results = results[results["nazwa"].str.contains(nazwa, case=False, na=False)]
    if NrZezw:
        results = results[results["NrZezw"].str.contains(NrZezw, case=False, na=False)]
    if TerminZezw:
        results = results[results["TerminZezw"].astype(str).str.contains(TerminZezw, case=False, na=False)]
    if TerminDoSprzedazy:
        results = results[results["TerminDoSprzedazy"].astype(str).str.contains(TerminDoSprzedazy, case=False, na=False)]
    if TerminDoStosowania:
        results = results[results["TerminDoStosowania"].astype(str).str.contains(TerminDoStosowania, case=False, na=False)]
    if Rodzaj:
        results = results[results["Rodzaj"].str.contains(Rodzaj, case=False, na=False)]
    if Substancja_czynna:
        results = results[results["Substancja_czynna"].str.contains(Substancja_czynna, case=False, na=False)]
    if uprawa:
        results = results[results["uprawa"].str.contains(uprawa, case=False, na=False)]
    if agrofag:
        results = results[results["agrofag"].str.contains(agrofag, case=False, na=False)]
    if dawka:
        results = results[results["dawka"].str.contains(dawka, case=False, na=False)]
    if termin:
        results = results[results["termin"].str.contains(termin, case=False, na=False)]

    # Zostawiamy tylko kolumny dozwolone
    results = results[KEEP_COLS]

    # Zmieniamy nazwy kolumn (np. "nazwa" -> "Nazwa", "Rodzaj" -> "Rodzaj")
    results = results.rename(columns=COLUMN_MAPPING)

    # Konwertuj do string, usuń "nan", "NaT" → None
    results = results.astype(str).replace("nan", None).replace("NaT", None)

    # Zamiana na listę słowników
    data_list = results.to_dict(orient="records")

    return JSONResponse(
        content={"count": len(data_list), "results": data_list},
        media_type="application/json; charset=utf-8"
    )
