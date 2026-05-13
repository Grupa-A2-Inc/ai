#!/usr/bin/env python
"""
Example script demonstrating how to use the Chat Support endpoint.
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
CHAT_ENDPOINT = f"{BASE_URL}/ai/api/v1/support/chat"


def print_response(response_data):
    """Pretty print the response."""
    print("\n" + "="*60)
    print(f"Model: {response_data.get('model')}")
    print(f"Timestamp: {response_data.get('timestamp')}")
    print("-"*60)
    print(f"Response:\n{response_data.get('response')}")
    print("="*60 + "\n")


def example_1_simple_question():
    """Example 1: Send a simple question."""
    print("Example 1: Simple Question")
    print("-" * 60)
    
    data = {
        "message": "What is the photosynthesis process?"
    }
    
    print(f"Sending: {json.dumps(data, indent=2)}")
    
    response = requests.post(CHAT_ENDPOINT, json=data)
    
    if response.status_code == 200:
        print_response(response.json())
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


def example_2_with_context():
    """Example 2: Send a question with student and topic context."""
    print("Example 2: Question with Student Context")
    print("-" * 60)
    
    data = {
        "message": "Can you explain Newton's third law of motion?",
        "studentId": "student-456",
        "topicId": 8,
        "context": "Grade 9 Physics - Forces and Motion"
    }
    
    print(f"Sending: {json.dumps(data, indent=2)}")
    
    response = requests.post(CHAT_ENDPOINT, json=data)
    
    if response.status_code == 200:
        print_response(response.json())
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


def example_3_algebra_help():
    """Example 3: Help with algebra."""
    print("Example 3: Algebra Help")
    print("-" * 60)
    
    data = {
        "message": "How do I solve the equation: 3x + 5 = 20?",
        "studentId": "student-789",
        "topicId": 5,
        "context": "Learning linear equations"
    }
    
    print(f"Sending: {json.dumps(data, indent=2)}")
    
    response = requests.post(CHAT_ENDPOINT, json=data)
    
    if response.status_code == 200:
        print_response(response.json())
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


def example_4_error_handling():
    """Example 4: Demonstrate error handling."""
    print("Example 4: Error Handling - Empty Message")
    print("-" * 60)
    
    data = {
        "message": ""  # Invalid: empty message
    }
    
    print(f"Sending: {json.dumps(data, indent=2)}")
    
    response = requests.post(CHAT_ENDPOINT, json=data)
    
    if response.status_code != 200:
        print(f"Status Code: {response.status_code}")
        print(f"Error Response: {json.dumps(response.json(), indent=2)}")


def example_5_long_question():
    """Example 5: More complex question."""
    print("Example 5: Complex Question")
    print("-" * 60)
    
    data = {
        "message": "What is the difference between mitochondria and chloroplast? Which one do plant cells have?",
        "studentId": "student-101",
        "topicId": 12,
        "context": "Cell Biology - Organelles"
    }
    
    print(f"Sending: {json.dumps(data, indent=2)}")
    
    response = requests.post(CHAT_ENDPOINT, json=data)
    
    if response.status_code == 200:
        print_response(response.json())
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


def batch_example():
    """Example: Batch process multiple questions."""
    print("Batch Example: Multiple Questions")
    print("="*60)
    
    questions = [
        "What is an algorithm?",
        "How do I create a function in Python?",
        "What is recursion?",
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\nQuestion {i}: {question}")
        
        data = {"message": question}
        response = requests.post(CHAT_ENDPOINT, json=data)
        
        if response.status_code == 200:
            response_text = response.json()["response"]
            # Print first 150 characters
            print(f"Answer: {response_text[:150]}...")
        else:
            print(f"Error: {response.status_code}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Chat Support Endpoint - Usage Examples")
    print("="*60)
    
    try:
        # Run examples
        example_1_simple_question()
        example_2_with_context()
        example_3_algebra_help()
        example_4_error_handling()
        example_5_long_question()
        batch_example()
        
        print("\n✓ All examples completed successfully!")
        
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to the chat service.")
        print("Make sure:")
        print("  1. Django server is running on http://localhost:8000")
        print("  2. Ollama container is running on http://localhost:11434")
        print("  3. The qwen2.5:3b model is pulled in Ollama")
    except Exception as e:
        print(f"\n✗ Error: {e}")
