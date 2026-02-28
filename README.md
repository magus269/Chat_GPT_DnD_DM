# Async D&D DM App (MVP Skeleton)

This repository contains a starter backend for an **asynchronous D&D campaign manager** where:

- Players submit actions/questions from their phones.
- A DM engine (intended to be ChatGPT) responds in turn.
- Campaign state and story memory are persisted so sessions stay consistent over time.
- D&D Beyond remains the source of truth for character sheets and dice rolls.

## Current MVP features

- Create, list, fetch, and update campaign state (summary + active scene).
- Party access guard for campaign mutations via `X-Party-Code` header.
- Join players to a campaign.
- Create chat threads and post thread messages.
- Append timeline events (player action, dice roll reference, system note, DM narration).
- Fetch a compact campaign context payload for DM prompting (`/campaigns/{id}/context`).
- Generate a DM turn from campaign context via a pluggable provider:
  - `mock` provider (default, offline-safe).
  - `openai` provider (requires `OPENAI_API_KEY`, optional package).
- Includes a basic browser test UI at `/app`.
- Persist campaign state to `./data/campaigns/*.json`.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open:

- Party test UI: `http://127.0.0.1:8000/app`
- API docs: `http://127.0.0.1:8000/docs`

## Running a first friend test

1. Create a campaign from `/app`.
2. Copy the generated `party_code`.
3. Share your hosted link and `party_code` with friends.
4. Friends can join + post actions.
5. Trigger DM turn generation after player actions.

## Sharing a temporary public link

If you want quick external testing without deploying a full stack, run a tunnel from your machine.

Example with `ngrok`:

```bash
ngrok http 8000
```

Then share the generated HTTPS URL, and have friends open `<url>/app`.

## Party auth behavior (current MVP)

- `POST /campaigns` returns a generated `party_code`.
- Include that value in `X-Party-Code` for mutating or private context endpoints.
- This is a lightweight shared-secret approach for MVP only; replace with proper auth before production.

## Suggested next steps

1. Replace party-code header auth with real user auth (JWT/session).
2. Add role permissions (DM/co-DM/player/observer).
3. Add websocket updates for live chat without polling.
4. Add D&D Beyond connector for roll + character sync.
5. Switch persistence from JSON files to Postgres.

## Notes on D&D Beyond integration

D&D Beyond does not provide an official fully open API for all campaign interactions, so production integration may require one of:

- user-authorized data export/import workflows,
- browser-extension-assisted sync,
- or manual linking endpoints.
