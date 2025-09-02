
# ISC Groq FastAPI (MVP)
App mínimo para classificar cirurgia segundo regras simplificadas (Anvisa) e normalizar termos com Groq.

## Endpoints
- `GET /` — ping
- `POST /classificar` — `{ "cirurgia": "ATQ" }`

## Variáveis de ambiente
- `GROQ_API_KEY` — chave da API Groq

## Rodar local (Docker)
```bash
export GROQ_API_KEY="sua_chave"
docker build -t isc-groq .
docker run -e GROQ_API_KEY=$GROQ_API_KEY -p 8080:8080 isc-groq
```

## Exemplo
```bash
curl -s -X POST http://localhost:8080/classificar \
 -H 'Content-Type: application/json' \
 -d '{"cirurgia":"CRM"}'
```
