import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from crm.models import TagihanSPP, TransaksiDonasi
from django.utils import timezone

@csrf_exempt
@require_POST
def ipaymu_webhook(request):
    """
    Webhook handler for iPaymu v2 notifications.
    """
    data = request.POST
    
    if not data:
        try:
            data = json.loads(request.body)
        except:
            return HttpResponse("Invalid Payload", status=400)

    sid = data.get('sid')
    reference_id = data.get('reference_id')
    status = data.get('status') 

    if not reference_id:
        return HttpResponse("Missing reference_id", status=400)

    # Identify if it's an Invoice (SPP) or Donation
    if reference_id.startswith('INV-'):
        try:
            invoice_id = reference_id.replace('INV-', '')
            obj = TagihanSPP.objects.get(id=invoice_id)
            if status in ['berhasil', 'paid']:
                obj.status = TagihanSPP.Status.LUNAS
                obj.tanggal_bayar = timezone.now()
                obj.save()
        except TagihanSPP.DoesNotExist:
            return HttpResponse("Invoice Not Found", status=404)

    elif reference_id.startswith('DON-'):
        try:
            donation_id = reference_id.replace('DON-', '')
            obj = TransaksiDonasi.objects.get(id=donation_id)
            if status in ['berhasil', 'paid']:
                obj.status = TransaksiDonasi.Status.VERIFIED
                obj.save()
        except TransaksiDonasi.DoesNotExist:
            return HttpResponse("Donation Not Found", status=404)

    return HttpResponse("OK")
