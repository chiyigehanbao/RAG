"""对话 REST API：持久化会话、多轮历史、Agent 调用与流式输出。"""
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from backend.agent.graph import build_graph
from backend.agent.history import HistoryMessage
from backend.agent.stream import stream_agent
from backend.db.models import ChatSession, Message, Trace
from backend.db.session import get_db
from backend.schemas.chat import ChatRequest, ChatResponse, MessageOut, SessionOut

router = APIRouter(prefix="/api", tags=["chat"])
_graph = None


def _get_graph():
    """懒加载编译后的 LangGraph。"""
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def _load_session_history(db: Session, session_id: str) -> list[HistoryMessage]:
    """读取该会话中已有消息（不含本轮尚未写入的内容）。"""
    rows = (
        db.query(Message)
        .filter_by(session_id=session_id)
        .order_by(Message.created_at)
        .all()
    )
    return [{"role": m.role, "content": m.content} for m in rows]


def run_agent(question: str, chat_history: list[HistoryMessage] | None = None) -> dict:
    """执行 Agent 并返回结果 dict。"""
    graph = _get_graph()
    return graph.invoke(
        {
            "question": question,
            "chat_history": chat_history or [],
            "node_trace": [],
        }
    )


@router.post("/chat", response_model=ChatResponse)
def post_chat(body: ChatRequest, db: Session = Depends(get_db)):
    """发送问题，持久化消息与 trace；携带同会话历史供多轮理解。"""
    session_id = body.session_id or str(uuid.uuid4())

    session = db.query(ChatSession).filter_by(id=session_id).first()
    if session is None:
        session = ChatSession(id=session_id, title=body.question[:30])
        db.add(session)

    # 在写入本轮用户消息前加载历史，供 Agent 理解上下文
    history = _load_session_history(db, session_id)

    user_msg = Message(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="user",
        content=body.question,
    )
    db.add(user_msg)
    db.flush()

    result = run_agent(body.question, chat_history=history)
    assistant_msg = Message(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="assistant",
        content=result.get("answer", ""),
    )
    db.add(assistant_msg)

    trace_payload = {
        "message_id": assistant_msg.id,
        "question": body.question,
        "nodes": result.get("node_trace", []),
        "citations": result.get("citations", []),
    }
    trace = Trace(
        id=str(uuid.uuid4()),
        message_id=assistant_msg.id,
        payload=json.dumps(trace_payload, ensure_ascii=False),
    )
    db.add(trace)
    db.commit()

    return ChatResponse(
        message_id=assistant_msg.id,
        session_id=session_id,
        answer=result.get("answer", ""),
        citations=result.get("citations", []),
        trace_id=trace.id,
    )


def _persist_assistant_turn(
    db: Session,
    session_id: str,
    question: str,
    answer: str,
    citations: list,
    node_trace: list,
) -> tuple[str, str]:
    """写入助手消息与 trace，返回 (message_id, trace_id)。"""
    assistant_msg = Message(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="assistant",
        content=answer,
    )
    db.add(assistant_msg)

    trace_payload = {
        "message_id": assistant_msg.id,
        "question": question,
        "nodes": node_trace,
        "citations": citations,
    }
    trace = Trace(
        id=str(uuid.uuid4()),
        message_id=assistant_msg.id,
        payload=json.dumps(trace_payload, ensure_ascii=False),
    )
    db.add(trace)
    db.commit()
    return assistant_msg.id, trace.id


@router.post("/chat/stream")
def post_chat_stream(body: ChatRequest):
    """SSE 流式问答：实时推送 LangGraph 节点与答案 token。"""
    from backend.db.session import SessionLocal

    session_id = body.session_id or str(uuid.uuid4())
    question = body.question

    db = SessionLocal()
    try:
        session = db.query(ChatSession).filter_by(id=session_id).first()
        if session is None:
            session = ChatSession(id=session_id, title=question[:30])
            db.add(session)
            db.commit()

        history = _load_session_history(db, session_id)
        user_msg = Message(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="user",
            content=question,
        )
        db.add(user_msg)
        db.commit()
    finally:
        db.close()

    def event_generator():
        answer = ""
        citations: list = []
        node_trace: list = []
        persist_db = SessionLocal()
        try:
            for payload in stream_agent(question, chat_history=history):
                if payload.get("type") == "error":
                    yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                    return
                if payload.get("type") == "done":
                    answer = payload.get("answer", "")
                    citations = payload.get("citations") or []
                    node_trace = payload.get("node_trace") or []
                    continue
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

            message_id, trace_id = _persist_assistant_turn(
                persist_db, session_id, question, answer, citations, node_trace
            )
            done = {
                "type": "done",
                "message_id": message_id,
                "session_id": session_id,
                "trace_id": trace_id,
                "answer": answer,
                "citations": citations,
            }
            yield f"data: {json.dumps(done, ensure_ascii=False)}\n\n"
        finally:
            persist_db.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/sessions", response_model=list[SessionOut])
def list_sessions(db: Session = Depends(get_db)):
    """会话列表，按最近创建排序。"""
    sessions = db.query(ChatSession).order_by(ChatSession.created_at.desc()).all()
    return [
        SessionOut(id=s.id, title=s.title, created_at=s.created_at.isoformat()) for s in sessions
    ]


def _citations_from_trace(message: Message) -> list[dict]:
    """从 trace 解析助手消息的引用列表。"""
    if message.trace is None:
        return []
    try:
        payload = json.loads(message.trace.payload)
    except json.JSONDecodeError:
        return []
    return payload.get("citations") or []


@router.get("/sessions/{session_id}/messages", response_model=list[MessageOut])
def list_messages(session_id: str, db: Session = Depends(get_db)):
    """会话消息历史（助手消息附带 citations）。"""
    if db.query(ChatSession).filter_by(id=session_id).first() is None:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = (
        db.query(Message)
        .options(joinedload(Message.trace))
        .filter_by(session_id=session_id)
        .order_by(Message.created_at)
        .all()
    )
    result: list[MessageOut] = []
    for msg in messages:
        citations = _citations_from_trace(msg) if msg.role == "assistant" else []
        result.append(
            MessageOut(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at.isoformat(),
                citations=citations,
            )
        )
    return result


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(session_id: str, db: Session = Depends(get_db)):
    """删除会话及其消息、trace（按 ID 批量删，避免 ORM 关系缓存冲突）。"""
    exists = db.query(ChatSession.id).filter_by(id=session_id).first()
    if exists is None:
        raise HTTPException(status_code=404, detail="Session not found")

    message_ids = [
        row[0] for row in db.query(Message.id).filter(Message.session_id == session_id).all()
    ]
    if message_ids:
        db.query(Trace).filter(Trace.message_id.in_(message_ids)).delete(synchronize_session=False)
    db.query(Message).filter(Message.session_id == session_id).delete(synchronize_session=False)
    db.query(ChatSession).filter(ChatSession.id == session_id).delete(synchronize_session=False)
    db.commit()
