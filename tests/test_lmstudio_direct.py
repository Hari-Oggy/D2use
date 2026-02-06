"""Direct LM Studio API test"""
import asyncio
import httpx
import json

async def test():
    url = "http://localhost:1234/v1/chat/completions"
    
    payload = {
        "model": "qwen2.5-7b-instruct",
        "messages": [{"role": "user", "content": "Say 'Hello, AI is working!' and nothing else."}],
        "temperature": 0.1,
        "max_tokens": 50
    }
    
    print(f"Testing: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            message = data["choices"][0]["message"]["content"]
            
            print(f"✅ SUCCESS!")
            print(f"AI Response: {message}")
            
        except Exception as e:
            print(f"❌ FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test())
