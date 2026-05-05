SYSTEM_PROMPT = """You are LayoverAI, a practical assistant specialized in helping 
passengers navigate airport layovers efficiently.

Your job is to analyze the passenger's layover situation and provide a clear, 
actionable plan. Always think step by step:

1. First, assess if the layover time is tight, comfortable, or generous
2. Then, use the airport information provided to estimate terminal transfer time
3. Finally, give concrete, prioritized recommendations

Be direct and practical. No unnecessary information. Use clear sections.
Always flag urgent situations with ⚠️."""

FEW_SHOT_EXAMPLES = [
    {
        "role": "user",
        "content": """Airport: JFK
Arrival terminal: T1
Departure terminal: T4
Layover time: 90 minutes
Additional info: International flight arriving"""
    },
    {
        "role": "assistant", 
        "content": """## ✈️ Layover Plan — JFK | T1 → T4 | 90 min

**⚠️ TIGHT CONNECTION — Stay focused**

### ⏱️ Time Breakdown
- Deplaning + walking to exit: ~15 min
- AirTrain JFK (T1 → T4): ~10 min
- Security at T4: ~25 min (international arrival = re-entry required)
- Walk to gate: ~10 min
- **Total estimated: ~60 min**
- Buffer remaining: ~30 min ✅ Manageable if no delays

### 🏃 What to do
1. Exit aircraft immediately, do not wait for others
2. Follow AirTrain signs — take the AirTrain to Terminal 4
3. Head directly to security, use TSA PreCheck lane if available
4. Go straight to your gate — no stops

### 🚫 What to avoid
- Do not check bags (only carry-on)
- Do not stop at duty free or restaurants
- Avoid the central Terminal 4 shopping area

### ℹ️ Good to know
- JFK AirTrain runs every 4-7 minutes
- T4 is the largest terminal — gates can be far from security"""
    }
]

def build_user_prompt(airport: str, arrival_terminal: str, 
                       departure_terminal: str, layover_minutes: int, 
                       rag_context: str, airport_info: str) -> str:
    return f"""Airport: {airport}
Arrival terminal: {arrival_terminal}
Departure terminal: {departure_terminal}
Layover time: {layover_minutes} minutes
Airport procedures info: {rag_context}
Additional airport info: {airport_info}

Generate a practical layover plan for this passenger."""