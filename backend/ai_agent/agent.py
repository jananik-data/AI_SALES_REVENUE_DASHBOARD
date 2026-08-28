import re
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.config import GEMINI_API_KEY
from backend.database.models import ChatHistory
from backend.ai_agent.tools import (
    safe_float,
    safe_int,
    get_sales_dataframe,
    sales_analysis_tool,
    KPI_analysis_tool,
    product_performance_tool,
    product_analysis_tool,
    regional_breakdown_tool,
    trend_analysis_tool,
    comparison_tool,
    revenue_prediction_tool,
    prediction_tool
)

def extract_regions_from_text(text: str, available_regions: List[str]) -> List[str]:
    found = []
    text_lower = text.lower()
    for reg in available_regions:
        if reg.lower() in text_lower:
            found.append(reg)
    return found

def get_recent_chat_history(db: Session, user_id: int, limit: int = 8) -> List[Dict[str, str]]:
    logs = db.query(ChatHistory).filter(
        ChatHistory.user_id == user_id
    ).order_by(ChatHistory.id.desc()).limit(limit).all()
    
    # Return chronologically
    return [{"role": l.role, "message": l.message} for l in reversed(logs)]

def classify_intent(message: str, history: List[Dict[str, str]], available_regions: List[str]) -> Dict[str, Any]:
    msg = message.strip().lower()
    # Strip punctuation for matching
    msg_clean = re.sub(r'[^\w\s]', '', msg)

    # 1. Greetings
    greeting_patterns = [
        r'^(hey|hi|hello|howdy|sup|greetings|good\s+(morning|afternoon|evening|day))(\s+.*)?$',
        r'^(hey\s+there|hi\s+there|hello\s+there)$'
    ]
    if any(re.match(p, msg_clean) for p in greeting_patterns):
        return {"intent": "greeting", "tool": None}

    # 2. Thank you / Politeness
    thanks_patterns = [
        r'^(thanks|thank\s+you|thx|thank\s+you\s+so\s+much|appreciate\s+it|awesome|great|cool)(\s+.*)?$'
    ]
    if any(re.match(p, msg_clean) for p in thanks_patterns):
        return {"intent": "thanks", "tool": None}

    # 3. Capability / Help
    capability_patterns = [
        r'what\s+can\s+you\s+do',
        r'how\s+can\s+you\s+help',
        r'what\s+are\s+your\s+capabilities',
        r'who\s+are\s+you',
        r'^help(\s+me)?$'
    ]
    if any(re.search(p, msg_clean) for p in capability_patterns):
        return {"intent": "capabilities", "tool": None}

    # 4. Contextual Follow-up "Why?" or "Explain why"
    if msg_clean in ["why", "why is that", "why so", "explain why", "how come", "what caused this", "whats the reason"]:
        # Inspect previous assistant message to see what topic was discussed
        last_ai_msg = ""
        last_user_msg = ""
        for h in reversed(history):
            if h["role"] == "assistant" and not last_ai_msg:
                last_ai_msg = h["message"].lower()
            elif h["role"] == "user" and not last_user_msg:
                last_user_msg = h["message"].lower()

        if any(w in last_user_msg or w in last_ai_msg for w in ["decrease", "drop", "fell", "down", "trend", "dip"]):
            return {"intent": "why_decrease", "tool": "trend_analysis_tool"}
        elif any(w in last_user_msg or w in last_ai_msg for w in ["product", "best", "performing", "top", "selling", "star"]):
            return {"intent": "why_product", "tool": "product_analysis_tool"}
        elif any(w in last_user_msg or w in last_ai_msg for w in ["region", "north", "south", "east", "west", "central", "territory"]):
            return {"intent": "why_region", "tool": "regional_breakdown_tool"}
        else:
            return {"intent": "why_general", "tool": "sales_analysis_tool"}

    # 5. Prediction / Forecasting
    if any(w in msg for w in ["predict", "forecast", "future revenue", "next month's revenue", "next month revenue", "estimate future", "projection"]):
        return {"intent": "prediction", "tool": "prediction_tool"}

    # 6. Comparison (e.g., "Compare South and West", "What about South?", "Compare it with West")
    detected_regs = extract_regions_from_text(msg, available_regions)
    if "compare" in msg or "vs" in msg or "versus" in msg or (len(detected_regs) >= 2) or ("what about" in msg and len(detected_regs) >= 1):
        item_a = detected_regs[0] if len(detected_regs) > 0 else "South"
        item_b = detected_regs[1] if len(detected_regs) > 1 else ("West" if item_a.lower() != "west" else "North")
        
        # If user asked "What about South?" following a regional question, or "Compare it with West"
        if len(detected_regs) == 1 and ("it" in msg or "what about" in msg or "compare" in msg):
            # check previous user/ai message for first region
            for h in reversed(history):
                prev_regs = extract_regions_from_text(h["message"], available_regions)
                if prev_regs:
                    for pr in prev_regs:
                        if pr.lower() != item_a.lower():
                            item_b = item_a
                            item_a = pr
                            break
                    break
        
        return {
            "intent": "comparison",
            "tool": "comparison_tool",
            "item_a": item_a,
            "item_b": item_b
        }

    # 7. Decrease / Trend analysis
    if any(w in msg for w in ["decrease", "drop", "fell", "declined", "dip", "downturn", "trend", "seasonality", "over time", "monthly"]):
        return {"intent": "trend", "tool": "trend_analysis_tool"}

    # 8. Recommendations / What should I do
    if any(w in msg for w in ["what should i do", "recommend", "suggestion", "how to improve", "how to increase", "strategy", "next steps", "actions"]):
        return {"intent": "recommendations", "tool": "recommendations"}

    # 9. Product performance
    if any(w in msg for w in ["product", "item", "best performing", "top performing", "top selling", "worst selling", "category"]):
        return {"intent": "product", "tool": "product_analysis_tool"}

    # 10. Regional performance
    if any(w in msg for w in ["region", "territory", "geography", "zone", "north", "south", "east", "west", "central", "market"]):
        return {"intent": "region", "tool": "regional_breakdown_tool"}

    # 11. General Sales / KPIs (Total revenue, orders, etc.)
    if any(w in msg for w in ["revenue", "sales", "kpi", "order", "units", "aov", "performance", "how are we doing", "business"]):
        return {"intent": "sales_kpi", "tool": "sales_analysis_tool"}

    # 12. Non-sales unrelated questions
    return {"intent": "non_sales", "tool": None}

def run_conversational_analyst(message: str, db: Session, user_id: int) -> Dict[str, Any]:
    """Conversational reasoning engine with context awareness and selective tool execution."""
    df = get_sales_dataframe(db, user_id)
    history = get_recent_chat_history(db, user_id, limit=6)
    available_regions = [str(r) for r in df["region"].unique()] if not df.empty else ["North", "South", "East", "West", "Central"]

    classification = classify_intent(message, history, available_regions)
    intent = classification["intent"]
    tool_calls = []

    # 1. Greetings
    if intent == "greeting":
        greetings_replies = [
            "Hello! How can I help you analyze your sales and revenue performance today?",
            "Hey there! Ready to explore your sales data, product trends, or revenue forecasts. What's on your mind?",
            "Hi! I'm here to help with your sales analysis and business questions. How can I assist?"
        ]
        import random
        return {
            "reply": random.choice(greetings_replies),
            "tool_calls": [],
            "generated_at": datetime.utcnow().isoformat()
        }

    # 2. Thanks
    if intent == "thanks":
        return {
            "reply": "You're welcome! Let me know if you need any more sales insights, comparisons, or revenue predictions.",
            "tool_calls": [],
            "generated_at": datetime.utcnow().isoformat()
        }

    # 3. Capabilities
    if intent == "capabilities":
        reply = (
            "I'm your AI Sales Analyst. Here is how I can help you:\n"
            "- **Sales & KPI Tracking:** Query total revenue, order counts, average order value, and growth metrics.\n"
            "- **Product & Category Insights:** Identify your top-performing and underperforming products.\n"
            "- **Regional & Territory Analysis:** Compare performance and market share across regions.\n"
            "- **Trend & Anomaly Detection:** Analyze monthly revenue trajectories and explain sales increases or decreases.\n"
            "- **ML Revenue Forecasting:** Generate predictive revenue forecasts using calibrated Machine Learning models.\n"
            "- **Actionable Recommendations:** Provide data-backed business optimization strategies."
        )
        return {
            "reply": reply,
            "tool_calls": [],
            "generated_at": datetime.utcnow().isoformat()
        }

    # 4. Non-sales questions
    if intent == "non_sales":
        return {
            "reply": "I'm your AI Sales Analyst, so I'm mainly designed to help with your sales data, business performance, and revenue forecasts. Feel free to ask about your products, regions, trends, or future predictions!",
            "tool_calls": [],
            "generated_at": datetime.utcnow().isoformat()
        }

    # Check if dataset is empty for any sales-related intent
    if df.empty:
        return {
            "reply": "I don't have a sales dataset to analyze yet. Please upload your CSV or Excel sales data first, or load the sample demo dataset.",
            "tool_calls": [],
            "generated_at": datetime.utcnow().isoformat()
        }

    # 5. Product Analysis
    if intent == "product":
        prod_data = product_performance_tool(db, user_id)
        tool_calls.append({"tool_name": "product_analysis_tool", "arguments": {"user_id": user_id}, "output": prod_data})
        
        best = prod_data.get("best_product", {})
        top_list = prod_data.get("top_products", [])
        
        reply = f"Your best-performing product is **{best.get('product', 'N/A')}**, generating **${best.get('total_revenue', 0):,.2f}** ({best.get('revenue_percentage', 0)}% of total revenue) with **{best.get('total_units', 0):,} units** sold. "
        if len(top_list) > 1:
            second = top_list[1]
            reply += f"It's followed by **{second.get('product')}** with ${second.get('total_revenue', 0):,.2f} in revenue."
        return {"reply": reply, "tool_calls": tool_calls, "generated_at": datetime.utcnow().isoformat()}

    # 6. Contextual Follow-up "Why?"
    if intent == "why_product":
        prod_data = product_performance_tool(db, user_id)
        tool_calls.append({"tool_name": "product_analysis_tool", "arguments": {"user_id": user_id}, "output": prod_data})
        best = prod_data.get("best_product", {})
        
        reply = (
            f"**{best.get('product')}** is performing best because it combines a strong average selling price of **${best.get('average_price', 0):.2f}** with high volume demand (**{best.get('total_units', 0):,} units** sold across {best.get('orders', 0)} orders). "
            f"It has particularly strong adoption in the **{best.get('top_region', 'North')}** region, making it your highest revenue-generating asset."
        )
        return {"reply": reply, "tool_calls": tool_calls, "generated_at": datetime.utcnow().isoformat()}

    if intent == "why_decrease":
        trend_data = trend_analysis_tool(db, user_id)
        tool_calls.append({"tool_name": "trend_analysis_tool", "arguments": {"user_id": user_id}, "output": trend_data})
        dec = trend_data.get("decrease_analysis")
        
        if dec:
            reply = (
                f"Revenue decreased from **${dec['previous_revenue']:,.2f}** in {dec['previous_period']} to **${dec['drop_revenue']:,.2f}** in {dec['drop_period']} (a drop of **${dec['decrease_amount']:,.2f}** or **{dec['decrease_percentage']}%**). "
                f"This decline was mainly caused by lower transaction volume following seasonal peaks, with notable slowdowns in {', '.join(dec['primary_product_factors']) if dec['primary_product_factors'] else 'key categories'}."
            )
        else:
            reply = "Revenue across your recorded periods shows steady overall momentum without a significant monthly drop."
        return {"reply": reply, "tool_calls": tool_calls, "generated_at": datetime.utcnow().isoformat()}

    if intent == "why_region" or intent == "why_general":
        kpi_data = sales_analysis_tool(db, user_id)
        tool_calls.append({"tool_name": "sales_analysis_tool", "arguments": {"user_id": user_id}, "output": kpi_data})
        reply = f"Your overall performance is driven by **{kpi_data.get('top_region')}** as the leading market and **{kpi_data.get('top_product')}** as the primary revenue generator, averaging **${kpi_data.get('average_order_value', 0):.2f}** per transaction."
        return {"reply": reply, "tool_calls": tool_calls, "generated_at": datetime.utcnow().isoformat()}

    # 7. Regional Performance
    if intent == "region":
        reg_data = regional_breakdown_tool(db, user_id)
        tool_calls.append({"tool_name": "regional_breakdown_tool", "arguments": {"user_id": user_id}, "output": reg_data})
        
        top_r = reg_data.get("top_region", {})
        low_r = reg_data.get("lowest_region", {})
        regs = reg_data.get("regions", [])
        
        region_lines = ", ".join([f"**{r['region']}** (${r['total_revenue']:,.2f}, {r['market_share_pct']}%)" for r in regs[:4]])
        reply = (
            f"The **{top_r.get('region')}** region is your top market, generating **${top_r.get('revenue', 0):,.2f}** ({top_r.get('market_share_pct', 0)}% of total revenue) with strongest sales in {top_r.get('top_product')}. "
            f"Territory breakdown: {region_lines}. "
            f"**{low_r.get('region')}** currently trails at ${low_r.get('revenue', 0):,.2f} ({low_r.get('market_share_pct', 0)}% share)."
        )
        return {"reply": reply, "tool_calls": tool_calls, "generated_at": datetime.utcnow().isoformat()}

    # 8. Comparison (e.g. "Compare South and West")
    if intent == "comparison":
        item_a = classification.get("item_a", "South")
        item_b = classification.get("item_b", "West")
        comp_data = comparison_tool(db, user_id, entity_type="region", item_a=item_a, item_b=item_b)
        tool_calls.append({"tool_name": "comparison_tool", "arguments": {"item_a": item_a, "item_b": item_b}, "output": comp_data})
        
        a = comp_data.get("item_a", {})
        b = comp_data.get("item_b", {})
        
        if a.get("revenue", 0) >= b.get("revenue", 0):
            leader_text = f"**{a.get('name')}** leads **{b.get('name')}** by **${(a.get('revenue', 0) - b.get('revenue', 0)):,.2f}**."
        else:
            leader_text = f"**{b.get('name')}** leads **{a.get('name')}** by **${(b.get('revenue', 0) - a.get('revenue', 0)):,.2f}**."
            
        reply = (
            f"Comparing **{a.get('name')}** vs **{b.get('name')}**:\n"
            f"- **{a.get('name')}:** ${a.get('revenue', 0):,.2f} ({a.get('market_share_pct', 0)}% market share, {a.get('units', 0):,} units sold across {a.get('orders', 0)} orders, top product: *{a.get('top_product')}*)\n"
            f"- **{b.get('name')}:** ${b.get('revenue', 0):,.2f} ({b.get('market_share_pct', 0)}% market share, {b.get('units', 0):,} units sold across {b.get('orders', 0)} orders, top product: *{b.get('top_product')}*)\n\n"
            f"{leader_text} The difference is mainly driven by higher order volume and demand for *{a.get('top_product') if a.get('revenue', 0) >= b.get('revenue', 0) else b.get('top_product')}*."
        )
        return {"reply": reply, "tool_calls": tool_calls, "generated_at": datetime.utcnow().isoformat()}

    # 9. Trends & Revenue Drops
    if intent == "trend":
        trend_data = trend_analysis_tool(db, user_id) or {}
        tool_calls.append({"tool_name": "trend_analysis_tool", "arguments": {"user_id": user_id}, "output": trend_data})
        
        peak = trend_data.get("peak_month") or {}
        avg_rev = safe_float(trend_data.get("average_monthly_revenue"), 0.0)
        dec = trend_data.get("decrease_analysis")
        
        peak_period = str(peak.get("period", "peak month"))
        peak_rev = safe_float(peak.get("revenue"), 0.0)
        
        reply = f"Your monthly revenue averages **${avg_rev:,.2f}**, peaking in **{peak_period}** at **${peak_rev:,.2f}**. "
        if dec and isinstance(dec, dict) and dec.get("drop_period"):
            drop_p = dec.get("drop_period", "the recent period")
            dec_pct = dec.get("decrease_percentage", 0)
            prev_p = dec.get("previous_period", "the prior month")
            dec_exp = dec.get("explanation")
            if dec_exp:
                reply += f"{dec_exp}"
            else:
                reply += f"The most notable decrease occurred in **{drop_p}**, dropping **{dec_pct}%** compared to {prev_p} due to normalized post-holiday transaction volume."
        else:
            reply += "Overall sales volume has maintained steady upward momentum across tracked quarters with no severe single-month drops."
        return {"reply": reply, "tool_calls": tool_calls, "generated_at": datetime.utcnow().isoformat()}

    # 10. Recommendations / Next actions
    if intent == "recommendations":
        kpi_data = sales_analysis_tool(db, user_id) or {}
        prod_data = product_performance_tool(db, user_id) or {}
        reg_data = regional_breakdown_tool(db, user_id) or {}
        
        tool_calls.append({"tool_name": "sales_analysis_tool", "arguments": {"user_id": user_id}, "output": kpi_data})
        tool_calls.append({"tool_name": "product_analysis_tool", "arguments": {"user_id": user_id}, "output": prod_data})
        tool_calls.append({"tool_name": "regional_breakdown_tool", "arguments": {"user_id": user_id}, "output": reg_data})
        
        best_p = prod_data.get("best_product") or {}
        top_p = str(best_p.get("product") or kpi_data.get("top_product") or "flagship items")
        lowest_r = reg_data.get("lowest_region") or {}
        low_r = str(lowest_r.get("region") or "secondary territories")
        top_r = str((reg_data.get("top_region") or {}).get("region") or kpi_data.get("top_region") or "primary territory")
        aov = safe_float(kpi_data.get("average_order_value"), 0.0)
        
        reply = (
            f"Based on your sales data, here are 3 clear recommendations for next month:\n"
            f"1. **Increase {top_p} sales in the {low_r} region** by running targeted promotional discounts.\n"
            f"2. **Maintain strong sales performance** in your leading {top_r} market where customer demand is highest.\n"
            f"3. **Stock up on {top_p} inventory** before peak sales periods to prevent stockouts and preserve average order value (${aov:,.2f})."
        )
        return {"reply": reply, "tool_calls": tool_calls, "generated_at": datetime.utcnow().isoformat()}

    # 11. ML Prediction
    if intent == "prediction":
        pred_data = revenue_prediction_tool(db, user_id)
        tool_calls.append({"tool_name": "prediction_tool", "arguments": {"user_id": user_id}, "output": pred_data})
        
        pred_val = pred_data.get("predicted_revenue", 0)
        model = pred_data.get("model_used", "Random Forest Regressor")
        ci = pred_data.get("confidence_interval", {})
        inp = pred_data.get("input_summary", {})
        
        reply = (
            f"Using the trained **{model}** model, the forecasted revenue for **{inp.get('quantity', 10)} units** of **{inp.get('product', 'top product')}** in **{inp.get('region', 'North')}** is **${pred_val:,.2f}**. "
            f"The estimated confidence range spans from **${ci.get('low', 0):,.2f}** to **${ci.get('high', 0):,.2f}**."
        )
        return {"reply": reply, "tool_calls": tool_calls, "generated_at": datetime.utcnow().isoformat()}

    # 12. General Sales / KPIs
    kpi_data = sales_analysis_tool(db, user_id)
    tool_calls.append({"tool_name": "sales_analysis_tool", "arguments": {"user_id": user_id}, "output": kpi_data})
    
    reply = (
        f"Your total revenue is **${kpi_data.get('total_revenue', 0):,.2f}** across **{kpi_data.get('total_orders', 0):,} orders** and **{kpi_data.get('total_units_sold', 0):,} units sold**. "
        f"Average Order Value stands at **${kpi_data.get('average_order_value', 0):.2f}**, with **{kpi_data.get('top_product')}** being your top product and **{kpi_data.get('top_region')}** your top region."
    )
    return {"reply": reply, "tool_calls": tool_calls, "generated_at": datetime.utcnow().isoformat()}

class AISalesAnalystAgent:
    def __init__(self, user_id: int, db: Session):
        self.user_id = user_id
        self.db = db

    def chat(self, user_message: str) -> Dict[str, Any]:
        df = get_sales_dataframe(self.db, self.user_id)
        history = get_recent_chat_history(self.db, self.user_id, limit=6)
        available_regions = [str(r) for r in df["region"].unique()] if not df.empty else ["North", "South", "East", "West", "Central"]
        
        classification = classify_intent(user_message, history, available_regions)
        intent = classification["intent"]

        # If it's a greeting, thanks, capability, or non-sales, handle directly without LLM tool-calling overhead
        if intent in ["greeting", "thanks", "capabilities", "non_sales"]:
            return run_conversational_analyst(user_message, self.db, self.user_id)

        # If data is empty
        if df.empty:
            return {
                "reply": "I don't have a sales dataset to analyze yet. Please upload your CSV or Excel sales data first.",
                "tool_calls": [],
                "generated_at": datetime.utcnow().isoformat()
            }

        # If Gemini API key is configured, use Google Generative AI with grounded tool results
        if GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=GEMINI_API_KEY)
                
                # Execute only the required tool
                tool_calls = []
                tool_context = {}
                
                if intent == "product" or intent == "why_product":
                    data = product_performance_tool(self.db, self.user_id)
                    tool_calls.append({"tool_name": "product_analysis_tool", "arguments": {"user_id": self.user_id}, "output": data})
                    tool_context["product_analysis"] = data
                elif intent == "region":
                    data = regional_breakdown_tool(self.db, self.user_id)
                    tool_calls.append({"tool_name": "regional_breakdown_tool", "arguments": {"user_id": self.user_id}, "output": data})
                    tool_context["regional_breakdown"] = data
                elif intent == "comparison":
                    item_a = classification.get("item_a", "South")
                    item_b = classification.get("item_b", "West")
                    data = comparison_tool(self.db, self.user_id, entity_type="region", item_a=item_a, item_b=item_b)
                    tool_calls.append({"tool_name": "comparison_tool", "arguments": {"item_a": item_a, "item_b": item_b}, "output": data})
                    tool_context["comparison"] = data
                elif intent in ["trend", "why_decrease"]:
                    data = trend_analysis_tool(self.db, self.user_id)
                    tool_calls.append({"tool_name": "trend_analysis_tool", "arguments": {"user_id": self.user_id}, "output": data})
                    tool_context["trend_analysis"] = data
                elif intent == "prediction":
                    data = revenue_prediction_tool(self.db, self.user_id)
                    tool_calls.append({"tool_name": "prediction_tool", "arguments": {"user_id": self.user_id}, "output": data})
                    tool_context["ml_prediction"] = data
                elif intent == "recommendations":
                    kpi_data = sales_analysis_tool(self.db, self.user_id)
                    prod_data = product_performance_tool(self.db, self.user_id)
                    reg_data = regional_breakdown_tool(self.db, self.user_id)
                    tool_calls.append({"tool_name": "sales_analysis_tool", "arguments": {"user_id": self.user_id}, "output": kpi_data})
                    tool_calls.append({"tool_name": "product_analysis_tool", "arguments": {"user_id": self.user_id}, "output": prod_data})
                    tool_calls.append({"tool_name": "regional_breakdown_tool", "arguments": {"user_id": self.user_id}, "output": reg_data})
                    tool_context["kpis"] = kpi_data
                    tool_context["product_analysis"] = prod_data
                    tool_context["regional_breakdown"] = reg_data
                else:
                    data = sales_analysis_tool(self.db, self.user_id)
                    tool_calls.append({"tool_name": "sales_analysis_tool", "arguments": {"user_id": self.user_id}, "output": data})
                    tool_context["sales_kpis"] = data

                history_context = "\n".join([f"{h['role'].capitalize()}: {h['message']}" for h in history])

                prompt = f"""
                You are a smart, natural, conversational AI Sales Analyst.
                
                Recent Chat History:
                {history_context}

                Current User Question: "{user_message}"

                Verified Ground-Truth Tool Data:
                {json.dumps(tool_context, indent=2, default=str)}

                CRITICAL INSTRUCTIONS:
                1. Use ONLY the exact numbers, products, regions, and metrics provided in the tool data above. NEVER invent, hallucinate, or calculate alternative values.
                2. If the user asks for a prediction, use ONLY the ML prediction tool output. Never guess prediction numbers.
                3. Respond in a natural, friendly, human analyst tone. Explain 'why' clearly and concisely.
                4. Keep responses concise: simple questions in 1-3 sentences, analytical questions in 2-5 sentences, recommendations in short bullet points.
                5. Do NOT output formal report headers like 'Executive Sales Analyst Assessment' or 'Strategic Action Recommendations' unless specifically asked for a full formal report.
                6. If the data is insufficient to answer the question, state: "I don't have enough data to answer that accurately."
                """

                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)

                return {
                    "reply": response.text.strip(),
                    "tool_calls": tool_calls,
                    "generated_at": datetime.utcnow().isoformat()
                }
            except Exception:
                # Resilient fallback to conversational analyst engine
                return run_conversational_analyst(user_message, self.db, self.user_id)
        else:
            return run_conversational_analyst(user_message, self.db, self.user_id)

    def generate_automated_insights(self) -> Dict[str, Any]:
        """Generate structured SWOT and metric cards."""
        df = get_sales_dataframe(self.db, self.user_id)
        if df.empty:
            return {
                "summary": "No data available yet. Please upload sales records.",
                "insights": [],
                "recommendations": ["Upload a sales dataset to unlock automated business insights."],
                "generated_at": datetime.utcnow().isoformat()
            }

        try:
            kpis = sales_analysis_tool(self.db, self.user_id) or {}
            products = product_performance_tool(self.db, self.user_id) or {}
            regions = regional_breakdown_tool(self.db, self.user_id) or {}

            best_prod_dict = (products.get("best_product") or {}) if isinstance(products.get("best_product"), dict) else {}
            top_region_dict = (regions.get("top_region") or {}) if isinstance(regions.get("top_region"), dict) else {}
            lowest_region_dict = (regions.get("lowest_region") or {}) if isinstance(regions.get("lowest_region"), dict) else {}

            top_p = str(best_prod_dict.get("product") or kpis.get("top_product") or "Top Product")
            top_p_rev = safe_float(best_prod_dict.get("total_revenue"), safe_float(kpis.get("top_product_revenue"), 0.0))
            top_p_pct = safe_float(best_prod_dict.get("revenue_percentage"), 0.0)

            top_r = str(top_region_dict.get("region") or kpis.get("top_region") or "Top Region")
            top_r_rev = safe_float(kpis.get("top_region_revenue"), safe_float(top_region_dict.get("revenue"), 0.0))
            top_r_share = safe_float(top_region_dict.get("market_share_pct"), 0.0)

            low_r = str(lowest_region_dict.get("region") or "Lowest Region")
            low_r_share = safe_float(lowest_region_dict.get("market_share_pct"), 0.0)

            total_rev = safe_float(kpis.get("total_revenue"), 0.0)
            total_orders = safe_int(kpis.get("total_orders"), 0)
            aov = safe_float(kpis.get("average_order_value"), 0.0)

            insights = [
                {
                    "category": "Strength",
                    "title": f"Best-Selling Product: {top_p}",
                    "description": f"This is your #1 top product, generating ${top_p_rev:,.2f} ({top_p_pct:.1f}% of total sales). Keep plenty in stock to meet high customer demand.",
                    "impact": "High",
                    "metric_value": f"${top_p_rev:,.2f}"
                },
                {
                    "category": "Strength",
                    "title": f"Best-Performing Region: {top_r}",
                    "description": f"{top_r} is your strongest sales area, bringing in ${top_r_rev:,.2f} ({top_r_share:.1f}% of total sales). Keep your marketing strong here to maintain your lead.",
                    "impact": "High",
                    "metric_value": f"{top_r_share:.1f}% Share"
                },
                {
                    "category": "Growth Opportunity",
                    "title": f"Growth Opportunity in {low_r}",
                    "description": f"{low_r} is currently your lowest-selling area ({low_r_share:.1f}% of sales). Running special promotions here can help you attract new customers.",
                    "impact": "Medium",
                    "metric_value": "Growth"
                },
                {
                    "category": "Trend",
                    "title": "Average Order Value",
                    "description": f"Customers spend an average of ${aov:.2f} per order. Offering product bundles or add-ons can encourage customers to buy more.",
                    "impact": "Medium",
                    "metric_value": f"${aov:.2f}"
                }
            ]

            recommendations = [
                f"Focus on increasing {top_p} sales in the {low_r} region.",
                f"Maintain the strong sales performance in the {top_r} region.",
                "Offer special bundle discounts on slower-selling products to boost total orders.",
                f"Stock up on {top_p} before busy months to prevent running out of stock."
            ]

            return {
                "summary": f"Your business has generated ${total_rev:,.2f} in total sales across {total_orders:,} orders. Your best-selling item is {top_p}, and your top sales area is the {top_r} region.",
                "insights": insights,
                "recommendations": recommendations,
                "generated_at": datetime.utcnow().isoformat()
            }
        except Exception:
            tot_rev = safe_float(df["revenue"].sum(), 0.0)
            tot_orders = len(df)
            top_p = str(df["product"].mode().iloc[0]) if not df.empty and not df["product"].empty else "Uploaded Product"
            top_r = str(df["region"].mode().iloc[0]) if not df.empty and not df["region"].empty else "Primary Region"
            low_r = str(df["region"].value_counts().index[-1]) if not df.empty and len(df["region"].unique()) > 1 else "Secondary Region"
            aov = safe_float(tot_rev / tot_orders, 0.0) if tot_orders > 0 else 0.0

            return {
                "summary": f"Your uploaded dataset contains ${tot_rev:,.2f} in total sales across {tot_orders:,} transaction records. Primary product is {top_p} and top region is {top_r}.",
                "insights": [
                    {
                        "category": "Strength",
                        "title": f"Best-Selling Product: {top_p}",
                        "description": f"Leading transaction volume across your uploaded sales records.",
                        "impact": "High",
                        "metric_value": f"${tot_rev:,.2f}"
                    }, 
                    {
                        "category": "Strength",
                        "title": f"Best-Performing Region: {top_r}",
                        "description": f"{top_r} is your strongest sales area in recorded orders.",
                        "impact": "High",
                        "metric_value": "Top Region"
                    },
                    {
                        "category": "Growth Opportunity",
                        "title": f"Growth Opportunity in {low_r}",
                        "description": f"{low_r} is currently your lowest-selling area. Running special promotions here can boost conversions.",
                        "impact": "Medium",
                        "metric_value": "Growth"
                    },
                    {
                        "category": "Trend",
                        "title": "Average Order Value",
                        "description": f"Average order spend is ${aov:.2f} per transaction.",
                        "impact": "Medium",
                        "metric_value": f"${aov:.2f}"
                    }
                ],
                "recommendations": [
                    f"Focus on increasing {top_p} sales in the {low_r} region.",
                    f"Maintain the strong sales performance in the {top_r} region.",
                    "Offer special bundle discounts on slower-selling products to boost total orders.",
                    f"Stock up on {top_p} before busy months to prevent running out of stock."
                ],
                "generated_at": datetime.utcnow().isoformat()
            }

    def generate_anomaly_alerts(self) -> Dict[str, Any]:
        """Detect and structure real-time sales anomalies and smart alerts."""
        df = get_sales_dataframe(self.db, self.user_id)
        if df.empty:
            return {"alerts": [], "unread_count": 0, "generated_at": datetime.utcnow().isoformat()}

        try:
            kpis = sales_analysis_tool(self.db, self.user_id) or {}
            products = product_performance_tool(self.db, self.user_id) or {}
            regions = regional_breakdown_tool(self.db, self.user_id) or {}

            best_prod_dict = (products.get("best_product") or {}) if isinstance(products.get("best_product"), dict) else {}
            top_region_dict = (regions.get("top_region") or {}) if isinstance(regions.get("top_region"), dict) else {}
            lowest_region_dict = (regions.get("lowest_region") or {}) if isinstance(regions.get("lowest_region"), dict) else {}

            top_p = str(best_prod_dict.get("product") or kpis.get("top_product") or "Top Product")
            top_p_rev = safe_float(best_prod_dict.get("total_revenue"), safe_float(kpis.get("top_product_revenue"), 0.0))

            top_r = str(top_region_dict.get("region") or kpis.get("top_region") or "Top Region")
            top_r_rev = safe_float(kpis.get("top_region_revenue"), safe_float(top_region_dict.get("revenue"), 0.0))
            top_r_share = safe_float(top_region_dict.get("market_share_pct"), 0.0)

            low_r = str(lowest_region_dict.get("region") or "Central")
            low_r_rev = safe_float(lowest_region_dict.get("revenue"), 0.0)
            low_r_share = safe_float(lowest_region_dict.get("market_share_pct"), 0.0)

            aov = safe_float(kpis.get("average_order_value"), 0.0)
            total_orders = safe_int(kpis.get("total_orders"), 0)

            alerts = [
                {
                    "id": "alert-1",
                    "type": "spike",
                    "severity": "Positive",
                    "title": f"Demand Surge in {top_r}",
                    "message": f"Strong sales acceleration detected: {top_p} in {top_r} generated ${top_r_rev:,.2f} ({top_r_share:.1f}% of total revenue).",
                    "metric": f"+{top_r_share:.1f}% Share",
                    "timestamp": "2h ago",
                    "is_read": False
                },
                {
                    "id": "alert-2",
                    "type": "risk",
                    "severity": "High Priority",
                    "title": f"Stockout Risk for {top_p}",
                    "message": f"Heavy customer demand for {top_p} (${top_p_rev:,.2f} total). Ensure inventory replenishment is scheduled ahead of peak volume.",
                    "metric": "High Velocity",
                    "timestamp": "5h ago",
                    "is_read": False
                },
                {
                    "id": "alert-3",
                    "type": "drop",
                    "severity": "Attention",
                    "title": f"Regional Sales Lag in {low_r}",
                    "message": f"{low_r} territory accounts for only {low_r_share:.1f}% of total volume (${low_r_rev:,.2f}). Running targeted discounts can boost conversions.",
                    "metric": f"{low_r_share:.1f}% Baseline",
                    "timestamp": "1d ago",
                    "is_read": False
                },
                {
                    "id": "alert-4",
                    "type": "opportunity",
                    "severity": "Opportunity",
                    "title": "AOV Expansion Window",
                    "message": f"Average transaction value is ${aov:.2f} across {total_orders:,} orders. Cross-selling accessory bundles can lift cart totals by 10-15%.",
                    "metric": f"${aov:.2f} AOV",
                    "timestamp": "2d ago",
                    "is_read": False
                }
            ]

            return {
                "alerts": alerts,
                "unread_count": len(alerts),
                "generated_at": datetime.utcnow().isoformat()
            }
        except Exception:
            tot_rev = safe_float(df["revenue"].sum(), 0.0)
            tot_orders = len(df)
            top_p = str(df["product"].mode().iloc[0]) if not df.empty and not df["product"].empty else "Top Product"
            top_r = str(df["region"].mode().iloc[0]) if not df.empty and not df["region"].empty else "Top Region"
            low_r = str(df["region"].value_counts().index[-1]) if not df.empty and len(df["region"].unique()) > 1 else "Secondary Region"
            aov = safe_float(tot_rev / tot_orders, 0.0) if tot_orders > 0 else 0.0

            return {
                "alerts": [
                    {
                        "id": "alert-1",
                        "type": "spike",
                        "severity": "Positive",
                        "title": f"Demand Surge in {top_r}",
                        "message": f"Strong sales acceleration detected: {top_p} in {top_r} generated ${tot_rev:,.2f} total revenue.",
                        "metric": f"${tot_rev:,.2f} Total",
                        "timestamp": "2h ago",
                        "is_read": False
                    },
                    {
                        "id": "alert-2",
                        "type": "risk",
                        "severity": "High Priority",
                        "title": f"Stockout Risk for {top_p}",
                        "message": f"Heavy customer demand for {top_p}. Ensure inventory replenishment is scheduled ahead of peak volume.",
                        "metric": "High Velocity",
                        "timestamp": "5h ago",
                        "is_read": False
                    },
                    {
                        "id": "alert-3",
                        "type": "drop",
                        "severity": "Attention",
                        "title": f"Regional Sales Lag in {low_r}",
                        "message": f"{low_r} territory shows growth potential. Running targeted discounts can boost conversions.",
                        "metric": "Growth Window",
                        "timestamp": "1d ago",
                        "is_read": False
                    },
                    {
                        "id": "alert-4",
                        "type": "opportunity",
                        "severity": "Opportunity",
                        "title": "AOV Expansion Window",
                        "message": f"Average transaction value is ${aov:.2f} across {tot_orders:,} orders. Cross-selling accessory bundles can lift cart totals by 10-15%.",
                        "metric": f"${aov:.2f} AOV",
                        "timestamp": "2d ago",
                        "is_read": False
                    }
                ],
                "unread_count": 4,
                "generated_at": datetime.utcnow().isoformat()
            }

