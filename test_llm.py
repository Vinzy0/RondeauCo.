import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def test_llm():
    print("🤖 Entering Direct LLM Test Mode (Type 'exit' to stop) 🤖")
    print("-" * 50)
    
    llm = ChatOpenAI(
        model="meta-llama/llama-3.1-8b-instruct",
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base="https://openrouter.ai/api/v1",
        streaming=False,
        temperature=0.3,
    )
    
    while True:
        prompt = input("\n📝 ENTER PROMPT: ")
        
        if prompt.lower() in ["exit", "quit", "q"]:
            print("👋 Goodbye!")
            break

        if not prompt.strip():
            continue

        print("📡 Sending to OpenRouter...")
        try:
            response = llm.invoke(prompt)
            print(f"🤖 LLM: {response.content}")
        except Exception as e:
            print(f"❌ LLM Error: {str(e)}")

if __name__ == "__main__":
    test_llm()
