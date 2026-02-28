from fastapi.testclient import TestClient

from app.main import app


def test_campaign_flow_with_party_auth_threads_and_dndbeyond_links() -> None:
    client = TestClient(app)

    root_resp = client.get("/", follow_redirects=False)
    assert root_resp.status_code in (302, 307)

    created = client.post(
        "/campaigns",
        json={
            "title": "Lost Mine Async",
            "source_type": "source_book",
            "source_reference": "DDB:LMoP",
        },
    )
    assert created.status_code == 200
    campaign = created.json()
    campaign_id = campaign["id"]
    party_code = campaign["party_code"]
    headers = {"X-Party-Code": party_code}

    join_resp = client.post(
        f"/campaigns/{campaign_id}/players",
        headers=headers,
        json={"name": "Alice", "character_name": "Aria"},
    )
    assert join_resp.status_code == 200
    player_id = join_resp.json()["players"][0]["id"]

    connect_resp = client.post(
        f"/campaigns/{campaign_id}/integrations/dndbeyond/connect",
        headers=headers,
        json={"campaign_url": "https://www.dndbeyond.com/campaigns/1234567"},
    )
    assert connect_resp.status_code == 200
    connected = connect_resp.json()
    assert connected["dndbeyond"]["campaign_id"] == "1234567"

    link_character_resp = client.post(
        f"/campaigns/{campaign_id}/integrations/dndbeyond/players/{player_id}/character-link",
        headers=headers,
        json={"character_url": "https://www.dndbeyond.com/characters/7654321"},
    )
    assert link_character_resp.status_code == 200
    assert link_character_resp.json()["dndbeyond"]["character_links"][0]["character_id"] == "7654321"

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

    dm_resp = client.post(
        f"/campaigns/{campaign_id}/dm-turn",
        headers=headers,
        json={"instructions": "Give a short result and prompt next action."},
    )
    assert dm_resp.status_code == 200

    data = dm_resp.json()
    assert len(data["events"]) >= 2
    assert data["events"][-1]["type"] == "dm_narration"
