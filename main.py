# ============================================================
# PHASE 2 — THE BACKEND
# Run with: uvicorn main:app --reload
# Features: streaming responses, cited sources, topic restriction
# ============================================================

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
import json
import os
from typing import List, Optional
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

load_dotenv()

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# SECURITY: Restrict CORS to your frontend's actual URL
ALLOWED_ORIGINS = [
    "http://localhost:5500",  # VS Code Live Server
    "http://127.0.0.1:5500",
    "http://localhost:3000",  # Common React/Vite port
    "http://localhost:8000",
    # "https://your-production-domain.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"], # Only allow necessary methods
    allow_headers=["Content-Type"], # Only allow necessary headers
)

# ---- CHANGE THESE ----
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
VECTOR_STORE_PATH = os.getenv("VECTOR_STORE_PATH")

SYSTEM_PROMPT = """You are a warm, knowledgeable assistant for Rondeau & Co., an upscale live-fire American grill restaurant in Nashville, TN.

Answer questions ONLY using the context provided below.
- If the answer is not in the context, say: "I don't have that information — please contact us directly at info@rondeauandco.com or call (615) 000-0000."
- If asked anything unrelated to the restaurant (e.g. general knowledge, other restaurants, coding), politely say: "I'm only able to help with questions about Rondeau & Co. Is there anything about our menu, reservations, or events I can help with?"
- Keep answers concise, warm, and on-brand for a fine dining experience.
- Never make up information that isn't in the context.

Chat History:
{chat_history}

Context:
{context}

Question: {question}

Answer:"""

# This prompt turns "yes" into "The user wants to book Thursday at 9pm"
CONDENSE_PROMPT = """Given the following chat history and a follow-up question, rephrase the follow-up question to be a standalone question.
Chat History:
{chat_history}
Follow-up Question: {question}
Standalone Question:"""

MODEL = "meta-llama/llama-3.1-8b-instruct"  # Removed :free suffix to fix 404
# ----------------------

# Load vector store once when server starts
print("Loading vector store...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_store = FAISS.load_local(VECTOR_STORE_PATH, embeddings, allow_dangerous_deserialization=True)
retriever = vector_store.as_retriever(search_kwargs={"k": 4})  # retrieve top 4 chunks
print("✅ Vector store loaded!")

# LLM with streaming enabled
llm = ChatOpenAI(
    model=MODEL,
    openai_api_key=OPENROUTER_API_KEY,
    openai_api_base="https://openrouter.ai/api/v1",
    streaming=True,
    temperature=0.3,  # lower = more factual, less creative
)

prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=SYSTEM_PROMPT,
)

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class Question(BaseModel):
    question: str
    history: List[ChatMessage] = []

    # Simple input validation
    def validate_input(self):
        if not self.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        if len(self.question) > 500:
            raise HTTPException(status_code=400, detail="Question too long (max 500 characters)")
        return self

@app.post("/ask")
@limiter.limit("5/minute")
async def ask(request: Request, body: Question):
    # Validate input
    body.validate_input()
    # Step 0 — Prepare Chat History string
    history_str = "\n".join([f"{m.role}: {m.content}" for m in body.history])
    
    # Step 1 — Rewrite the question if history exists (Contextualization)
    search_query = body.question
    if body.history:
        condense_input = CONDENSE_PROMPT.format(chat_history=history_str, question=body.question)
        # We do a quick non-streaming call to rephrase the question
        res = llm.invoke(condense_input)
        search_query = res.content
        print(f"DEBUG: Original: {body.question} -> Search Query: {search_query}")

    # Step 2 — Retrieve relevant chunks based on updated query
    docs = retriever.invoke(search_query)

    # Step 2 — Build context string from retrieved chunks
    context = "\n\n".join([doc.page_content for doc in docs])

    # Step 3 — Collect unique source names for citations
    sources = list(set([
        doc.metadata.get("source", "unknown") for doc in docs
    ]))

    # Step 5 — Format the full prompt with History + Context
    formatted_prompt = prompt.format(
        chat_history=history_str if history_str else "No previous conversation.",
        context=context, 
        question=body.question
    )

    # Step 5 — Stream response back to frontend via SSE
    async def generate():
        # Send sources first so the frontend can display them immediately
        yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"

        # Stream tokens one by one
        async for chunk in llm.astream(formatted_prompt):
            token = chunk.content
            if token:
                yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"

        # Signal stream is complete
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

@app.get("/")
def root():
    return {"status": "✅ Rondeau & Co. RAG backend is running"}
