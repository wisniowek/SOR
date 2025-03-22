from fastapi import FastAPI

app = FastAPI()

print("🔥 RUSZYŁO – MINIMALNY TEST 🔥")

@app.get("/")
def root():
    return {"message": "Działa minimalna wersja!"}
