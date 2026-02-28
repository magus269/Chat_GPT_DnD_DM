from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class EventType(str, Enum):
    PLAYER_ACTION = "player_action"
    DM_NARRATION = "dm_narration"
    DICE_ROLL = "dice_roll"
    SYSTEM_NOTE = "system_note"


class CampaignEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: EventType
    actor: str
    content: str
    dndbeyond_roll_ref: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Player(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    character_name: Optional[str] = None
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    sender: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatThread(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    messages: List[ChatMessage] = Field(default_factory=list)


class Campaign(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    source_type: str = Field(
        default="custom", description="custom or source_book"
    )
    source_reference: Optional[str] = None
    summary: str = ""
    active_scene: str = ""
    party_code: str = Field(default_factory=lambda: str(uuid4())[:8])
    players: List[Player] = Field(default_factory=list)
    threads: List[ChatThread] = Field(default_factory=list)
    events: List[CampaignEvent] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CampaignContext(BaseModel):
    campaign_id: str
    title: str
    source_type: str
    source_reference: Optional[str] = None
    summary: str = ""
    active_scene: str = ""
    player_names: List[str] = Field(default_factory=list)
    recent_events: List[CampaignEvent] = Field(default_factory=list)


class CreateCampaignRequest(BaseModel):
    title: str
    source_type: str = "custom"
    source_reference: Optional[str] = None


class UpdateCampaignStateRequest(BaseModel):
    summary: Optional[str] = None
    active_scene: Optional[str] = None


class JoinPartyRequest(BaseModel):
    name: str
    character_name: Optional[str] = None


class CreateThreadRequest(BaseModel):
    title: str
    created_by: str


class PostThreadMessageRequest(BaseModel):
    sender: str
    content: str


class AddEventRequest(BaseModel):
    type: EventType
    actor: str
    content: str
    dndbeyond_roll_ref: Optional[str] = None


class GenerateTurnRequest(BaseModel):
    instructions: str = (
        "Respond as a D&D 5e DM. Keep continuity with prior events and ask for the next player action."
    )
