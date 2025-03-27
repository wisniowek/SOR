# -*- coding: utf-8 -*-

import os
from typing import Optional

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import httpx  # <-- biblioteka do zapytań asynchronicznych

app = FastAPI()

# Dodanie CORS (umożliwia wywołania z innych domen)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # W produkcji warto ograniczyć do konkretnych domen
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------
# 1. Klucz API DeepSeek zamiast OpenAI
# --------------------------------
DEESEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")  # <-- ZAŁÓŻ, że tu jest Twój klucz

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
    "TerminDoStosowania": "Termin dopuszczenia do sprzedaży",  # Uwaga: duplikat z powyższym
    "Rodzaj": "Rodzaj",
    "Substancja_czynna": "Substancja czynna",
    "uprawa": "Uprawa",
    "agrofag": "Agrofag",
    "dawka": "Dawka",
    "termin": "Termin stosowania",
}

# Wczytanie pliku Excel i przygotowanie DataFrame
try:
    df = pd.read_excel(EXCEL_PATH, sheet_name="Rejestr_zastosowanie")
    # Usuwamy spacje w nagłówkach
    df.columns = df.columns.str.strip()
    # Sprawdź duplikaty kolumn
    dup_cols = df.columns[df.columns.duplicated()].unique()
    if len(dup_cols) > 0:
        print("⚠️ Wykryto duplikaty kolumn:", dup_cols)
        # Usuwamy powtórki – zostaje pierwsza kolumna o danej nazwie
        df = df.loc[:, ~df.columns.duplicated()]
    print("✅ Wczytano Excel – liczba wierszy:", len(df), ", kolumny:", df.columns.tolist())
except Exception as e:
    print("❌ Błąd wczytywania Excela:", e)
    df = None

@app.head("/")
def head_home():
    """
    Obsługa metody HEAD na '/' – aby uniknąć błędu 405 Method Not Allowed.
    """
    return None

@app.get("/")
def home():
    """
    Strona główna – informuje, czy dane zostały poprawnie wczytane.
    """
    if df is None:
        content = {"message": "Brak danych Excel. Sprawdź logi."}
    else:
        content = {"message": "API SOR działa – filtry (ręczne parametry), polskie znaki (ą, ś, ć, ź, ż)"}
    return JSONResponse(content=content, media_type="application/json; charset=utf-8")

@app.get("/distinct")
def get_distinct_values(col: str = Query(..., description="Nazwa kolumny, z której chcesz uzyskać unikalne wartości")):
    """
    Endpoint zwraca unikalne wartości z podanej kolumny.
    Przykład: GET /distinct?col=uprawa
    """
    if df is None:
        raise HTTPException(status_code=500, detail="Dane z Excela nie zostały wczytane.")
    if col not in df.columns:
        raise HTTPException(
            status_code=404,
            detail=f"Kolumna '{col}' nie występuje. Dostępne kolumny: {list(df.columns)}"
        )
    distinct_vals = df[col].drop_duplicates().dropna().tolist()
    return JSONResponse(
        content={"column": col, "distinct_values": distinct_vals},
        media_type="application/json; charset=utf-8"
    )

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
    Filtrowanie w kolumnach.
    Jeśli parametr jest podany, stosowane jest filtrowanie metodą .str.contains(...)
    (bez uwzględnienia wielkości liter i z pominięciem wartości NaN).
    """
    if df is None:
        raise HTTPException(status_code=500, detail="Dane z Excela nie zostały wczytane.")
    results = df.copy()
    if nazwa:
        results = results[results["nazwa"].str.contains(nazwa, case=False, na=False)]
    if NrZezw:
        results = results[results["NrZezw"].str.contains(NrZezw, case=False, na=False)]
    if TerminZezw:
        results = results[results["TerminZezw"].astype(str).str.contains(TerminZezw, case=False, na=False)]
    if TerminDoSprzedazy:
        results = results[results["TerminDoSprzedazy"].astype(str).str.contains(TerminDoSprzedazy, case=False, na=False)]
    if TerminDoStosowania:
        results = results[results["TerminDoStosowania"].astype(str).str.contains(TerminDoSprzedazy, case=False, na=False)]
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
    results = results[KEEP_COLS]
    results = results.rename(columns=COLUMN_MAPPING)
    results = results.astype(str).replace("nan", None).replace("NaT", None)
    data_list = results.to_dict(orient="records")
    return JSONResponse(
        content={"count": len(data_list), "results": data_list},
        media_type="application/json; charset=utf-8"
    )

# -----------------------------------------------
# 2. Endpoint korzystający teraz z DeepSeek
# -----------------------------------------------
@app.post("/estimate-price")
async def estimate_price(item: dict):
    """
    Endpoint korzystający z DeepSeek do oszacowania ceny na podstawie promptu.
    Oczekuje JSON w formacie: { "prompt": "..." }
    """

    if not DEESEEK_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Brak zmiennej środowiskowej DEEPSEEK_API_KEY z kluczem do DeepSeek."
        )

    prompt = item.get("prompt")
    if not prompt:
        raise HTTPException(status_code=400, detail="Pole 'prompt' jest wymagane.")

    # <-- WAŻNE: dostosuj do dokumentacji DeepSeek
    # Zakładamy, że DeepSeek używa podobnej struktury co OpenAI ChatCompletion:
    # POST https://api.deepseek.com/v1/chat/completions
    # JSON: {"model": "deepseek-chat", "messages": [...], "max_tokens": 150, "temperature": 0.7, ... }

    deepseek_url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEESEEK_API_KEY}"
    }
    data = {
        "model": "deepseek-chat",  # <-- dostosuj do nazwy modelu w DeepSeek
        "messages": [
            {"role": "system", "content": "Jesteś ekspertem od cen środków rolniczych."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 150,
        "temperature": 0.7
    }

    # Wywołanie API za pomocą httpx w trybie async
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(deepseek_url, json=data, headers=headers, timeout=30.0)
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Problem z połączeniem do DeepSeek: {str(e)}")

        if response.status_code != 200:
            # Można zajrzeć w text, by zobaczyć zwrotkę z serwera
            raise HTTPException(status_code=500, detail=f"Błąd DeepSeek: {response.text}")

        try:
            response_data = response.json()
            # Zakładamy, że odpowiedź ma pole "choices" -> [0] -> "message" -> "content"
            result_text = response_data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError) as e:
            raise HTTPException(
                status_code=500,
                detail=f"Nie udało się sparsować odpowiedzi od DeepSeek. Szczegóły: {str(e)}.\nTreść: {response.text}"
            )

    return {"price_estimate": result_text}

