from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import pandas as pd
import numpy as np
import os

app = FastAPI()

# Ścieżka do pliku Excel (musi być w tym samym katalogu co main.py)
EXCEL_PATH = os.path.join(os.path.dirname(__file__), "Rejestr_zastosowanie.xlsx")

# Kolumny, które chcemy w wyniku
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
    # kolumn takich jak: nazwa_grupy, maloobszarowe, zastosowanie/uzytkownik,
    # srodek_mikrobiologiczny nie wymieniamy, bo NIE ŁADUJ
]

# Mapowanie nazw kolumn (stara_nazwa -> docelowa_nazwa)
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

# Próbujemy wczytać plik Excel
try:
    df = pd.read_excel(EXCEL_PATH, sheet_name="Rejestr_zastosowanie")
    df.columns = df.columns.str.strip()  # usuń ewentualne spacje w nagłówkach
    print("✅ Wczytano Excel – liczba wierszy:", len(df))
except Exception as e:
    print("❌ Błąd wczytywania Excela:", e)
    df = None

@app.get("/")
def home():
    if df is None:
        return {"message": "Brak danych Excel. Sprawdź logi."}
    return {"message": "API SOR działa – filtry (ręczne parametry) + zmiana nazw kolumn"}

@app.get("/search-all")
def search_all(
    # Każdy parametr jest Optional – użytkownik może podać lub pominąć
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
    Filtrowanie po dowolnej z tych kolumn:
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

    Jeśli użytkownik nie poda parametru, nie filtrujemy po tej kolumnie.
    """

    if df is None:
        raise HTTPException(500, "Dane z Excela nie zostały wczytane.")

    results = df.copy()

    # Filtry – każdy parametr jest
