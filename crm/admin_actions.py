from django.contrib import admin
from django.utils.safestring import mark_safe
from django.contrib import messages
from core.services.ipaymu import IPaymuService

@admin.action(description='Generate Link Pembayaran iPaymu')
def generate_ipaymu_link(modeladmin, request, queryset):
    """
    Generate iPaymu payment link for selected TagihanSPP or TagihanProgram
    """
    success_count = 0
    fail_count = 0
    failed_details = []

    # Initialize Service (will use tenant from request or first object)
    # Ideally service should be initialized per object if tenants differ, 
    # but admin actions usually run on a queryset of the same tenant (or we handle it in loop)
    
    for obj in queryset:
        # Skip if already paid or has link (optional, maybe we want to regenerate?)
        # For now, let's allow regeneration if unpaid
        if obj.status == 'LUNAS':
            continue

        # Get Tenant
        tenant = obj.tenant
        service = IPaymuService(tenant=tenant)

        # Prepare Data
        # Transaksi ID: INV-{id} for SPP, PRG-{id} for Program
        if hasattr(obj, 'bulan'): # TagihanSPP
            ref_id = f"INV-{obj.id}"
            description = f"SPP {obj.santri.nama_lengkap} - {obj.bulan.strftime('%B %Y')}"
            amount = obj.jumlah
        else: # TagihanProgram
            ref_id = f"PRG-{obj.id}"
            description = f"{obj.program.nama_program} - {obj.santri.nama_lengkap}"
            amount = obj.nominal

        # Buyer Data
        name = obj.santri.nama_wali or obj.santri.nama_lengkap
        email = "wali@santri.id" # Placeholder or get from logic
        phone = obj.santri.no_hp_wali or "081234567890"

        # Create Payment
        result, error = service.create_payment(
            amount=amount,
            reference_id=ref_id,
            name=name,
            email=email,
            phone=phone,
            description=description
        )

        if result:
            obj.external_id = result['session_id']
            obj.payment_url = result['url']
            obj.save()
            success_count += 1
        else:
            fail_count += 1
            failed_details.append(f"{obj}: {error}")

    # User Feedback
    if success_count > 0:
        modeladmin.message_user(request, f"Berhasil membuat {success_count} link pembayaran iPaymu.", messages.SUCCESS)
    
    if fail_count > 0:
        modeladmin.message_user(request, f"Gagal: {fail_count}. Detail: {'; '.join(failed_details[:3])}", messages.ERROR)

@admin.action(description='Kirim Tagihan via WhatsApp')
def send_invoice_whatsapp(modeladmin, request, queryset):
    """
    Send payment link via WhatsApp to Wali Santri
    """
    from core.services.starsender import StarSenderService

    success_count = 0
    fail_count = 0
    skip_count = 0

    for obj in queryset:
        if not obj.payment_url:
            skip_count += 1
            continue
        
        # Get Recipient
        phone = obj.santri.no_hp_wali
        if not phone:
            fail_count += 1
            continue

        # Prepare Message
        amount = obj.jumlah if hasattr(obj, 'jumlah') else obj.nominal
        amount_fmt = f"Rp {amount:,.0f}"
        
        if hasattr(obj, 'bulan'): # TagihanSPP
            desc = f"SPP Bulan {obj.bulan.strftime('%B %Y')}"
            recipient_name = obj.santri.nama_wali or "Wali Santri"
            santri_name = obj.santri.nama_lengkap
        else: # TagihanProgram
            desc = obj.program.nama_program
            recipient_name = obj.santri.nama_wali or "Wali Santri"
            santri_name = obj.santri.nama_lengkap
            
        message = (
            f"Assalamualaikum Warahmatullahi Wabarakatuh,\n\n"
            f"Yth. Bapak/Ibu {recipient_name},\n\n"
            f"Berikut adalah informasi tagihan untuk Ananda *{santri_name}*:\n\n"
            f"💳 *{desc}*\n"
            f"💰 Nominal: *{amount_fmt}*\n\n"
            f"Silakan melakukan pembayaran melalui link berikut:\n"
            f"{obj.payment_url}\n\n"
            f"Jazakumullah Khairan Katsiran.\n"
            f"_{obj.tenant.name if obj.tenant else 'Pondok IT'}_"
        )

        try:
            # Send Message using StarSender
            StarSenderService.send_message(
                to=phone,
                body=message,
                tenant=obj.tenant
            )
            success_count += 1
        except Exception as e:
            fail_count += 1
            # Log error ideally
    
    # User Feedback
    if success_count > 0:
        modeladmin.message_user(request, f"Berhasil mengirim {success_count} pesan WhatsApp.", messages.SUCCESS)
    
    if skip_count > 0:
        modeladmin.message_user(request, f"Dilewati {skip_count} data (Link belum digenerate).", messages.WARNING)
        
    if fail_count > 0:
        modeladmin.message_user(request, f"Gagal mengirim {fail_count} pesan.", messages.ERROR)
