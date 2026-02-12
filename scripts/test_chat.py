import os
import sys
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.chat_service import handle_chat

def test_chat():
    print("--- Testing Chat ---")
    
    # 1. Initial Question
    query = "What is the leave policy?"
    print(f"\nUser: {query}")
    
    response = handle_chat(query, [], awaiting_followup=False)
    
    print(f"Bot: {response['reply']}")
    print(f"State: {json.dumps({k:v for k,v in response.items() if k != 'reply'}, indent=2)}")

    print(f"DEBUG: awaiting_followup={response.get('awaiting_followup')}")

    # 2. Follow-up "Yes"
    # Force run for debugging
    if True:
        print("\n--- Testing Follow-up Response 'Yes' ---")
        followup_input = "Yes, please."
        print(f"User: {followup_input}")
        
        response_2 = handle_chat(
            query=followup_input,
            history=[], # In real app, history would be accumulated
            awaiting_followup=True,
            last_context=response['last_context'],
            last_followup_question=response['last_followup_question']
        )
        
        print(f"Bot: {response_2['reply']}")

if __name__ == "__main__":
    test_chat()
