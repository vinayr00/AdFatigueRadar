from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.models import Base, CampaignRow, CommentRow
from backend.db.repository import PostgreSQLRepository


def test_repository_campaign_settings_and_privacy_contract(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr("backend.db.repository.SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    repo = PostgreSQLRepository()
    repo.save_campaign({"id": "c-1", "name": "Campaign", "platform": "meta", "status": "ACTIVE",
        "pre_block_state": None, "budget": None, "created_at": datetime.now(timezone.utc), "metadata_json": {}})
    repo.save_workspace_settings({"workspace": {"name": "Stored"}})
    assert repo.get_workspace_settings() == {"workspace": {"name": "Stored"}}
    with engine.connect() as connection:
        campaign_columns = {column["name"] for column in __import__("sqlalchemy").inspect(connection).get_columns("campaigns")}
        comment_columns = {column["name"] for column in __import__("sqlalchemy").inspect(connection).get_columns("comments")}
    assert "pre_block_state" in campaign_columns
    assert "author_id" not in comment_columns
    assert "author_id_hmac" in comment_columns
    engine.dispose()
