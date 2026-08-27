import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database.db import get_db
from backend.database.models import User, ChatHistory
from backend.schemas.ai_schema import AIChatRequest, AIChatResponse, AIInsightsResponse
from backend.services.auth_service import get_current_user
from backend.ai_agent.agent import AISalesAnalystAgent

router = APIRouter(prefix="/api/ai", tags=["AI Sales Analyst Agent"])

@router.post("/chat", response_model=AIChatResponse)
def chat_with_sales_analyst(
    req: AIChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Question message cannot be empty.")

    try:
        agent = AISalesAnalystAgent(user_id=user.id, db=db)
        result = agent.chat(req.message)

        clean_tool_calls = []
        for tc in result.get("tool_calls", []):
            clean_tool_calls.append({
                "tool_name": str(tc.get("tool_name", "")),
                "arguments": tc.get("arguments", {}),
                "output": tc.get("output", {})
            })

        # Log user message
        user_log = ChatHistory(
            user_id=user.id,
            role="user",
            message=req.message
        )
        db.add(user_log)

        # Log agent response
        agent_log = ChatHistory(
            user_id=user.id,
            role="assistant",
            message=result.get("reply", "I have processed your query."),
            tool_calls_json=json.dumps(clean_tool_calls, default=str)
        )
        db.add(agent_log)
        db.commit()

        return AIChatResponse(
            reply=result.get("reply", "I have processed your query."),
            tool_calls=clean_tool_calls,
            generated_at=result.get("generated_at", datetime.utcnow().isoformat())
        )
    except Exception as e:
        db.rollback()
        return AIChatResponse(
            reply="I encountered an issue analyzing your query. Please try rephrasing or asking about your sales data.",
            tool_calls=[],
            generated_at=datetime.utcnow().isoformat()
        )

@router.get("/insights", response_model=AIInsightsResponse)
def get_ai_automated_insights(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    try:
        agent = AISalesAnalystAgent(user_id=user.id, db=db)
        res = agent.generate_automated_insights()
        return AIInsightsResponse(
            summary=res.get("summary", "No insights available."),
            insights=res.get("insights", []),
            recommendations=res.get("recommendations", []),
            generated_at=res.get("generated_at", datetime.utcnow().isoformat())
        )
    except Exception:
        return AIInsightsResponse(
            summary="No sales data available yet. Please upload sales records.",
            insights=[],
            recommendations=["Upload a sales dataset to unlock automated business insights."],
            generated_at=datetime.utcnow().isoformat()
        )

@router.get("/alerts")
def get_ai_anomaly_alerts(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    try:
        agent = AISalesAnalystAgent(user_id=user.id, db=db)
        return agent.generate_anomaly_alerts()
    except Exception:
        return {
            "alerts": [],
            "unread_count": 0,
            "generated_at": datetime.utcnow().isoformat()
        }

@router.get("/chat-history")
def get_chat_history(
    limit: int = 30,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    logs = db.query(ChatHistory).filter(
        ChatHistory.user_id == user.id
    ).order_by(ChatHistory.id.asc()).limit(limit).all()

    return [
        {
            "id": l.id,
            "role": l.role,
            "message": l.message,
            "tool_calls": json.loads(l.tool_calls_json) if l.tool_calls_json else [],
            "created_at": l.created_at.isoformat() if l.created_at else ""
        }
        for l in logs
    ]

@router.delete("/chat-history")
def clear_chat_history(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    deleted_count = db.query(ChatHistory).filter(ChatHistory.user_id == user.id).delete()
    db.commit()
    return {"status": "success", "message": f"Cleared {deleted_count} messages."}

