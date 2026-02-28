from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from app.models import (
    Campaign,
    CampaignContext,
    CampaignEvent,
    ChatMessage,
    ChatThread,
    Player,
)


class CampaignRepository:
    def __init__(self, base_path: str = "data/campaigns"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _path_for(self, campaign_id: str) -> Path:
        return self.base_path / f"{campaign_id}.json"

    def list_campaigns(self) -> List[Campaign]:
        campaigns: List[Campaign] = []
        for file in self.base_path.glob("*.json"):
            campaigns.append(Campaign.model_validate_json(file.read_text()))
        return sorted(campaigns, key=lambda c: c.updated_at, reverse=True)

    def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        path = self._path_for(campaign_id)
        if not path.exists():
            return None
        return Campaign.model_validate_json(path.read_text())

    def save_campaign(self, campaign: Campaign) -> Campaign:
        campaign.updated_at = datetime.now(timezone.utc)
        self._path_for(campaign.id).write_text(
            json.dumps(campaign.model_dump(mode="json"), indent=2)
        )
        return campaign

    def update_campaign_state(
        self,
        campaign_id: str,
        summary: Optional[str] = None,
        active_scene: Optional[str] = None,
    ) -> Optional[Campaign]:
        campaign = self.get_campaign(campaign_id)
        if campaign is None:
            return None

        if summary is not None:
            campaign.summary = summary
        if active_scene is not None:
            campaign.active_scene = active_scene

        return self.save_campaign(campaign)

    def add_player(self, campaign_id: str, player: Player) -> Optional[Campaign]:
        campaign = self.get_campaign(campaign_id)
        if campaign is None:
            return None
        campaign.players.append(player)
        return self.save_campaign(campaign)

    def create_thread(self, campaign_id: str, thread: ChatThread) -> Optional[Campaign]:
        campaign = self.get_campaign(campaign_id)
        if campaign is None:
            return None
        campaign.threads.append(thread)
        return self.save_campaign(campaign)

    def add_thread_message(
        self,
        campaign_id: str,
        thread_id: str,
        message: ChatMessage,
    ) -> Optional[Campaign]:
        campaign = self.get_campaign(campaign_id)
        if campaign is None:
            return None

        for thread in campaign.threads:
            if thread.id == thread_id:
                thread.messages.append(message)
                return self.save_campaign(campaign)
        return None

    def append_event(self, campaign_id: str, event: CampaignEvent) -> Optional[Campaign]:
        campaign = self.get_campaign(campaign_id)
        if campaign is None:
            return None
        campaign.events.append(event)
        return self.save_campaign(campaign)

    def campaign_context(
        self,
        campaign_id: str,
        max_events: int = 25,
    ) -> Optional[CampaignContext]:
        campaign = self.get_campaign(campaign_id)
        if campaign is None:
            return None

        recent_events = campaign.events[-max_events:] if max_events > 0 else []

        return CampaignContext(
            campaign_id=campaign.id,
            title=campaign.title,
            source_type=campaign.source_type,
            source_reference=campaign.source_reference,
            summary=campaign.summary,
            active_scene=campaign.active_scene,
            player_names=[player.name for player in campaign.players],
            recent_events=recent_events,
        )
