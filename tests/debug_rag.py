import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()

VECTOR_STORE_PATH = os.getenv("VECTOR_STORE_PATH", "vector_store")

def debug_rag():
    print("DEBUG: Checking if vector_store path exists...")
    if not os.path.exists(VECTOR_STORE_PATH):
        print(f"❌ Path {VECTOR_STORE_PATH} does not exist!")
        return

    print("DEBUG: Loading embeddings (this might take a while if downloading)...")
    try:
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    except Exception as e:
        print(f"❌ Failed to load embeddings: {str(e)}")
        return

    print("DEBUG: Loading vector store...")
    try:
        vector_store = FAISS.load_local(VECTOR_STORE_PATH, embeddings, allow_dangerous_deserialization=True)
    except Exception as e:
        print(f"❌ Failed to load FAISS: {str(e)}")
        return

    print("DEBUG: Testing retrieval...")
    retriever = vector_store.as_retriever(search_kwargs={"k": 2})
    
    question = "What is on the menu?"
    print(f"DEBUG: Searching for: '{question}'")
    docs = retriever.invoke(question)
    
    print(f"DEBUG: Found {len(docs)} documents.")
    for i, doc in enumerate(docs):
        print(f"\nDocument {i+1} (Source: {doc.metadata.get('source')}):")
        print(doc.page_content[:200] + "...")

if __name__ == "__main__":
    debug_rag()
