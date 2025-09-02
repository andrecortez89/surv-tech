
import os, requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-70b-versatile"

MANDATORIAS = {
    "cesariana": {"period": 30, "aliases": ["cesárea", "parto cesáreo", "cesariana"]},
    "prótese de mama": {"period": 90, "aliases": ["protese de mama", "implante mamário", "mamoplastia com prótese"]},
    "artroplastia de quadril": {"period": 90, "aliases": ["atq", "prótese de quadril", "artroplastia quadril"]},
    "artroplastia de joelho": {"period": 90, "aliases": ["atj", "prótese de joelho", "artroplastia joelho"]},
    "revascularização do miocárdio": {"period": 90, "aliases": ["crm", "cabg", "revascularizacao miocardio"]},
    "derivação interna neurológica": {"period": 90, "aliases": ["dvp", "derivacao ventriculoperitoneal", "derivacao interna neurologica"]},
    "facectomia": {"period": 90, "aliases": ["catarata", "cirurgia de catarata", "facectomia"]},
}

CLASSE_FERIDA_SUGESTOES = {
    "cesariana": "Potencialmente contaminada",
    "prótese de mama": "Limpa (com implante)",
    "artroplastia de quadril": "Limpa (com implante)",
    "artroplastia de joelho": "Limpa (com implante)",
    "revascularização do miocárdio": "Potencialmente contaminada",
    "derivação interna neurológica": "Limpa (com implante)",
    "facectomia": "Limpa",
    "default": "Confirmar com ato operatório (pode variar: Limpa / Potencialmente contaminada / Contaminada / Infectada)"
}

app = FastAPI(title="ISC - Classificador (Anvisa, simplificado)", version="0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    cirurgia: str

def groq_normaliza_termo(termo: str) -> str:
    if not GROQ_API_KEY:
        return termo.strip().lower()

    prompt_sis = (
        "Você é um normalizador de termos cirúrgicos em português do Brasil. "
        "Receba um nome livre (com gírias, abreviações) e devolva APENAS o nome clínico padronizado, "
        "sem comentários. Exemplos: "
        "'ATQ' -> 'artroplastia de quadril'; "
        "'CRM' -> 'revascularização do miocárdio'; "
        "'catarata' -> 'facectomia'; "
        "'implante mamário' -> 'prótese de mama'."
    )
    prompt_user = f"Termo: {termo}\nResponda só com o nome clínico padronizado."

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    body = {
        "model": GROQ_MODEL,
        "temperature": 0.0,
        "messages": [
            {"role": "system", "content": prompt_sis},
            {"role": "user", "content": prompt_user}
        ]
    }
    try:
        r = requests.post(GROQ_CHAT_URL, headers=headers, json=body, timeout=20)
        r.raise_for_status()
        txt = r.json()["choices"][0]["message"]["content"].strip()
        return txt.lower()
    except Exception:
        return termo.strip().lower()

def match_mandatoria(nome_norm: str):
    for base, meta in MANDATORIAS.items():
        if nome_norm == base:
            return base, meta
        for a in meta.get("aliases", []):
            if nome_norm == a.lower():
                return base, meta
    for base, meta in MANDATORIAS.items():
        if base in nome_norm:
            return base, meta
        for a in meta.get("aliases", []):
            if a.lower() in nome_norm:
                return base, meta
    return None, None

@app.post("/classificar")
def classificar(q: Query):
    termo = q.cirurgia.strip()
    if not termo:
        raise HTTPException(status_code=400, detail="Informe o nome da cirurgia.")

    nome_norm = groq_normaliza_termo(termo)
    base, meta = match_mandatoria(nome_norm)

    if base:
        obrigatoria = True
        periodo = meta["period"]
        classe = CLASSE_FERIDA_SUGESTOES.get(base, CLASSE_FERIDA_SUGESTOES["default"])
    else:
        obrigatoria = False
        periodo = 30
        classe = CLASSE_FERIDA_SUGESTOES["default"]

    return {
        "entrada": termo,
        "nome_normalizado": nome_norm,
        "obrigatoria_nacional": obrigatoria,
        "periodo_vigilancia_dias": periodo,
        "classe_ferida_sugerida": classe,
        "ajuda_isc": (
            "ISC incisional superficial (pele/subcutâneo, 30d); "
            "ISC incisional profunda (fáscia/músculo, 30–90d); "
            "ISC órgão/cavidade (30–90d). Considerar o plano mais profundo."
        ),
        "aviso": (
            "MVP simplificado. Classe de ferida depende do ato operatório "
            "e achados intraoperatórios. Ajuste a lista conforme NT vigente."
        ),
    }

@app.get("/")
def root():
    return {"ok": True, "como_usar": "POST /classificar { 'cirurgia': 'ATQ' }"}
