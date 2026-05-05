import os
import json
import io

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from fastapi.responses import FileResponse, StreamingResponse
from pdf_report import generate_report

from weather import get_airport_info, AIRPORT_INFO_FUNCTION
from rag import get_vectorstore, query_airport_procedures
from prompts import SYSTEM_PROMPT, FEW_SHOT_EXAMPLES, build_user_prompt

load_dotenv()

app = FastAPI(title="LayoverAI API")

# Serve frontend folder
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

# Load vectorstore once at startup
vectorstore = None

@app.on_event("startup")
async def startup_event():
    global vectorstore
    print("Loading vectorstore...")
    vectorstore = get_vectorstore()
    print("Vectorstore ready.")


@app.get("/")
async def serve_frontend():
    return FileResponse("../frontend/index.html")


class LayoverRequest(BaseModel):
    airport: str
    arrival_terminal: str
    departure_terminal: str
    layover_minutes: int
    icao_code: str


@app.post("/api/layover")
async def get_layover_plan(request: LayoverRequest):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Step 1 — RAG: get airport procedures from ChromaDB
    rag_context = query_airport_procedures(
        vectorstore=vectorstore,
        airport=request.airport,
        query=f"terminal transfer procedures security {request.arrival_terminal} {request.departure_terminal}"
    )

    # Step 2 — Build messages with few-shot examples
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *FEW_SHOT_EXAMPLES,
        {
            "role": "user",
            "content": build_user_prompt(
                airport=request.airport,
                arrival_terminal=request.arrival_terminal,
                departure_terminal=request.departure_terminal,
                layover_minutes=request.layover_minutes,
                rag_context=rag_context,
                airport_info="Fetching live data..."
            )
        }
    ]

    # Step 3 — First API call with function calling enabled (U4)
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=[AIRPORT_INFO_FUNCTION],
            tool_choice="auto"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")

    response_message = response.choices[0].message

    # Step 4 — Handle function calling if GPT decided to use it
    if response_message.tool_calls:
        tool_call = response_message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
        airport_data = get_airport_info(args["icao_code"])

        # Must convert to dict before appending
        messages.append({
            "role": "assistant",
            "tool_calls": [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                }
            ]
        })
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(airport_data)
        })

        # Step 5 — Second API call with real airport data
        try:
            final_response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )
            plan = final_response.choices[0].message.content
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"OpenAI API error on second call: {str(e)}"
            )
    else:
        plan = response_message.content

    return {"plan": plan}

class ReportRequest(BaseModel):
    airport: str
    arrival_terminal: str
    departure_terminal: str
    layover_minutes: int
    plan: str

@app.post("/api/report")
async def download_report(request: ReportRequest):
    pdf_bytes = generate_report(
        airport=request.airport,
        arrival=request.arrival_terminal,
        departure=request.departure_terminal,
        layover=request.layover_minutes,
        plan_text=request.plan
    )
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=layover-{request.airport}.pdf"}
    )


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "vectorstore_loaded": vectorstore is not None
    }