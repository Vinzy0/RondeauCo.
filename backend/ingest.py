# ============================================================
# PHASE 1 — INGEST YOUR PDFS
# Run this ONCE whenever you add or update your PDF files.
# It processes your PDFs and saves a searchable vector store.
# ============================================================

from pypdf import PdfReader
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import os

# ---- CHANGE THIS ----
PDF_FILES = [
    "../data/01-dinner-menu.pdf",
    "../data/02-faq.pdf",
    "../data/03-about.pdf",
    "../data/04-wine-and-cocktails.pdf",
    "../data/05-private-dining-and-events.pdf",
    "../data/06-seasonal-specials.pdf",
]
VECTOR_STORE_PATH = "../vector_store"
# ----------------------

def ingest():
    all_chunks = []

    for pdf_path in PDF_FILES:
        if not os.path.exists(pdf_path):
            print(f"  ⚠ Skipping {pdf_path} — file not found")
            continue

        print(f"Loading {pdf_path}...")
        reader = PdfReader(pdf_path)
        pages = [
            Document(
                page_content=page.extract_text() or "",
                metadata={"page": i, "source": pdf_path}
            )
            for i, page in enumerate(reader.pages)
        ]

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=600,    # slightly larger for richer context per chunk
            chunk_overlap=100, # more overlap so context isn't lost at borders
            separators=["\n\n", "\n", ".", " ", ""] # tries to split on natural breaks first
        )
        chunks = splitter.split_documents(pages)

        # ---- METADATA TAGGING ----
        # Tag every chunk with a clean source name so citations work in main.py
        source_name = os.path.splitext(os.path.basename(pdf_path))[0]  # e.g. "menu"
        for chunk in chunks:
            chunk.metadata["source"] = source_name
            chunk.metadata["file_path"] = pdf_path

        all_chunks.extend(chunks)
        print(f"  → {len(chunks)} chunks from {source_name}")

    if not all_chunks:
        print("\n❌ No chunks created. Make sure your PDFs are in the /data folder.")
        return

    print(f"\nConverting {len(all_chunks)} chunks to vectors...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_store = FAISS.from_documents(all_chunks, embeddings)
    vector_store.save_local(VECTOR_STORE_PATH)

    print(f"\n✅ Done! Vector store saved to '{VECTOR_STORE_PATH}'")
    print(f"Total chunks indexed: {len(all_chunks)}")

if __name__ == "__main__":
    ingest()
