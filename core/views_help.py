from django.http import JsonResponse
from .models import Tutorial
from django.db.models import Q

def get_tutorial_api(request):
    """
    Fetch tutorial content based on the 'key' parameter.
    URL: /help/api/?key=crm.santri
    """
    key = request.GET.get('key')
    if not key:
        return JsonResponse({'error': 'Missing key'}, status=400)
    
    tutorial = Tutorial.objects.filter(target_key=key, is_active=True).first()
    
    if tutorial:
        return JsonResponse({
            'title': tutorial.title,
            'content': tutorial.content,
            'video_url': tutorial.video_url,
            'found': True
        })
    
    return JsonResponse({
        'title': 'Bantuan Belum Tersedia',
        'content': 'Panduan untuk menu ini sedang dalam proses pembuatan. Silakan hubungi pusat bantuan kami.',
        'found': False
    })

from django.views.decorators.csrf import csrf_exempt
import json
from core.services.ai_service import AIService
from crm.models import Santri, Donatur, TagihanSPP
from django.db.models import Q

class LiveDataRetriever:
    @staticmethod
    def search(query, tenant):
        if not tenant or len(query) < 3:
            return ""
        
        results = []
        q = query.lower()

        # Simple keyword extractor: strip common Indonesian filler words
        filler_words = ["siapa", "dimana", "tolong", "cek", "data", "carikan", "tampilkan", "daftar", 
                        "ada", "yang", "bernama", "dengan", "saya", "kamu", "yasmin", "halo", "permisi", 
                        "mau", "tanya", "apa", "bagaimana", "berikan", "info", "informasi"]
        
        clean_q = q
        for word in filler_words:
            clean_q = clean_q.replace(f" {word} ", " ").replace(f"{word} ", "").replace(f" {word}", "")
        
        clean_q = clean_q.strip()
        search_terms = [clean_q] if clean_q else []
        # If the query is long, also try to search by individual words if they look like names
        if len(clean_q.split()) > 1:
            search_terms.extend([w for w in clean_q.split() if len(w) > 2])

        # Dedup search terms
        search_terms = list(dict.fromkeys(search_terms))

        # Helper to get admin change URL
        def get_admin_url(obj, model_name, app_label='crm'):
            return f"/admin/{app_label}/{model_name}/{obj.id}/change/"

        # Search function to avoid redundancy
        def perform_search(model, fields, terms, tenant_filter=True):
            objs = model.objects.all()
            if tenant_filter:
                objs = objs.filter(tenant=tenant)
            
            final_q = Q()
            for term in terms:
                term_q = Q()
                for field in fields:
                    term_q |= Q(**{f"{field}__icontains": term})
                final_q |= term_q
            
            return objs.filter(final_q)

        # 1. Search Santri
        found_santris = perform_search(Santri, ['nama_lengkap', 'nis', 'no_hp_wali'], search_terms)[:5]
        for s in found_santris:
            url = get_admin_url(s, 'santri')
            latest_spp = s.tagihan_spp.order_by('-bulan').first()
            status_spp = f"{latest_spp.get_status_display()} ({latest_spp.bulan_display})" if latest_spp else "N/A"
            results.append(f"SANTRI: {s.nama_lengkap} (NIS: {s.nis}), Wali: {s.nama_wali}, Telp: {s.no_hp_wali}, SPP: {status_spp}. URL_EDIT: {url}")

        # 2. Search Donatur
        found_donaturs = perform_search(Donatur, ['nama_donatur', 'no_hp'], search_terms)[:5]
        for d in found_donaturs:
            url = get_admin_url(d, 'donatur')
            results.append(f"DONATUR: {d.nama_donatur} (KODE: {d.kode_donatur}), Telp: {d.no_hp}, Kategori: {d.get_kategori_display()}. URL_EDIT: {url}")

        # 3. Search Tagihan SPP
        if any(w in q for w in ['spp', 'tagihan', 'bayar', 'tunggak', 'lunas']):
            # Filter specifically for SPP
            found_spp = TagihanSPP.objects.filter(tenant=tenant).filter(
                Q(santri__nama_lengkap__icontains=clean_q) | Q(santri__nis__icontains=clean_q)
            ).order_by('-bulan')[:5]
            for t in found_spp:
                url = get_admin_url(t, 'tagihanspp')
                results.append(f"TAGIHAN SPP: {t.santri.nama_lengkap}, Bulan: {t.bulan_display}, Nom: {t.jumlah_display}, Stat: {t.get_status_display()}. URL_DETAIL: {url}")

        # 4. Search Donasi/Program
        if any(w in q for w in ['donasi', 'program', 'pendaftaran', 'masuk', 'dana']):
            from crm.models import TransaksiDonasi, TagihanProgram
            found_donasi = TransaksiDonasi.objects.filter(tenant=tenant).filter(
                Q(donatur__nama_donatur__icontains=clean_q) | Q(program__nama_program__icontains=clean_q)
            )[:3]
            for td in found_donasi:
                url = get_admin_url(td, 'transaksidonasi')
                results.append(f"DONASI: {td.donatur.nama_donatur}, Prog: {td.program.nama_program}, Nom: Rp {td.nominal:,.0f}, Stat: {td.get_status_display()}. URL_EDIT: {url}")
            
            found_prog = TagihanProgram.objects.filter(tenant=tenant).filter(
                Q(santri__nama_lengkap__icontains=clean_q) | Q(program__nama_program__icontains=clean_q)
            )[:3]
            for tp in found_prog:
                url = get_admin_url(tp, 'tagihanprogram')
                results.append(f"PROG: {tp.program.nama_program}, Santri: {tp.santri.nama_lengkap}, Nom: Rp {tp.nominal:,.0f}, Stat: {tp.get_status_display()}. URL_DETAIL: {url}")

        if not results:
            return ""
            
        return "\n\n=== DATA TERKINI DARI DATABASE ===\n" + "\n".join(results)

@csrf_exempt
def chat_assistant_api(request):
    """
    Interactive AI Chat Assistant with Live Data Retrieval.
    URL: /help/api/chat/ (POST)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        message = data.get('message')
        key = data.get('key', 'general')
        chat_history = data.get('chat_history', []) # New: receive history from frontend
        tenant = getattr(request, 'tenant', None)
        
        if not message:
            return JsonResponse({'error': 'Message required'}, status=400)
            
        # Context 1: Tutorial/Knowledge Context
        tutorial_context = ""
        if key and key != 'general':
            tutorial = Tutorial.objects.filter(target_key=key, is_active=True).first()
            if tutorial:
                tutorial_context = f"\nKonteks Halaman: {tutorial.title}\nIsi Panduan: {tutorial.content}"

        # Context 2: Live Data Context (Tenant Scoped)
        live_data_context = LiveDataRetriever.search(message, tenant)

        # Context 3: Vector Search / RAG Knowledge Context
        vector_context = AIService.find_relevant_knowledge(message, tenant)

        # Context 4: Menu Registry (Major Modules)
        menu_registry = (
            "\n=== DAFTAR MENU UTAMA ===\n"
            "- Menu Santri: /admin/crm/santri/\n"
            "- Menu Donatur: /admin/crm/donatur/\n"
            "- Menu Tagihan SPP: /admin/crm/tagihanspp/\n"
            "- Menu Lead/Pendaftaran: /admin/core/lead/\n"
            "- Menu Knowledge Base: /admin/core/aiknowledgebase/\n"
            "- Menu Pengaturan API: /admin/core/apisetting/\n"
            "- Dashboard Utama: /admin/\n"
        )

        system_prompt = (
            "Anda adalah Yasmin, AI Assistant (Admin Virtual) untuk pengelola Pondok Pesantren. "
            "Tugas Anda adalah membantu user memahami fitur panel admin dan memberikan informasi data secara cerdas. "
            "Gunakan bahasa Indonesia yang ramah, sopan, dan profesional.\n\n"
            "KEMAMPUAN DATA LIVE:\n"
            "Anda dapat mencari data Santri, Donatur, Tagihan SPP, Tagihan Program, dan Transaksi Donasi secara spesifik berdasarkan nama atau identitas.\n\n"
            "ATURAN LINK & NAVIGASI:\n"
            "1. Jika merujuk ke data spesifik (Santri/Donatur/SPP/Donasi), WAJIB sertakan link HTML menggunakan format: "
            "<a href='URL' class='text-primary-600 dark:text-primary-400 underline font-black'>[Teks Klik]</a>\n"
            "2. Gunakan URL_EDIT atau URL_DETAIL yang disediakan di bagian DATA TERKINI.\n"
            "3. Jika menyarankan ke menu tertentu, gunakan link dari DAFTAR MENU UTAMA.\n"
            "4. Selalu gunakan target='_self'.\n"
            "PENTING: Gunakan data terkini di bawah ini untuk menjawab secara detail. Jika tidak ada data yang cocok, sarankan user untuk mencari dengan kata kunci (nama) yang lebih spesifik."
        )
        
        if tutorial_context:
            system_prompt += f"\n\n=== KONTEKS PANDUAN HALAMAN ==={tutorial_context}"
        if live_data_context:
            system_prompt += f"\n\n{live_data_context}"
        if vector_context:
            system_prompt += f"\n\n{vector_context}"
        
        system_prompt += menu_registry
            
        response = AIService.get_completion(
            message=message,
            tenant=tenant,
            sender_name=request.user.get_full_name() or request.user.username,
            system_prompt=system_prompt,
            chat_history=chat_history # Passing history to AIService
        )
        
        return JsonResponse({'reply': response})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
