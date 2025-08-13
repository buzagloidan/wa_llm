#!/usr/bin/env python3
"""
Test webhook functionality by sending a simulated WhatsApp message
"""
import asyncio
import httpx
import json
from datetime import datetime

async def test_webhook():
    """Send a test webhook payload to the bot."""
    
    # Sample WhatsApp webhook payload for a private message
    test_payload = {
        "from": "1234567890@c.us",  # Private message (not group)
        "pushname": "Test User",
        "timestamp": datetime.now().isoformat(),
        "message": {
            "id": f"test_{int(datetime.now().timestamp())}",
            "text": "Hello, what is Jeen.ai?"
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("Testing webhook with private message...")
            
            response = await client.post(
                "https://wallm-production.up.railway.app/webhook",
                json=test_payload,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Webhook Response: {response.status_code}")
            print(f"Response Text: {response.text}")
            
            if response.status_code == 200:
                print("Webhook accepted the message!")
            else:
                print(f"Webhook failed: {response.status_code}")
                
    except Exception as e:
        print(f"Error testing webhook: {e}")

if __name__ == "__main__":
    asyncio.run(test_webhook())