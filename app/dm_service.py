from __future__ import annotations

import os
from typing import Protocol

from app.models import Campaign, CampaignEvent, EventType


class DMProvider(Protocol):
    def generate(self, campaign: Campaign, instructions: str) -> str:
        ...


class MockDMProvider:
    def generate(self, campaign: Campaign, instructions: str) -> str:
        recent = campaign.events[-1].content if campaign.events else "the beginning of the adventure"
        return (
            f"The world reacts to {recent}. "
            "Describe your next move, and include any D&D Beyond roll reference if you rolled."
        )


class OpenAIDMProvider:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is required for provider=openai")

    def generate(self, campaign: Campaign, instructions: str) -> str:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "openai package is not installed. Install it or use provider=mock"
            ) from exc

        client = OpenAI(api_key=self.api_key)

        timeline = "\n".join(
            f"- [{event.type}] {event.actor}: {event.content}"
            for event in campaign.events[-25:]
        )

        prompt = (
            f"Campaign title: {campaign.title}\n"
            f"Source: {campaign.source_type} / {campaign.source_reference or 'n/a'}\n"
            f"Summary: {campaign.summary or 'n/a'}\n"
            f"Active scene: {campaign.active_scene or 'n/a'}\n"
            f"Recent timeline:\n{timeline or '- no events yet'}\n\n"
            f"Instructions: {instructions}"
        )

        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
        )

        return response.output_text.strip()


class DMService:
    def __init__(self, provider_name: str = "mock"):
        if provider_name == "openai":
            self.provider: DMProvider = OpenAIDMProvider()
        else:
            self.provider = MockDMProvider()

    def run_turn(self, campaign: Campaign, instructions: str) -> CampaignEvent:
        narration = self.provider.generate(campaign, instructions)
        return CampaignEvent(type=EventType.DM_NARRATION, actor="DM", content=narration)
