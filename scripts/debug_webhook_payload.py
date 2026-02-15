import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pondokindonesia.settings')
django.setup()

from core.models import WhatsAppMessage

def inspect_latest_messages():
    print("Inspecting latest 5 WhatsApp Messages...")
    messages = WhatsAppMessage.objects.all().order_by('-created_at')[:5]
    
    if not messages:
        print("No messages found.")
        return

    for msg in messages:
        print(f"ID: {msg.id} | Sender: {msg.sender}")
        print(f"Extracted Name: '{msg.sender_name}'")
        if msg.raw_data:
            print(f"Raw Data Keys: {list(msg.raw_data.keys())}")
            print("Full Raw Data:")
            print(json.dumps(msg.raw_data, indent=2))
        else:
            print("Raw Data: None")
        print("-" * 40)

if __name__ == "__main__":
    inspect_latest_messages()
