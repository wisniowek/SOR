# -*- coding: utf-8 -*-
import os
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DeepSeek API key
DEESEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
if not DEESEEK_API_KEY:
    print("❌ WARNING: DEEPSEEK_API_KEY not set in environment")

# Excel configuration
EXCEL_PATH = os.path.join(os.path.dirname(__file__), "Rejestr_zastosowanie.xlsx")
KEEP_COLS = ["nazwa","NrZezw","TerminZezw","TerminDoSprzedazy","TerminDoStosowania","Rodzaj","Substancja_czynna","uprawa","agrofag","dawka","termin"]
COLUMN_MAPPING = {
    "nazwa":"Nazwa","NrZezw":"Numer zezwolenia","TerminZezw":"Termin zezwolenia",
    "TerminDoSprzedazy":"Termin dopuszczenia do sprzedaży","TerminDoStosowania":"Termin dopuszczenia do sprzedaży",
    "Rodzaj":"Rodzaj","Substancja_czynna":"Substancja czynna","uprawa":"Uprawa",
    "agrofag":"Agrofag","dawka":"Dawka","termin":"Termin stosowania"
}

# Load Excel
try:
    df = pd.read_excel(EXCEL_PATH, sheet_name="Rejestr_zastosowanie")
    df.columns = df.columns.str.strip()
    df = df.loc[:, ~df.columns.duplicated()]
    print(f"✅ Loaded Excel: {len(df)} rows")
except Exception as e:
    print(f"❌ Error loading Excel: {e}")
    df = None

@app.get("/")
def home():
    return JSONResponse({"message":"API is live"})

@app.get("/distinct")
def get_distinct(col: str = Query(...)):
    if df is None:
        raise HTTPException(500, "Excel data not loaded")
    if col not in df.columns:
        raise HTTPException(404, f"Column '{col}' not found")
    return {"column": col, "distinct_values": df[col].dropna().unique().tolist()}

@app.get("/search-all")
def search_all(
    nazwa: Optional[str] = None, NrZezw: Optional[str] = None, TerminZezw: Optional[str] = None,
    TerminDoSprzedazy: Optional[str] = None, TerminDoStosowania: Optional[str] = None,
    Rodzaj: Optional[str] = None, Substancja_czynna: Optional[str] = None,
    uprawa: Optional[str] = None, agrofag: Optional[str] = None,
    dawka: Optional[str] = None, termin: Optional[str] = None
):
    if df is None:
        raise HTTPException(500, "Excel data not loaded")
    results = df.copy()
    filters = {
        "nazwa": nazwa, "NrZezw": NrZezw, "TerminZezw": TerminZezw,
        "TerminDoSprzedazy": TerminDoSprzedazy, "TerminDoStosowania": TerminDoSprzedazy,
        "Rodzaj": Rodzaj, "Substancja_czynna": Substancja_czynna,
        "uprawa": uprawa, "agrofag": agrofag,
        "dawka": dawka, "termin": termin
    }
    for col, term in filters.items():
        if term:
            results = results[results[col].astype(str).str.contains(term, case=False, na=False)]
    results = results[KEEP_COLS].rename(columns=COLUMN_MAPPING).replace({"nan":None,"NaT":None})
    return {"count": len(results), "results": results.to_dict(orient="records")}

@app.post("/estimate-price")
async def estimate_price(item: dict):
    prompt = item.get("prompt")
    if not prompt:
        raise HTTPException(400, "'prompt' is required")
    if not DEESEEK_API_KEY:
        raise HTTPException(500, "Missing DEEPSEEK_API_KEY")
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEESEEK_API_KEY}", "Content-Type": "application/json"}
    data = {"model":"deepseek-chat","messages":[{"role":"system","content":"You are an expert on agricultural product pricing."},{"role":"user","content":prompt}],"max_tokens":150,"temperature":0.7}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers, timeout=30)
    print("🔍 DeepSeek status:", response.status_code)
    print("🔍 DeepSeek response:", response.text)
    if response.status_code != 200:
        raise HTTPException(500, f"DeepSeek error: {response.text}")
    content = response.json().get("choices", [{}])[0].get("message", {}).get("content")
    if not content:
        raise HTTPException(500, "Malformed response from DeepSeek")
    return {"price_estimate": content.strip()}
