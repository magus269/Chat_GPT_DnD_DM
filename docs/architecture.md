# Architecture notes

## Core flows

1. **Players send action/question**
   - Stored as an event with optional `dndbeyond_roll_ref`.
2. **DM turn generation**
   - Loads campaign state + recent timeline.
   - Generates narration through provider.
   - Saves narration as event.
3. **Campaign memory persistence**
   - JSON file per campaign in `data/campaigns/`.
4. **Party interaction channel (MVP)**
   - Party members are represented as `players` on the campaign.
   - Player chat is organized as campaign `threads` with threaded messages.
5. **Friend-testing web console**
   - Static UI is served from `/app` for quick multiplayer trials.
6. **Source book context selection**
   - Source book options are exposed by `/metadata/source-books` and set on campaign.
7. **D&D Beyond adapter endpoints**
   - Store discovered DDB campaign URLs for the current party.
   - Connect one selected campaign URL to the local campaign.
   - Link DDB character URLs to local players.
   - Ingest external dice roll references as `dice_roll` events.
   - Support extension bridge token + bridge event ingestion for AboveVTT-style overlays.

## Auth approach (MVP)

- Campaign creation generates a `party_code` shared secret.
- Mutating/private endpoints require `X-Party-Code`.
- This keeps setup simple while enabling shared async play on one campaign.

## D&D Beyond strategy

- Treat D&D Beyond as external truth for:
  - character sheets,
  - official source access,
  - dice roll outcomes.
- Store references in this app so story continuity can include those outcomes.
- Do not collect or store DDB login credentials in this service.

## Next technical milestones

- Replace party-code auth with proper user auth + campaign membership.
- Switch persistence from JSON files to Postgres.
- Add websocket/chat channel for real-time and async push.
- Add summarization snapshots to reduce token usage.
- Add automation for D&D Beyond sync (extension-backed or authorized integration worker).
