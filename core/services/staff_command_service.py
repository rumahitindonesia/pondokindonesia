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
