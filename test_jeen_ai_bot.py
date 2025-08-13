#!/usr/bin/env python3
"""
Test script for Jeen.ai company representative bot.
This script demonstrates how to upload company documentation and test the bot.
"""

import asyncio
import httpx
import json
from typing import List, Dict, Any

# Example Jeen.ai company documentation
SAMPLE_DOCS = [
    {
        "title": "Jeen.ai Platform Overview", 
        "content": """
        Jeen.ai is a cutting-edge AI platform designed to help enterprises harness the power of artificial intelligence. 
        Our platform provides advanced machine learning capabilities, natural language processing, and intelligent automation tools.
        
        Key features include:
        - Custom AI model training and deployment
        - Real-time data processing and analytics
        - Intelligent document processing
        - Automated workflow optimization
        - Enterprise-grade security and compliance
        
        The platform is designed for enterprise customers across various industries including finance, healthcare, manufacturing, and technology.
        """,
        "source": "company_overview"
    },
    {
        "title": "Getting Started with Jeen.ai",
        "content": """
        To get started with the Jeen.ai platform:
        
        1. Account Setup: Contact our sales team to set up your enterprise account
        2. Initial Configuration: Work with our onboarding team to configure your workspace
        3. Data Integration: Connect your data sources using our secure APIs or data connectors
        4. Model Training: Upload your training data and select appropriate AI models
        5. Deployment: Deploy your trained models to production with one-click deployment
        6. Monitoring: Use our dashboard to monitor model performance and accuracy
        
        Our customer success team is available 24/7 to help with any questions during the onboarding process.
        """,
        "source": "getting_started"
    },
    {
        "title": "Jeen.ai API Documentation",
        "content": """
        The Jeen.ai REST API allows you to integrate our AI capabilities directly into your applications.
        
        Authentication: All API requests require an API key that can be obtained from your dashboard.
        Base URL: https://api.jeen.ai/v1/
        
        Common endpoints:
        - POST /models/train - Train a new AI model
        - GET /models/{id} - Get model information
        - POST /predictions - Make predictions using trained models
        - GET /data/sources - List connected data sources
        
        Rate limits: Enterprise accounts have higher rate limits. Contact support for custom limits.
        
        All responses are in JSON format and include status codes and error messages for debugging.
        """,
        "source": "api_docs"
    },
    {
        "title": "Troubleshooting Common Issues",
        "content": """
        Common issues and solutions:
        
        1. Model Training Failures:
           - Check data format and quality
           - Ensure sufficient training data (minimum 1000 samples recommended)
           - Verify data preprocessing steps
        
        2. API Authentication Errors:
           - Verify API key is correct and active
           - Check that API key has necessary permissions
           - Ensure proper header format: Authorization: Bearer YOUR_API_KEY
        
        3. Performance Issues:
           - Check model complexity vs available compute resources
           - Consider data batching for large datasets
           - Review model configuration parameters
        
        For additional support, contact our technical team at support@jeen.ai
        """,
        "source": "troubleshooting"
    }
]

async def upload_documentation(base_url: str = "https://wallm-production.up.railway.app") -> bool:
    """Upload sample company documentation to the knowledge base."""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print(f"Uploading {len(SAMPLE_DOCS)} documents to {base_url}/load_company_documentation...")
            
            response = await client.post(
                f"{base_url}/load_company_documentation",
                json=SAMPLE_DOCS,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"Successfully uploaded documentation: {result}")
                return True
            else:
                print(f"Failed to upload documentation: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        print(f"Error uploading documentation: {e}")
        return False

async def simulate_user_questions():
    """Simulate user questions that the Jeen.ai representative should be able to answer."""
    sample_questions = [
        "What is Jeen.ai and what does it do?",
        "How do I get started with the platform?",
        "What are the main features of Jeen.ai?",
        "How do I use the API?",
        "I'm having trouble with model training, what should I check?",
        "What industries does Jeen.ai serve?",
        "How do I authenticate with the API?",
        "What's the minimum amount of training data needed?",
    ]
    
    print("\nSample questions the Jeen.ai representative can now answer:")
    for i, question in enumerate(sample_questions, 1):
        print(f"{i}. {question}")

async def main():
    print("Jeen.ai Company Representative Bot Setup")
    print("=" * 50)
    
    print("\n1. Uploading company documentation...")
    success = await upload_documentation()
    
    if success:
        print("\n2. Documentation uploaded successfully!")
        print("\nYour WhatsApp bot is now configured as a Jeen.ai company representative!")
        print("\nKey Changes Made:")
        print("- Removed all group-related functionality")
        print("- Bot now only responds to private messages")
        print("- Updated to use company documentation for responses")
        print("- Professional Jeen.ai representative system prompt")
        print("- New API endpoint for loading company docs")
        
        await simulate_user_questions()
        
        print(f"\nTo test the bot:")
        print("1. Make sure your WhatsApp webhook is pointing to your bot")
        print("2. Send a private message to the bot's WhatsApp number")
        print("3. Ask questions about Jeen.ai - the bot will use the uploaded documentation to respond")
        
        print(f"\nTo add more documentation:")
        print("POST /load_company_documentation with JSON format:")
        print(json.dumps([{
            "title": "Document Title",
            "content": "Document content here...",
            "source": "document_source"
        }], indent=2))
        
    else:
        print("\nFailed to upload documentation. Make sure the bot server is running.")
        print("Start the bot with: python app/main.py")

if __name__ == "__main__":
    asyncio.run(main())