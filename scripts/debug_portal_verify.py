import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pondokindonesia.settings")
django.setup()

from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from portal.views import VerifyOTPView
from portal.services.otp_service import OTPService
from portal.models import PublicUserSession

def simulate_verify():
    print("Simulating VerifyOTPView...")
    factory = RequestFactory()
    
    # generate dummy data
    phone = "08123456789"
    user_type = "LEAD"
    user_data = {"lead_id": 1} # lead dummy id

    # Create dummy OTP session data
    request = factory.post('/portal/verify/', {'otp_code': '123456'})
    middleware = SessionMiddleware(lambda x: None)
    middleware.process_request(request)
    request.session['otp_phone_number'] = phone
    request.session.save()

    # Mock OTPService.verify_otp to return success
    # We are testing the View logic, not the Service logic (which seems fixed)
    # BUT wait, the error happened AFTER verify_otp, likely in View's session handling
    # Let's inspect VerifyOTPView.post
    
    # We need to test if OTPService.verify_otp returns the object correctly
    # and if View handles it correctly.
    
    print("Mocking OTPService.verify_otp...")
    original_verify = OTPService.verify_otp
    original_create = OTPService.create_session
    
    try:
        # Mock verify to return success
        def mock_verify(phone, code):
            print(f"Mock Verify called with {phone}, {code}")
            return True, "Success", "LEAD", {"lead_id": 1}
        
        OTPService.verify_otp = mock_verify
        
        # Test the view
        view = VerifyOTPView.as_view()
        response = view(request)
        print(f"Response status: {response.status_code}")
        
    except Exception as e:
        print(f"CAUGHT EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    finally:
        OTPService.verify_otp = original_verify

if __name__ == "__main__":
    simulate_verify()
