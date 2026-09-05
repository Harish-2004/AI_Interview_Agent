import asyncio
import litellm

async def main():
    print("Testing Ollama via LiteLLM...")
    models_to_test = ["ollama/qwen2.5-coder:7b", "ollama/llama3.2", "ollama/gemma:2b"]
    for m in models_to_test:
        try:
            print(f"\n--- Testing {m} ---")
            res = await litellm.acompletion(
                model=m,
                messages=[{"role": "user", "content": "Hello! Say hi in 5 words."}],
                api_base="http://localhost:11434"
            )
            print("Response:", res.choices[0].message.content)
        except Exception as e:
            print(f"Error for {m}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
