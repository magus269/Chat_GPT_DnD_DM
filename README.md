# Async D&D DM App (MVP Skeleton)

This repository contains a starter backend for an **asynchronous D&D campaign manager** where:

- Players submit actions/questions from their phones.
- A DM engine (intended to be ChatGPT) responds in turn.
- Campaign state and story memory are persisted so sessions stay consistent over time.
- D&D Beyond remains the source of truth for character sheets and dice rolls.

## Current MVP features

- Create, list, fetch, and update campaign state (summary + active scene).
- Party access guard for campaign mutations via `X-Party-Code` header.
- Choose a source book from API-provided options and attach it to campaign context.
- Join players to a campaign.
- Create chat threads and post thread messages.
- Append timeline events (player action, dice roll reference, system note, DM narration).
- Fetch a compact campaign context payload for DM prompting (`/campaigns/{id}/context`).
- Generate a DM turn from campaign context via a pluggable provider:
  - `mock` provider (default, offline-safe).
  - `openai` provider (requires `OPENAI_API_KEY`, optional package).
- D&D Beyond adapter endpoints:
  - store discovered/accessible DDB campaign URLs for a campaign
  - connect one DDB campaign URL to local campaign metadata
  - link each player to a DDB character URL
  - ingest DDB roll references into campaign events
  - rotate campaign bridge tokens + ingest browser-extension bridge events (AboveVTT-style pattern)
- Includes a basic browser test UI at `/app` with source book dropdown, dice-roll capture, and bridge-token test tools.
- Persist campaign state to `./data/campaigns/*.json`.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# optional for real AI DM responses
pip install openai
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open:

- Party test UI: `http://127.0.0.1:8000/app`
- API docs: `http://127.0.0.1:8000/docs`

## D&D Beyond integration status

This app does **not** request or store D&D Beyond account credentials.

Current integration is adapter-style:

1. Discover/store campaign URLs you can access from DDB (`/discover-campaigns`).
2. Select one campaign URL and connect it (`/connect`).
3. Link local players to DDB character URLs (`/character-link`).
4. Record DDB roll references into the campaign timeline (`/rolls`).
5. For AboveVTT-style automation, rotate a campaign bridge token and ingest extension events via `/integrations/dndbeyond/bridge-events`.

This gives you continuity and traceability now, while leaving room for future automation (e.g., browser extension sync).

## Running a first friend test

1. Create a campaign from `/app`.
2. Copy the generated `party_code`.
3. Pick a source book from dropdown and save it.
4. Add/connect DDB campaign URL.
5. Join players, post actions, capture DDB roll references.
6. Trigger DM turn generation after player actions.

## Sharing a temporary public link

If you want quick external testing without deploying a full stack, run a tunnel from your machine.

Example with `ngrok`:

```bash
ngrok http 8000
```

Then share the generated HTTPS URL, and have friends open `<url>/app`.

## Suggested next steps

1. Replace party-code header auth with real user auth (JWT/session).
2. Add role permissions (DM/co-DM/player/observer).
3. Add websocket updates for live chat without polling.
4. Add a D&D Beyond automation layer (extension-backed sync worker).
5. Switch persistence from JSON files to Postgres.
