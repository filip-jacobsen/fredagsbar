# Fredagsbar

Et system til at holde styr på events og tilmeldinger i fredagsbaren. Hvert event har et begrænset antal pladser, og API'en svarer 409, når et event er fuldt eller en person allerede er tilmeldt.

- `api.py`: Flask API (Del 1), dokumenteret i `swagger.json`
- `app.py`: Streamlit-frontend, der taler med API'en via httpx (Del 2)
- `Dockerfile` og `docker-compose.yml`: kører begge dele i Docker (Del 3)

## Start med Docker (anbefalet)

Fra roden af repoet:

```bash
docker compose up --build
```

| Del | Adresse |
|---|---|
| Frontend (Streamlit) | http://localhost:8501 |
| API (Flask) | http://localhost:5000 (port **5000**) |

Stop med `Ctrl+C`, og ryd op med `docker compose down`.

## Start lokalt uden Docker

Kræver [uv](https://docs.astral.sh/uv/). Brug to terminaler fra roden af repoet:

```bash
uv sync
uv run api.py                    # terminal 1: API'en på http://127.0.0.1:5000
uv run streamlit run app.py      # terminal 2: frontenden på http://localhost:8501
```

Frontenden finder API'en via miljøvariablen `API_URL`. Lokalt bruges standardværdien `http://127.0.0.1:5000`, og i Docker sætter `docker-compose.yml` den til `http://api:5000`.

## API-endpoints

| Metode | URL | Body | Svar ved succes |
|---|---|---|---|
| GET | `/events` | – | 200 + liste af events |
| GET | `/events/<id>` | – | 200 + ét event |
| POST | `/events` | `{"title", "date", "capacity"}` | 201 + det nye event |
| POST | `/events/<id>/signups` | `{"name"}` | 201 + det opdaterede event |
| DELETE | `/events/<id>/signups/<name>` | – | 204 |
| DELETE | `/events/<id>` | – | 204 |

Fejl returneres som `{"error": "..."}` med statuskode 400, 404 eller 409. Se `swagger.json` for den fulde dokumentation (kan åbnes i [Swagger Editor](https://editor.swagger.io)).

## Bemærkninger

- Data ligger i hukommelsen og nulstilles, når API'en genstartes.
- Hvis port 5000 er optaget (fx af AirPlay på macOS), kan du ændre `"5000:5000"` i `docker-compose.yml` til `"5001:5000"` og bruge http://localhost:5001.