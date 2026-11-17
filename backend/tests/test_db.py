"""数据库模型测试。"""
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.models import Base, ChatSession, Message


def test_create_session_and_message():
    """能创建会话并写入消息。"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()

    session = ChatSession(id=str(uuid.uuid4()), title="测试会话")
    db.add(session)
    db.commit()

    msg = Message(
        id=str(uuid.uuid4()),
        session_id=session.id,
        role="user",
        content="你好",
    )
    db.add(msg)
    db.commit()

    assert db.query(Message).count() == 1
