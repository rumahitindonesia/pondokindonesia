from users.models import User
from crm.services import CRMService

class StaffCommandService:
    @staticmethod
    def process_message(tenant, message, sender_phone):
        """
        Process a staff command message.
        Format: username#command#data1#data2...
        """
        parts = [p.strip() for p in message.split('#')]
        if len(parts) < 2:
            return None # Not a command format

        username = parts[0].lower()
        command = parts[1].lower()
        
        # 1. Authorize Staff
        try:
            # Use _base_manager to find staff across tenants if needed, 
            # but usually restricted to the same tenant or global admin
            staff = User._base_manager.get(username=username, is_active=True)
            
            # Basic Security: Staff must belong to the same tenant OR be a superuser
            if not staff.is_superuser and staff.tenant != tenant:
                return f"Error: Anda tidak memiliki akses ke tenant {tenant.subdomain}."
            
            # Optional: Verify if sender_phone matches staff's phone_number
            # if staff.phone_number and staff.phone_number != sender_phone:
            #     return f"Error: Nomor HP {sender_phone} tidak terdaftar untuk user {username}."

        except User.DoesNotExist:
            return None # Ignore if username doesn't exist to avoid conflict with public info

        # 2. Execute Command
        if command == 'santri':
            # format: username#santri#nama#nohp#alamat
            if len(parts) >= 5:
                res, msg = CRMService.direct_insert_santri(tenant, {
                    'nama': parts[2],
                    'phone': parts[3],
                    'alamat': parts[4]
                }, staff_user=staff)
                return msg
            return "Error format Santri: username#santri#nama#nohp#alamat"

        elif command == 'donatur':
            # format: username#donatur#nama#nohp#alamat
            if len(parts) >= 5:
                res, msg = CRMService.direct_insert_donatur(tenant, {
                    'nama': parts[2],
                    'phone': parts[3],
                    'alamat': parts[4]
                }, staff_user=staff)
                return msg
            return "Error format Donatur: username#donatur#nama#nohp#alamat"

        elif command == 'donasi':
            # format: username#donasi#kode_donatur#nama_program#nominal#keterangan
            if len(parts) >= 5:
                try:
                    res, msg = CRMService.direct_insert_donation(tenant, {
                        'donatur_kode': parts[2],
                        'program_nama': parts[3],
                        'nominal': int(parts[4]),
                        'keterangan': parts[5] if len(parts) > 5 else "Input via WA"
                    }, staff_user=staff)
                    return msg
                except ValueError:
                    return "Error: Nominal harus angka."
            return "Error format Donasi: username#donasi#kode_donatur#nama_program#nominal#keterangan"

        elif command == 'kode':
            # format: username#kode#donatur#nama_pencarian
            if len(parts) >= 4:
                return CRMService.search_records(tenant, parts[2].lower(), parts[3])
            return "Error format Kode: username#kode#donatur/santri#nama"

        return None # Command not recognized

    @staticmethod
    def process_message_v2(tenant, message, staff_user):
        """
        Process a staff command message using standardized keywords.
        Keywords: LEAD/, SANTRI/, DONATUR/, TRX/, CARI
        """
        msg_upper = message.upper()
        
        # 1. Handle SEARCH (CARI [keyword])
        if msg_upper.startswith('CARI '):
            query = message[5:].strip()
            if not query:
                return "Format CARI salah. Contoh: CARI Ahmad"
            
            # Search across Santri and Donatur
            res_santri = CRMService.search_records(tenant, 'santri', query)
            res_donatur = CRMService.search_records(tenant, 'donatur', query)
            
            return f"--- Hasil Pencarian ---\n\n{res_santri}\n\n{res_donatur}"

        # 2. Handle DATA INPUT (KEYWORD/)
        # Common format: KEYWORD/data1#data2#...
        valid_keywords = ['LEAD/', 'SANTRI/', 'DONATUR/', 'TRX/']
        keyword = None
        for kw in valid_keywords:
            if msg_upper.startswith(kw):
                keyword = kw
                break
        
        if not keyword:
            return None # Not a recognized staff command
            
        # Extract body and parts
        body = message[len(keyword):].strip()
        parts = [p.strip() for p in body.split('#')]
        
        if keyword == 'LEAD/':
            # format: LEAD/nama#nohp#keterangan
            if len(parts) >= 2:
                from core.models import Lead
                lead = Lead.objects.create(
                    tenant=tenant,
                    name=parts[0],
                    phone_number=parts[1],
                    notes=parts[2] if len(parts) > 2 else "Input via WA Staff",
                    cs=staff_user,
                    status=Lead.Status.NEW
                )
                return f"Lead '{lead.name}' ({lead.phone_number}) berhasil disimpan dan ditugaskan ke Anda."
            return "Format LEAD salah: LEAD/nama#nohp#keterangan"

        elif keyword == 'SANTRI/':
            # format: SANTRI/nama#nohp#alamat
            if len(parts) >= 3:
                res, msg = CRMService.direct_insert_santri(tenant, {
                    'nama': parts[0],
                    'phone': parts[1],
                    'alamat': parts[2]
                }, staff_user=staff_user)
                return msg
            return "Format SANTRI salah: SANTRI/nama#nohp#alamat"

        elif keyword == 'DONATUR/':
            # format: DONATUR/nama#nohp#alamat
            if len(parts) >= 3:
                res, msg = CRMService.direct_insert_donatur(tenant, {
                    'nama': parts[0],
                    'phone': parts[1],
                    'alamat': parts[2]
                }, staff_user=staff_user)
                return msg
            return "Format DONATUR salah: DONATUR/nama#nohp#alamat"

        elif keyword == 'TRX/':
            # format: TRX/kode#program#nominal#keterangan
            # kode can be NIS (Santri) or Kode Donatur
            if len(parts) >= 3:
                try:
                    # Attempt donation insert
                    res, msg = CRMService.direct_insert_donation(tenant, {
                        'donatur_kode': parts[0],
                        'program_nama': parts[1],
                        'nominal': int(parts[2]),
                        'keterangan': parts[3] if len(parts) > 3 else "Input via WA Staff"
                    }, staff_user=staff_user)
                    return msg
                except ValueError:
                    return "Error: Nominal harus angka."
            return "Format TRX salah: TRX/kode#program#nominal#keterangan"

        return "Keyword staff dikenali tapi gagal diproses."
