import requests
import json

# ============================================================
# SIMPLE TEST SCRIPT FOR YOUR RAG BACKEND
# Ensure your server is running first: uvicorn main:app --reload
# ============================================================

URL = "http://127.0.0.1:8000/ask"

def test_ask():
    print("✨ Entering Interactive RAG Test Mode (Stateful) ✨")
    print("Type 'exit' to stop, 'clear' to reset memory.")
    print("-" * 50)
    
    # This is your "Client Side Session Storage"
    history = []
    
    while True:
        question = input("\n🙋 ASK A QUESTION: ")
        
        if question.lower() in ["exit", "quit", "q"]:
            print("👋 Goodbye!")
            break

        if question.lower() == "clear":
            history = []
            print("🧠 Memory cleared!")
            continue

        if not question.strip():
            continue

        print("📡 Sending to backend...")
        # Now we send the history list along with the question
        payload = {
            "question": question,
            "history": history
        }
        
        full_response = ""
        
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
                                token = data.get("token", "")
                                full_response += token
                                print(token, end="", flush=True)
                        except:
                            continue
            
            # SAVE TO MEMORY: Append the exchange to history for the next turn
            history.append({"role": "user", "content": question})
            history.append({"role": "assistant", "content": full_response})
            
            # Keep history manageable (last 10 messages)
            if len(history) > 10:
                history = history[-10:]

            print("\n" + "." * 30)

        except requests.exceptions.ConnectionError:
            print("❌ Connection Error: Is Uvicorn running?")

if __name__ == "__main__":
    test_ask()
