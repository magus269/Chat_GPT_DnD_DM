from fastapi.testclient import TestClient

from app.main import app


def test_campaign_flow_with_source_books_and_dndbeyond_campaign_discovery() -> None:
    client = TestClient(app)

    source_books = client.get("/metadata/source-books")
    assert source_books.status_code == 200
    assert len(source_books.json()) > 0

    created = client.post(
        "/campaigns",
        json={
            "title": "Lost Mine Async",
            "source_type": "custom",
        },
    )
    assert created.status_code == 200
    campaign = created.json()
    campaign_id = campaign["id"]
    party_code = campaign["party_code"]
    headers = {"X-Party-Code": party_code}

    set_book = client.post(
        f"/campaigns/{campaign_id}/source-book",
        headers=headers,
        json={"key": "cos", "title": "Curse of Strahd"},
    )
    assert set_book.status_code == 200
    assert set_book.json()["source_book"] == "Curse of Strahd"

    discovered = client.post(
        f"/campaigns/{campaign_id}/integrations/dndbeyond/discover-campaigns",
        headers=headers,
        json={
            "campaigns": [
                {
                    "campaign_url": "https://www.dndbeyond.com/campaigns/1234567",
                    "title": "Curse of Strahd Party",
                }
            ]
        },
    )
    assert discovered.status_code == 200
    assert discovered.json()["dndbeyond"]["accessible_campaigns"][0]["campaign_id"] == "1234567"

    connect = client.post(
        f"/campaigns/{campaign_id}/integrations/dndbeyond/connect",
        headers=headers,
        json={"campaign_url": "https://www.dndbeyond.com/campaigns/1234567"},
    )
    assert connect.status_code == 200

    join_resp = client.post(
        f"/campaigns/{campaign_id}/players",
        headers=headers,
        json={"name": "Alice", "character_name": "Aria"},
    )
    assert join_resp.status_code == 200
    player_id = join_resp.json()["players"][0]["id"]

    link_character_resp = client.post(
        f"/campaigns/{campaign_id}/integrations/dndbeyond/players/{player_id}/character-link",
        headers=headers,
        json={"character_url": "https://www.dndbeyond.com/characters/7654321"},
    )
    assert link_character_resp.status_code == 200

    roll_resp = client.post(
        f"/campaigns/{campaign_id}/integrations/dndbeyond/rolls",
        headers=headers,
        json={
            "actor": "Aria",
            "content": "Rolled Stealth check: 17",
            "roll_reference": "ddb-roll-abc-123",
        },
    )
    assert roll_resp.status_code == 200
    assert roll_resp.json()["events"][-1]["type"] == "dice_roll"


    rotate_token = client.post(
        f"/campaigns/{campaign_id}/integrations/dndbeyond/bridge-token/rotate",
        headers=headers,
    )
    assert rotate_token.status_code == 200
    bridge_token = rotate_token.json()["bridge_token"]

    bridge_roll = client.post(
        "/integrations/dndbeyond/bridge-events",
        json={
            "campaign_id": campaign_id,
            "bridge_token": bridge_token,
            "event_type": "dice_roll",
            "actor": "Aria",
            "content": "Bridge roll: Perception 14",
            "roll_reference": "ddb-roll-bridge-1",
        },
    )
    assert bridge_roll.status_code == 200
    assert bridge_roll.json()["events"][-1]["type"] == "dice_roll"
