from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class AIChatRequest(BaseModel):
    message: str
    context_filters: Optional[Dict[str, Any]] = None

class ToolCallInfo(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    output: Any

class AIChatResponse(BaseModel):
    reply: str
    tool_calls: List[ToolCallInfo] = []
    generated_at: str

class AIInsightItem(BaseModel):
    category: str # "Strength", "Risk", "Opportunity", "Trend"
    title: str
    description: str
    impact: str # "High", "Medium", "Low"
    metric_value: Optional[str] = None

class AIInsightsResponse(BaseModel):
    summary: str
    insights: List[AIInsightItem]
    recommendations: List[str]
    generated_at: str
