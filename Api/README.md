# Subcontractor Part Number → Customer Service Lookup API

Simple FastAPI service that stores subcontractors, part numbers, and customer service contacts, and provides a lookup API to return the correct customer service phone number for a given part number and/or subcontractor name.

## Project structure

```
main.py          # FastAPI app and endpoints
database.py      # Database engine and session
models.py        # SQLAlchemy models
requirements.txt
```

## Setup

```bash
pip install -r requirements.txt
```

Optional environment variables:

- `DATABASE_URL` — SQLAlchemy URL (default: `sqlite:///./lookup.db`)
- `API_KEY` — if set, required as `X-API-Key` on protected routes (see Authentication)

## Run locally

```bash
uvicorn main:app --reload
```

App: [http://127.0.0.1:8000](http://127.0.0.1:8000) — interactive docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Authentication

If `API_KEY` is set, requests must include:

```http
X-API-Key: your_api_key
```

If `API_KEY` is not set, the API is open (for local testing). `GET /health` never requires a key.

---

## API endpoints

### Health check

`GET /health`

### Create subcontractor

`POST /subcontractors`

Body:

```json
{
  "name": "CoolAir",
  "logo_url": null,
  "website_url": null,
  "is_active": true
}
```

### Add customer service contact

`POST /contacts`

Body:

```json
{
  "subcontractor_id": 1,
  "phone_number_e164": "+18005551234",
  "email": "support@coolair.com",
  "operating_hours": "Mon-Fri 9-5",
  "language": "en",
  "is_primary": true
}
```

### Add part number

`POST /part-numbers`

Body:

```json
{
  "subcontractor_id": 1,
  "part_number": "ABC123",
  "description": "AC Motor",
  "is_active": true
}
```

### Lookup customer service number (main endpoint)

- `GET /lookup-cs-number?part_number=ABC123`
- `GET /lookup-cs-number?subcontractor_name=CoolAir`
- `GET /lookup-cs-number?part_number=ABC123&subcontractor_name=CoolAir`

Returns:

```json
{
  "subcontractor_id": 1,
  "subcontractor_name": "CoolAir",
  "phone_number_e164": "+18005551234",
  "email": "support@coolair.com",
  "language": "en",
  "operating_hours": "Mon-Fri 9-5"
}
```

---

## Notes

- Part numbers are stored as unique and linked to a subcontractor.
- Each subcontractor can have multiple part numbers.
- Each subcontractor can have multiple customer service contacts, but only one should be marked `is_primary: true`.
- Phone numbers must be in **E.164** format (e.g. required for Twilio).
- This API is intended for use by an AI agent to look up the correct customer service number and initiate escalation.
