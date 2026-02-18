from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from core.models import Lead, APISetting
from core.services.ai_service import AIService
from core.services.starsender import StarSenderService
from core.services.lead_workflow_service import LeadWorkflowService
import re
import logging

logger = logging.getLogger(__name__)

def pendaftaran_view(request, id=None):
    if request.method == 'POST':
        try:
            # 1. Extract Data
            nama_lengkap = request.POST.get('nama_lengkap')
            no_wa = request.POST.get('no_wa_ortu')
            
            # Additional Data
            lead_data = {
                'nisn': request.POST.get('nisn'),
                'jenis_kelamin': request.POST.get('jenis_kelamin'),
                'tempat_lahir': request.POST.get('tempat_lahir'),
                'tanggal_lahir': request.POST.get('tanggal_lahir'),
                'alamat': request.POST.get('alamat'),
                'sekolah_asal': request.POST.get('sekolah_asal'),
                'jurusan': request.POST.get('jurusan'), # Changed from Jenjang
                'nama_ayah': request.POST.get('nama_ayah'),
                'nama_ibu': request.POST.get('nama_ibu'),
                'sumber': 'Web Form Pendaftaran'
            }
            
            # 2. Clean Phone Number
            if not no_wa:
                messages.error(request, "Nomor WhatsApp wajib diisi.")
                return redirect('core:pendaftaran')
                
            clean_wa = re.sub(r'\D', '', no_wa)
            if clean_wa.startswith('0'):
                clean_wa = '62' + clean_wa[1:]
            
            # 2b. Handle Photo Upload
            pas_foto_url = None
            if request.FILES.get('pas_foto'):
                try:
                    from django.core.files.storage import FileSystemStorage
                    import os
                    foto = request.FILES['pas_foto']
                    fs = FileSystemStorage()
                    ext = os.path.splitext(foto.name)[1]
                    # Sanitize filename
                    safe_name = "".join([c for c in nama_lengkap if c.isalnum() or c in (' ','_')]).replace(' ','_')
                    filename = f"uploads/santri/{clean_wa}_{safe_name}{ext}"
                    saved_name = fs.save(filename, foto)
                    pas_foto_url = fs.url(saved_name)
                except Exception as e:
                    logger.error(f"[UPLOAD ERROR] {e}")

            # Update lead_data with photo URL
            if pas_foto_url:
                lead_data['foto_santri'] = pas_foto_url
            
            # 2c. Get Tenant from ID if available (Contextual Registration to Tenant)
            santri_id = request.resolver_match.kwargs.get('id')
            tenant = getattr(request, 'tenant', None)
            
            if santri_id and not tenant:
                try:
                    from crm.models import Santri
                    santri_obj = Santri.objects.filter(id=santri_id).first()
                    if santri_obj and santri_obj.tenant:
                        tenant = santri_obj.tenant
                except:
                    pass

            # 3. Create/Update Lead
            lead, created = Lead.objects.get_or_create(
                tenant=tenant,
                phone_number=clean_wa,
                defaults={
                    'name': nama_lengkap,
                    'type': Lead.Type.SANTRI,
                    'data': lead_data,
                    'status': Lead.Status.NEW
                }
            )
            
            if not created:
                lead.name = nama_lengkap
                lead.data.update(lead_data)
                lead.status = Lead.Status.NEW
                lead.save()
                
            logger.info(f"[REGISTRATION] Lead {'created' if created else 'updated'}: {lead}")

            # 3b. Sync to Santri if ID is present (Update Existing Santri Data)
            if santri_id and tenant:
                try:
                    from crm.models import Santri
                    # Use filter to avoid crash if not found
                    santri_obj = Santri.objects.filter(id=santri_id, tenant=tenant).first()
                    if santri_obj:
                        santri_obj.nama_lengkap = nama_lengkap
                        santri_obj.alamat = lead_data.get('alamat')
                        santri_obj.nama_wali = lead_data.get('nama_ayah') or lead_data.get('nama_ibu')
                        santri_obj.no_hp_wali = clean_wa
                        
                        # Handle Date of Birth
                        tgl_lahir_str = lead_data.get('tanggal_lahir')
                        if tgl_lahir_str:
                            santri_obj.tgl_lahir = tgl_lahir_str
                            
                        santri_obj.save()
                        
                        # Link Lead to Santri
                        lead.santri = santri_obj
                        lead.save(update_fields=['santri'])
                        
                        logger.info(f"[REGISTRATION] Synced data to Santri {santri_obj.id}: {santri_obj.nama_lengkap}")
                except Exception as e:
                    logger.error(f"[REGISTRATION ERROR] Failed to sync Santri data: {e}")

            # 4. Assign CS
            assigned_cs = LeadWorkflowService.assign_to_cs(lead)
            
            # 5. Generate & Send AI Greeting
            try:
                # Prepare Context
                cs_info = f"{assigned_cs.first_name} ({assigned_cs.phone_number})" if assigned_cs else "Admin"
                
                greeting_prompt = (
                    f"Buatkan pesan konfirmasi pendaftaran resmi untuk calon santri baru.\n"
                    f"Nama Santri: {nama_lengkap}\n"
                    f"Jurusan: {lead_data.get('jurusan', '-')}\n"
                    f"Asal: {lead_data['alamat']}\n\n"
                    f"Pesan harus:\n"
                    f"- Mengucapkan selamat datang dan terima kasih telah mendaftar.\n"
                    f"- Mengonfirmasi data telah diterima sistem.\n"
                    f"- Memberitahu bahwa {cs_info} akan segera menghubungi untuk verifikasi berkas.\n"
                    f"- Nada: Formal tapi hangat, Islami."
                )

                system_prompt = (
                    "Role: Official AI Assistant of Pondok Pesantren.\n"
                    "Task: Send registration confirmation.\n"
                    "Tone: Professional, Warm, Islamic.\n"
                    "Output: WhatsApp Message Content ONLY."
                )

                # Get AI Response
                ai_response = AIService.get_completion(
                    greeting_prompt,
                    tenant=tenant,
                    sender_name=nama_lengkap,
                    sender_phone=clean_wa,
                    system_prompt=system_prompt
                )
                
                if ai_response:
                    # Send Message
                    api_key = AIService.get_setting('WHATSAPP_API_KEY_SANTRI', tenant)
                    StarSenderService.send_message(to=clean_wa, body=ai_response, tenant=tenant, api_key_override=api_key)
                    logger.info(f"[REGISTRATION] AI Greeting sent to {clean_wa}")
                    
            except Exception as e:
                logger.error(f"[REGISTRATION] AI Greeting failed: {e}")
                
            # Success Feedback
            messages.success(request, f"Alhamdulillah, pendaftaran Ananda {nama_lengkap} berhasil diterima. Cek WhatsApp Anda untuk konfirmasi.")
            return render(request, 'core/pendaftaran.html', {'success': True})
            
        except Exception as e:
            logger.error(f"[REGISTRATION ERROR] {e}")
            messages.error(request, "Terjadi kesalahan sistem. Mohon coba lagi atau hubungi Admin.")
            return redirect('core:pendaftaran')
            
    # GET Request: Render Form
    context = {}
    if id:
        try:
            from crm.models import Santri
            santri = Santri.objects.filter(id=id).first()
            if santri:
                context['initial_data'] = {
                    'nama_lengkap': santri.nama_lengkap,
                    'no_wa_ortu': santri.no_hp_wali,
                    'nama_ayah': santri.nama_wali,
                    'nama_ibu': santri.nama_wali, # Fallback
                    'nisn': santri.nis.replace('REG-', '') if santri.nis and 'REG-' in santri.nis else ''
                }
        except Exception as e:
            logger.error(f"[REGISTRATION VIEW] Failed to fetch pre-fill data: {e}")

    # Fetch Jurusan Options from APISetting with Global Fallback
    tenant = getattr(request, 'tenant', None)
    
    # 1. Try Tenant Specific
    jurusan_obj = None
    if tenant:
        jurusan_obj = APISetting.objects.filter(key_name='REGISTRATION_JURUSAN', is_active=True, tenant=tenant).first()
        
    # 2. Try Global
    if not jurusan_obj:
        jurusan_obj = APISetting.objects.filter(key_name='REGISTRATION_JURUSAN', is_active=True, tenant__isnull=True).first()

    # 3. Try Main Tenant (ID=1) as Ultimate Fallback
    if not jurusan_obj:
        jurusan_obj = APISetting.objects.filter(key_name='REGISTRATION_JURUSAN', is_active=True, tenant__id=1).first()
    if jurusan_obj:
        jurusan_options = [j.strip() for j in jurusan_obj.value.split(',') if j.strip()]
    else:
        # Default Fallback
        jurusan_options = ['Teknik Komputer Jaringan (TKJ)', 'Rekayasa Perangkat Lunak (RPL)', 'Multimedia (MM)', 'Tahfidz Al-Quran']

    context['jurusan_list'] = jurusan_options
    return render(request, 'core/pendaftaran.html', context)
