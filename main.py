# ============================================================
# PHASE 2 — THE BACKEND
# Run with: uvicorn main:app --reload
# Features: streaming responses, cited sources, topic restriction
# ============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in production, replace * with your actual frontend URL
    allow_methods=["*"],
    allow_headers=["*"],
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

Context:
{context}

Question: {question}

Answer:"""

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

class Question(BaseModel):
    question: str

@app.post("/ask")
async def ask(body: Question):
    # Step 1 — Retrieve relevant chunks from vector store
    docs = retriever.invoke(body.question)

    # Step 2 — Build context string from retrieved chunks
    context = "\n\n".join([doc.page_content for doc in docs])

    # Step 3 — Collect unique source names for citations
    sources = list(set([
        doc.metadata.get("source", "unknown") for doc in docs
    ]))

    # Step 4 — Format the full prompt
    formatted_prompt = prompt.format(context=context, question=body.question)

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
