#!/usr/bin/env python3
"""Test routing between company and general questions."""

import os
from pathlib import Path

# Load environment
env_path = Path('.env')
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

from chatbot.premium_chatbot import PremiumChatbot

# Initialize
chatbot = PremiumChatbot()

print("\n" + "=" * 70)
print("TEST 1: COMPANY-SPECIFIC QUESTION")
print("=" * 70)

q1 = "What are your pricing tiers?"
print(f"\nQuestion: {q1}")
r1 = chatbot.get_response(q1)
print(f"Source: {r1['source']}")
print(f"Response: {r1['response'][:200]}...")

print("\n" + "=" * 70)
print("TEST 2: GENERAL KNOWLEDGE QUESTION")
print("=" * 70)

q2 = "Who is the president of the United States?"
print(f"\nQuestion: {q2}")
r2 = chatbot.get_response(q2)
print(f"Source: {r2['source']}")
print(f"Response: {r2['response'][:200]}...")

print("\n" + "=" * 70)
print("ROUTING SUMMARY")
print("=" * 70)
print(f"✓ Company question returned source: {r1['source']}")
print(f"✓ General question returned source: {r2['source']}")
