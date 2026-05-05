# LayoverAI

LayoverAI is a web application that generates practical, AI-powered layover plans for airport passengers. Given a layover airport, arrival terminal, departure terminal, and available time between flights, the system produces a structured action plan enriched with real-time weather data and airport-specific procedural context retrieved from official documentation.

---

## Course Units Applied

| Unit | Description |
|------|-------------|
| U1 - Generative AI & LLMs | GPT-4o is used to generate the layover plan. The model was selected for its instruction-following capability, reliable structured markdown output, and native function calling support. |
| U2 - Prompt Engineering | A role-specific system prompt defines the LayoverAI assistant behavior. Few-shot examples guide the output structure. Chain-of-thought reasoning is enforced by prompting the model to assess urgency, estimate transfer time, and prioritize recommendations in sequence. |
| U3 - Transformers & APIs | The OpenAI Python SDK handles all API communication. The endpoint flow includes two sequential calls: an initial call with function calling enabled, and a second call that incorporates the live weather result. Error handling is implemented at both stages. |
| U4 - Agents & Automation | Function calling allows GPT-4o to autonomously decide when to invoke the `get_airport_info` tool, which queries the aviationweather.gov API for real-time METAR data for the layover airport. |
| U5 - RAG & Vector Databases | Airport procedure PDFs are ingested, split into chunks, embedded using `text-embedding-3-small`, and stored in ChromaDB. At inference time, a semantic search retrieves the most relevant chunks for the queried airport and terminals, which are injected into the prompt as context. |

---

## Architecture

```
User Input (Browser)
        |
        v
FastAPI Backend  (src/main.py)
        |
        |-- RAG Query --------> ChromaDB
        |                       (airport procedure chunks)
        |
        |-- Prompt Builder ----> prompts.py
        |                       (system prompt + few-shot + RAG context)
        |
        |-- OpenAI API Call 1 -> GPT-4o
        |         |              function calling enabled
        |         |
        |         v
        |   get_airport_info() -> aviationweather.gov (METAR)
        |
        |-- OpenAI API Call 2 -> GPT-4o
        |                       with weather data injected
        |
        v
   Layover Plan (JSON response)
        |
        v
   Frontend (frontend/index.html)
        |
        v
   PDF Report (src/pdf_report.py via /api/report)
```

---

## Technologies Used

- Python 3.12
- FastAPI — REST API backend and static file serving
- OpenAI Python SDK — GPT-4o completions and function calling
- LangChain + ChromaDB — document ingestion, embedding, and semantic retrieval
- ReportLab — server-side PDF generation
- HTML, CSS, JavaScript — single-file frontend with no external framework
- aviationweather.gov — free official FAA API for real-time METAR data, no authentication required

---

## Installation and Configuration

**1. Clone the repository**

```bash
git clone https://github.com/Aryyaann/LayoverAI.git
cd LayoverAI
```

**2. Create and activate a virtual environment**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure environment variables**

```bash
cp .env.example .env
```

Open `.env` and set your OpenAI API key:

```
OPENAI_API_KEY=sk-...
```

**5. Add airport procedure PDFs**

Download airport diagram PDFs from the FAA and place them in the `docs/` folder. The filenames must match the airport IATA code:

```
docs/JFK.pdf
docs/LAX.pdf
docs/MIA.pdf
docs/ORD.pdf
```

FAA airport diagrams are available at:
https://www.faa.gov/air_traffic/flight_info/aeronav/digital_products/dtpp/

Note: FAA PDF URLs rotate every 28 days following the AIRAC cycle. If a direct link returns 404, navigate to the FAA digital products page and search by airport identifier.

**6. Start the server**

```bash
cd src
uvicorn main:app --reload
```

**7. Open the application**

Navigate to http://127.0.0.1:8000 in your browser.

---

## Usage

1. Select a layover airport from the dropdown list (15 major airports available).
2. The ICAO code is auto-filled based on the selected airport.
3. Select the arrival terminal from the filtered list.
4. Select the departure terminal from the filtered list.
5. Set the available layover time using the slider.
6. Click **Generate Layover Plan**.
7. The plan is rendered in the right panel with a structured breakdown.
8. Click **Download Report** to export the plan as a PDF.

**Example input:** JFK — Terminal 1 to Terminal 4 — 90 minutes

---

## Screenshots

![Main interface with form filled](docs/screenshots/screenshot_1.png)
*Main interface showing airport selection and layover configuration.*

![Generated layover plan](docs/screenshots/screenshot_2.png)
*Layover plan generated by GPT-4o with time breakdown and recommendations.*

![Downloaded PDF report](docs/screenshots/screenshot_3.png)
*PDF report exported from the application.*

---

## Technical Decisions

**Model selection: GPT-4o**
GPT-4o was selected over alternatives such as GPT-3.5-turbo and Claude due to its superior instruction-following behavior with structured prompts, native support for function calling, and consistent markdown formatting in outputs. The higher cost per token is justified by the quality and reliability of the generated plans.

**Vector store: ChromaDB**
ChromaDB was chosen because it runs locally without any external service or infrastructure, integrates natively with LangChain, and is well-suited to the document volume of this project. It eliminates the need for a managed vector database service while fully demonstrating the RAG pipeline.

**Weather API: aviationweather.gov**
The FAA Aviation Weather Center API was selected because it is free, requires no authentication, returns structured JSON METAR data, and is an authoritative source for real airport conditions. The endpoint fits cleanly into the OpenAI function calling schema.

**Key parameters**

| Parameter | Value |
|-----------|-------|
| Embedding model | text-embedding-3-small |
| Chunk size | 500 tokens |
| Chunk overlap | 50 tokens |
| RAG top-k retrieval | 4 chunks |
| GPT-4o temperature | default (1.0) |

**Difficulties encountered**

LangChain changed the import path for `RecursiveCharacterTextSplitter` in recent versions, requiring the use of `langchain_text_splitters` as a separate package. The OpenAI function calling flow requires the assistant message to be serialized as a plain dictionary before being appended to the message history, as passing the SDK object directly causes a 400 error on the second API call. FAA PDF URLs rotate on a 28-day AIRAC cycle, which means direct links become invalid and must be refreshed periodically.

---

## Possible Improvements

1. **Flight delay integration** — connect to a live flight status API such as AviationStack or FlightAware to detect whether the incoming flight is delayed and automatically recalculate the effective layover time before generating the plan.

2. **Airport coverage expansion** — the current version supports 15 airports. Expanding the PDF document base and the frontend airport list to cover the top 100 global hubs would significantly increase the practical utility of the application.

---

## Author

Aryan Haresh Narwani Daswani
Machine Learning 2 — U-tad
