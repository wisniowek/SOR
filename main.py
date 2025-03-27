# -*- coding: utf-8 -*-

import os
from typing import Optional

import numpy as np
import pandas as pd
import openai
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

# Dodanie CORS (umożliwia wywołania z innych domen)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # W produkcji warto ograniczyć do konkretnych domen
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ustawienie klucza API OpenAI (upewnij się, że zmienna OPENAI_API_KEY jest ustawiona)
openai.api_key = os.environ.get("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")

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
    "TerminDoStosowania": "Termin dopuszczenia do sprzedaży",  # Uwaga: ta sama wartość co TerminDoSprzedazy
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

@app.post("/estimate-price")
async def estimate_price(item: dict):
    """
    Endpoint korzystający z OpenAI do oszacowania ceny na podstawie promptu.
    Oczekuje JSON w formacie: { "prompt": "..." }
    """
    prompt = item.get("prompt")
    if not prompt:
        raise HTTPException(status_code=400, detail="Pole 'prompt' jest wymagane.")
    try:
        # Używamy asynchronicznej wersji ChatCompletion
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Jesteś ekspertem od cen środków rolniczych."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )
        result_text = response.choices[0].message.content.strip()
        return {"price_estimate": result_text}
    except Exception as e:
        print("Error in /estimate-price:", e)
        raise HTTPException(status_code=500, detail=str(e))
