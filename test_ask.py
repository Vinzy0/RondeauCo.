import requests
import json

# ============================================================
# SIMPLE TEST SCRIPT FOR YOUR RAG BACKEND
# Ensure your server is running first: uvicorn main:app --reload
# ============================================================

URL = "http://127.0.0.1:8000/ask"

def test_ask():
    print("✨ Entering Interactive RAG Test Mode (Type 'exit' to stop) ✨")
    print("-" * 50)
    
    while True:
        question = input("\n🙋 ASK A QUESTION: ")
        
        if question.lower() in ["exit", "quit", "q"]:
            print("👋 Goodbye!")
            break

        if not question.strip():
            continue

        print("📡 Sending to backend...")
        payload = {"question": question}
        
        try:
            response = requests.post(URL, json=payload, stream=True)
            
            if response.status_code != 200:
                print(f"❌ Error: {response.status_code}")
                continue

            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith("data: "):
                        raw_json = line_str[6:]
                        try:
                            data = json.loads(raw_json)
                            if data.get("type") == "sources":
                                sources = ", ".join(data.get("sources", []))
                                print(f"📚 RESEARCHED: {sources}")
                                print("🤖 RESPONSE: ", end="", flush=True)
                            elif data.get("type") == "token":
                                print(data.get("token", ""), end="", flush=True)
                        except:
                            continue
            print("\n" + "." * 30)

        except requests.exceptions.ConnectionError:
            print("❌ Connection Error: Is Uvicorn running?")

if __name__ == "__main__":
    test_ask()
