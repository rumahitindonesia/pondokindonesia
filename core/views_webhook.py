import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from crm.models import Tagihan, TransaksiDonasi
from django.utils import timezone

@csrf_exempt
@require_POST
def ipaymu_webhook(request):
    """
    Webhook handler for iPaymu v2 notifications.
    iPaymu sends data via POST.
    """
    # iPaymu sends data as form data or JSON depending on configuration
    # By default it's usually POST form data
    data = request.POST
    
    if not data:
        try:
            data = json.loads(request.body)
        except:
            return HttpResponse("Invalid Payload", status=400)

    # Key fields from iPaymu: sid (SessionID), status (paid, etc), reference_id
    sid = data.get('sid')
    reference_id = data.get('reference_id')
    status = data.get('status') # 'berhasil' or 'paid' for success

    if not reference_id:
        return HttpResponse("Missing reference_id", status=400)

    # Identify if it's an Invoice or Donation
    if reference_id.startswith('INV-'):
        try:
            invoice_id = reference_id.replace('INV-', '')
            obj = Tagihan.objects.get(id=invoice_id)
            if status in ['berhasil', 'paid']:
                obj.status = Tagihan.Status.LUNAS
                obj.tgl_bayar = timezone.now()
                obj.save()
                # TODO: Trigger WhatsApp Notification here if needed
        except Tagihan.DoesNotExist:
            return HttpResponse("Invoice Not Found", status=404)

    elif reference_id.startswith('DON-'):
        try:
            donation_id = reference_id.replace('DON-', '')
            obj = TransaksiDonasi.objects.get(id=donation_id)
            # Donations are created as success records usually, 
            # but we could use this to finalize them if they were 'pending'
            if status in ['berhasil', 'paid']:
                # Update something if needed
                pass
        except TransaksiDonasi.DoesNotExist:
            return HttpResponse("Donation Not Found", status=404)

    return HttpResponse("OK")
