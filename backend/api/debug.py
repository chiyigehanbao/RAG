"""调试 trace API。"""
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db.models import Trace
from backend.db.session import get_db

router = APIRouter(prefix="/api", tags=["debug"])


@router.get("/traces/{message_id}")
def get_trace(message_id: str, db: Session = Depends(get_db)):
    """按 assistant message_id 返回完整 trace JSON。"""
    trace = db.query(Trace).filter_by(message_id=message_id).first()
    if trace is None:
        raise HTTPException(status_code=404, detail="Trace not found")
    return json.loads(trace.payload)
