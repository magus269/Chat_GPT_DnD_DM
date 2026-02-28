from fastapi.testclient import TestClient

from app.main import app


def test_campaign_flow_with_party_auth_and_chat_threads() -> None:
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

    unauthorized = client.patch(
        f"/campaigns/{campaign_id}",
        json={"summary": "No auth should fail."},
    )
    assert unauthorized.status_code == 401

    state_resp = client.patch(
        f"/campaigns/{campaign_id}",
        headers=headers,
        json={"summary": "The party reached Phandalin.", "active_scene": "Stonehill Inn"},
    )
    assert state_resp.status_code == 200

    join_resp = client.post(
        f"/campaigns/{campaign_id}/players",
        headers=headers,
        json={"name": "Alice", "character_name": "Aria"},
    )
    assert join_resp.status_code == 200
    assert len(join_resp.json()["players"]) == 1

    thread_resp = client.post(
        f"/campaigns/{campaign_id}/threads",
        headers=headers,
        json={"title": "Campfire Planning", "created_by": "Alice"},
    )
    assert thread_resp.status_code == 200
    thread_id = thread_resp.json()["threads"][0]["id"]

    message_resp = client.post(
        f"/campaigns/{campaign_id}/threads/{thread_id}/messages",
        headers=headers,
        json={"sender": "Alice", "content": "Let's scout before dawn."},
    )
    assert message_resp.status_code == 200
    assert message_resp.json()["threads"][0]["messages"][0]["content"] == "Let's scout before dawn."

    event_resp = client.post(
        f"/campaigns/{campaign_id}/events",
        headers=headers,
        json={
            "type": "player_action",
            "actor": "Aria",
            "content": "I inspect the locked chest for traps.",
            "dndbeyond_roll_ref": "ddb-roll-123",
        },
    )
    assert event_resp.status_code == 200

    context_resp = client.get(
        f"/campaigns/{campaign_id}/context?max_events=10",
        headers=headers,
    )
    assert context_resp.status_code == 200
    context = context_resp.json()
    assert context["active_scene"] == "Stonehill Inn"
    assert context["player_names"] == ["Alice"]
    assert len(context["recent_events"]) == 1

    dm_resp = client.post(
        f"/campaigns/{campaign_id}/dm-turn",
        headers=headers,
        json={"instructions": "Give a short result and prompt next action."},
    )
    assert dm_resp.status_code == 200

    data = dm_resp.json()
    assert len(data["events"]) >= 2
    assert data["events"][-1]["type"] == "dm_narration"
