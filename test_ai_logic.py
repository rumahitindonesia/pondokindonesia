import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pondokindonesia.settings')
django.setup()

from core.services.ai_service import AIService
from tenants.models import Tenant

def test_ai_prompts():
    print("--- TESTING AI PROMPT LOGIC ---")
    tenant = Tenant.objects.get(subdomain='test')
    
    # Test 1: General Inquiry (Should include Objection/Complaint Rules)
    prompt = AIService.get_system_prompt(tenant=tenant, query="Kok biaya pendaftarannya mahal?")
    
    print("\nVerifying Objection Handling Rules in Prompt...")
    if "OBJECTION HANDLING" in prompt:
        print("PASSED: Objection Handling rules found in prompt.")
    else:
        print("FAILED: Objection Handling rules MISSING from prompt.")

    print("\nVerifying Complaint Handling Rules in Prompt...")
    if "COMPLAINT HANDLING" in prompt:
        print("PASSED: Complaint Handling rules found in prompt.")
    else:
        print("FAILED: Complaint Handling rules MISSING from prompt.")

    # Test 2: Simulated Objection Response (Integration would require real LLM call, 
    # but we can print the prompt to see if it's correct)
    print("\nFull Prompt Preview (Snippet):")
    print(prompt[:500] + "...")

if __name__ == "__main__":
    test_ai_prompts()
