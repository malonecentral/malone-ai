#!/usr/bin/env python3
"""Diagnostic script to test the Ollama endpoint."""

import asyncio
import sys

from openai import AsyncOpenAI


async def main():
    print("=== Malone AI - Ollama Endpoint Test ===\n")

    base_url = "http://mcomen.malonecentral.com:11434/v1"
    model = "llama3.1:8b"

    print(f"Endpoint: {base_url}")
    print(f"Model: {model}")
    print()

    client = AsyncOpenAI(base_url=base_url, api_key="ollama", timeout=30.0)

    # Test models list
    print("1. Listing available models...")
    try:
        models = await client.models.list()
        print(f"   Found {len(models.data)} model(s):")
        for m in models.data:
            print(f"     - {m.id}")
    except Exception as e:
        print(f"   WARNING: Could not list models: {e}")

    print()

    # Test chat completion
    print("2. Testing chat completion...")
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say hello in one sentence."}],
        )
        content = response.choices[0].message.content
        print(f"   Response: {content}")
        print("   Chat completion is working!")
    except Exception as e:
        print(f"   ERROR: {e}")
        print("   Chat completion failed.")
        sys.exit(1)

    print("\n=== Test complete ===")


if __name__ == "__main__":
    asyncio.run(main())
