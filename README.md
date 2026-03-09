# Rondeau & Co. RAG Assistant

A complete Retrieval-Augmented Generation (RAG) chatbot and frontend for a premium restaurant experience.

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=FastAPI&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-121212?style=for-the-badge&logo=chainlink&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)

## Overview

This project implements a Retrieval-Augmented Generation (RAG) system utilizing **FastAPI**, **LangChain**, and **OpenRouter** to power an intelligent interactive assistant on an upscale restaurant's custom-built website (HTML/CSS/JS). The system ingests authentic restaurant documentation (menus, FAQs, special events) to formulate grounded, concise, and domain-specific answers for customers.

## Features
- **Knowledge Base Retrieval**: Accurately queries specific menu items, private event details, and restaurant FAQs from provided source PDFs.
- **Streaming LLM Responses**: Streams token responses back to the frontend in real-time via Server-Sent Events (SSE).
- **Topic Restraint**: Enforces guardrails so the assistant exclusively answers questions related to Rondeau & Co., handling off-topic queries gracefully.
- **Separated Tech Stack**: Distinct frontend and backend layers with clear separation of responsibilities. 

## Project Structure

```
.
├── backend/            # FastAPI server & RAG logic
│   ├── main.py         # Primary API and endpoint setup
│   ├── ingest.py       # Script to embed and ingest PDF documentation
│   ├── requirements.txt# Backend dependencies
│   └── .env            # Environment variables (API keys, settings)
├── frontend/           # Static HTML/CSS/JS assets
│   ├── index.html      # Primary landing page and web application
│   ├── styles.css      # Vanilla CSS styling
│   ├── script.js       # UI interactions
│   └── chat.js         # Chatbot communication logic
├── data/               # Source PDF files used for the knowledge base
├── docs/               # Source Markdown files
├── tests/              # Sandbox files and experimental scripts
└── vector_store/       # FAISS database for generated embeddings
```

## Setup & Run Instructions

### 1. Backend Setup

From the root directory, navigate to the `/backend` folder and install dependencies:

```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

Ensure you have your `.env` configured inside the `/backend` directory:

```env
OPENROUTER_API_KEY=your_api_key_here
VECTOR_STORE_PATH=../vector_store
ALLOWED_ORIGINS=http://localhost:5500, http://127.0.0.1:5500
```

> **Note**: To build the vector store (if you add new data), run `python ingest.py` inside the backend directory.

Start the FastAPI application:

```bash
uvicorn main:app --reload
```

### 2. Frontend Setup

The frontend depends exclusively on HTML, CSS, and JS. All you need is a local development server! 

- If using **VS Code**, right-click `frontend/index.html` and select **Open with Live Server**.
- Alternatively, you can run Python's built-in HTTP server:

```bash
cd frontend
python -m http.server 5500
```

Open your browser to `http://localhost:5500` to view the beautiful landing page and test the embedded Chatbot!
