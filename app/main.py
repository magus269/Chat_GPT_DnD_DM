from __future__ import annotations

import os
from pathlib import Path
from typing import List

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.dm_service import DMService
from app.dndbeyond import extract_campaign_id, extract_character_id
from app.models import (
    AddEventRequest,
    Campaign,
    CampaignContext,
    CampaignEvent,
    ChatMessage,
    ChatThread,
    ConnectDndBeyondRequest,
    CreateCampaignRequest,
    CreateThreadRequest,
    DiscoverDndBeyondCampaignsRequest,
    DndBeyondCampaignSummary,
    DndBeyondRollRequest,
    EventType,
    GenerateTurnRequest,
    JoinPartyRequest,
    LinkDndBeyondCharacterRequest,
    Player,
    PostThreadMessageRequest,
    SetSourceBookRequest,
    SourceBookOption,
    UpdateCampaignStateRequest,
)
from app.repository import CampaignRepository

app = FastAPI(title="Async D&D DM App", version="0.6.0")
repo = CampaignRepository()

SOURCE_BOOK_OPTIONS = [
    SourceBookOption(key="phb", title="Player's Handbook"),
    SourceBookOption(key="xgte", title="Xanathar's Guide to Everything"),
    SourceBookOption(key="tcoe", title="Tasha's Cauldron of Everything"),
    SourceBookOption(key="lmoP", title="Lost Mine of Phandelver"),
    SourceBookOption(key="cos", title="Curse of Strahd"),
    SourceBookOption(key="toA", title="Tomb of Annihilation"),
    SourceBookOption(key="bgdia", title="Baldur's Gate: Descent Into Avernus"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_path = Path(__file__).parent / "static"
app.mount("/app", StaticFiles(directory=static_path, html=True), name="app")


def _dm_service() -> DMService:
    return DMService(provider_name=os.getenv("DM_PROVIDER", "mock"))


def _campaign_or_404(campaign_id: str) -> Campaign:
    campaign = repo.get_campaign(campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


def _require_party_access(campaign: Campaign, x_party_code: str | None) -> None:
    if not x_party_code:
        raise HTTPException(status_code=401, detail="Missing X-Party-Code header")
    if x_party_code != campaign.party_code:
        raise HTTPException(status_code=403, detail="Invalid party code")


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/app")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/metadata/source-books", response_model=List[SourceBookOption])
def list_source_books() -> List[SourceBookOption]:
    return SOURCE_BOOK_OPTIONS


@app.post("/campaigns", response_model=Campaign)
def create_campaign(req: CreateCampaignRequest) -> Campaign:
    campaign = Campaign(
        title=req.title,
        source_type=req.source_type,
        source_reference=req.source_reference,
    )
    return repo.save_campaign(campaign)


@app.get("/campaigns", response_model=List[Campaign])
def list_campaigns() -> List[Campaign]:
    return repo.list_campaigns()


@app.get("/campaigns/{campaign_id}", response_model=Campaign)
def get_campaign(campaign_id: str) -> Campaign:
    return _campaign_or_404(campaign_id)


@app.patch("/campaigns/{campaign_id}", response_model=Campaign)
def update_campaign_state(
    campaign_id: str,
    req: UpdateCampaignStateRequest,
    x_party_code: str | None = Header(default=None),
) -> Campaign:
    campaign = _campaign_or_404(campaign_id)
    _require_party_access(campaign, x_party_code)

    updated = repo.update_campaign_state(
        campaign_id,
        summary=req.summary,
        active_scene=req.active_scene,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return updated


@app.post("/campaigns/{campaign_id}/source-book", response_model=Campaign)
def set_source_book(
    campaign_id: str,
    req: SetSourceBookRequest,
    x_party_code: str | None = Header(default=None),
) -> Campaign:
    campaign = _campaign_or_404(campaign_id)
    _require_party_access(campaign, x_party_code)

    updated = repo.set_source_book(campaign_id, req.key, req.title)
    if updated is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return updated


@app.post("/campaigns/{campaign_id}/integrations/dndbeyond/discover-campaigns", response_model=Campaign)
def discover_dndbeyond_campaigns(
    campaign_id: str,
    req: DiscoverDndBeyondCampaignsRequest,
    x_party_code: str | None = Header(default=None),
) -> Campaign:
    campaign = _campaign_or_404(campaign_id)
    _require_party_access(campaign, x_party_code)

    discovered: List[DndBeyondCampaignSummary] = []
    for item in req.campaigns:
        campaign_url = str(item.campaign_url)
        discovered.append(
            DndBeyondCampaignSummary(
                campaign_url=campaign_url,
                campaign_id=extract_campaign_id(campaign_url),
                title=item.title,
            )
        )

    updated = repo.discover_dndbeyond_campaigns(campaign_id, discovered)
    if updated is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return updated


@app.post("/campaigns/{campaign_id}/integrations/dndbeyond/connect", response_model=Campaign)
def connect_dndbeyond_campaign(
    campaign_id: str,
    req: ConnectDndBeyondRequest,
    x_party_code: str | None = Header(default=None),
) -> Campaign:
    campaign = _campaign_or_404(campaign_id)
    _require_party_access(campaign, x_party_code)

    ddb_campaign_id = extract_campaign_id(str(req.campaign_url))
    updated = repo.update_dndbeyond_campaign(
        campaign_id,
        campaign_url=str(req.campaign_url),
        dndbeyond_campaign_id=ddb_campaign_id,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return updated


@app.post(
    "/campaigns/{campaign_id}/integrations/dndbeyond/players/{player_id}/character-link",
    response_model=Campaign,
)
def link_dndbeyond_character(
    campaign_id: str,
    player_id: str,
    req: LinkDndBeyondCharacterRequest,
    x_party_code: str | None = Header(default=None),
) -> Campaign:
    campaign = _campaign_or_404(campaign_id)
    _require_party_access(campaign, x_party_code)

    ddb_character_id = extract_character_id(str(req.character_url))
    updated = repo.link_dndbeyond_character(
        campaign_id,
        player_id=player_id,
        character_url=str(req.character_url),
        character_id=ddb_character_id,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Campaign or player not found")
    return updated


@app.post("/campaigns/{campaign_id}/integrations/dndbeyond/rolls", response_model=Campaign)
def add_dndbeyond_roll(
    campaign_id: str,
    req: DndBeyondRollRequest,
    x_party_code: str | None = Header(default=None),
) -> Campaign:
    campaign = _campaign_or_404(campaign_id)
    _require_party_access(campaign, x_party_code)

    roll_event = CampaignEvent(
        type=EventType.DICE_ROLL,
        actor=req.actor,
        content=req.content,
        dndbeyond_roll_ref=req.roll_reference,
    )
    updated = repo.append_event(campaign_id, roll_event)
    if updated is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return updated


@app.post("/campaigns/{campaign_id}/players", response_model=Campaign)
def join_party(
    campaign_id: str,
    req: JoinPartyRequest,
    x_party_code: str | None = Header(default=None),
) -> Campaign:
    campaign = _campaign_or_404(campaign_id)
    _require_party_access(campaign, x_party_code)

    player = Player(name=req.name, character_name=req.character_name)
    updated = repo.add_player(campaign_id, player)
    if updated is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return updated


@app.get("/campaigns/{campaign_id}/context", response_model=CampaignContext)
def get_campaign_context(
    campaign_id: str,
    max_events: int = Query(default=25, ge=1, le=200),
    x_party_code: str | None = Header(default=None),
) -> CampaignContext:
    campaign = _campaign_or_404(campaign_id)
    _require_party_access(campaign, x_party_code)

    context = repo.campaign_context(campaign_id, max_events=max_events)
    if context is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return context


@app.post("/campaigns/{campaign_id}/threads", response_model=Campaign)
def create_thread(
    campaign_id: str,
    req: CreateThreadRequest,
    x_party_code: str | None = Header(default=None),
) -> Campaign:
    campaign = _campaign_or_404(campaign_id)
    _require_party_access(campaign, x_party_code)

    thread = ChatThread(title=req.title, created_by=req.created_by)
    updated = repo.create_thread(campaign_id, thread)
    if updated is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return updated


@app.post("/campaigns/{campaign_id}/threads/{thread_id}/messages", response_model=Campaign)
def post_thread_message(
    campaign_id: str,
    thread_id: str,
    req: PostThreadMessageRequest,
    x_party_code: str | None = Header(default=None),
) -> Campaign:
    campaign = _campaign_or_404(campaign_id)
    _require_party_access(campaign, x_party_code)

    message = ChatMessage(sender=req.sender, content=req.content)
    updated = repo.add_thread_message(campaign_id, thread_id, message)
    if updated is None:
        raise HTTPException(status_code=404, detail="Campaign or thread not found")
    return updated


@app.post("/campaigns/{campaign_id}/events", response_model=Campaign)
def add_event(
    campaign_id: str,
    req: AddEventRequest,
    x_party_code: str | None = Header(default=None),
) -> Campaign:
    campaign = _campaign_or_404(campaign_id)
    _require_party_access(campaign, x_party_code)

    event = CampaignEvent(
        type=req.type,
        actor=req.actor,
        content=req.content,
        dndbeyond_roll_ref=req.dndbeyond_roll_ref,
    )
    updated = repo.append_event(campaign_id, event)
    if updated is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return updated


@app.post("/campaigns/{campaign_id}/dm-turn", response_model=Campaign)
def generate_dm_turn(
    campaign_id: str,
    req: GenerateTurnRequest,
    x_party_code: str | None = Header(default=None),
) -> Campaign:
    campaign = _campaign_or_404(campaign_id)
    _require_party_access(campaign, x_party_code)

    dm_event = _dm_service().run_turn(campaign, req.instructions)
    updated = repo.append_event(campaign_id, dm_event)
    if updated is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return updated
