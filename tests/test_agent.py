from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from app.agent import extractive_answer, llm_answer
from app.index import ChunkIndex
from app.ingest import load_chunks
from app.main import app

DATA = Path(__file__).resolve().parents[1] / "data" / "sample_configs"


@pytest.fixture(scope="module")
def index():
    return ChunkIndex(load_chunks(DATA))


def test_chunks_are_created_from_all_files():
    chunks = load_chunks(DATA)
    sources = {c.source for c in chunks}
    assert {"core-router-r1.cfg", "access-switch-sw1.cfg", "troubleshooting-runbook.md"} <= sources


def test_ospf_exstart_finds_mtu_runbook_entry(index):
    hits = index.search("OSPF neighbor stuck in EXSTART", k=3)
    assert hits[0].source == "troubleshooting-runbook.md"
    assert "MTU" in hits[0].text


def test_trunk_question_finds_switch_config(index):
    hits = index.search("which VLANs are allowed on the trunk to distribution", k=3)
    assert any(h.source == "access-switch-sw1.cfg" and "allowed vlan" in h.text for h in hits)


def test_unrelated_question_returns_no_hits(index):
    assert index.search("chocolate cake recipe", k=3) == []
    assert "could not find" in extractive_answer("chocolate cake recipe", [])


def test_llm_answer_uses_langchain_chain(index):
    fake = FakeListChatModel(responses=["Check the MTU on both ends (troubleshooting-runbook.md)."])
    hits = index.search("OSPF neighbor stuck in EXSTART", k=2)
    assert "MTU" in llm_answer("OSPF stuck?", hits, fake)


def test_api_health_and_query():
    with TestClient(app) as client:
        assert client.get("/health").json()["status"] == "ok"
        r = client.post("/query", json={"question": "BGP session stuck in Active", "top_k": 2})
        body = r.json()
        assert r.status_code == 200
        assert body["mode"] == "extractive"
        assert body["sources"][0]["source"] == "troubleshooting-runbook.md"
        assert client.post("/query", json={"question": "hi"}).status_code == 422
