from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q
from hr.models import Absensi, Tugas, LogAmalan, JenisAmalan, PeriodePenilaian, TargetKPI, RealisasiKPI, KamusKPI

class PerformanceService:
    @staticmethod
    def calculate_attendance_score(pengurus, start_date, end_date):
        """
        Hitung skor kehadiran berdasarkan data Absensi.
        Rumus sederhana: (Jumlah Hadir / Total Hari Kerja) * 100
        Note: Total Hari Kerja diasumsikan exclude Weekend? 
        Untuk MVP: Total Hari dalam range dikurangi weekend.
        """
        # 1. Hitung Hari Kerja (Senin-Jumat)
        total_days = (end_date - start_date).days + 1
        work_days = 0
        current = start_date
        while current <= end_date:
            if current.weekday() < 5: # 0-4 is Mon-Fri
                work_days += 1
            current += timezone.timedelta(days=1)
        
        if work_days == 0:
            return 0
            
        # 2. Hitung Kehadiran (Hadir/Telat dianggap masuk, Izin setengah?)
        # Asumsi: Hadir = 1, Telat = 0.9, Izin = 0.5, Alpha = 0
        attendance_records = Absensi.objects.filter(
            pengurus=pengurus, 
            tanggal__range=[start_date, end_date]
        )
        
        score_point = 0
        for record in attendance_records:
            if record.status in [Absensi.Status.HADIR]:
                score_point += 1
            elif record.status == Absensi.Status.TELAT:
                score_point += 0.9 # Penalti telat
            elif record.status in [Absensi.Status.IZIN, Absensi.Status.SAKIT]:
                score_point += 0.5 # Setengah poin
            elif record.status == Absensi.Status.ALPHA:
                score_point += 0
        
        tunjangan_kehadiran = (score_point / work_days) * 100
        return min(tunjangan_kehadiran, 100.0)

    @staticmethod
    def calculate_task_score(pengurus, start_date, end_date):
        """
        Hitung rata-rata skor tugas yang selesai dalam periode ini.
        """
        tasks = Tugas.objects.filter(
            penerima=pengurus,
            tanggal_selesai__range=[start_date, end_date],
            status=Tugas.Status.SELESAI,
            skor__isnull=False
        )
        
        if not tasks.exists():
            return 0
            
        avg_score = tasks.aggregate(Avg('skor'))['skor__avg']
        return avg_score or 0

    @staticmethod
    def calculate_amalan_score(pengurus, start_date, end_date):
        """
        Hitung persentase amalan yang dikerjakan vs total target.
        """
        logs = LogAmalan.objects.filter(
            pengurus=pengurus,
            tanggal__range=[start_date, end_date]
        )
        
        if not logs.exists():
            return 0
            
        # Total Poin yang harusnya didapat (jika semua dikerjakan)
        # Agregat berdasarkan LogAmalan yang terbentuk
        total_possible_points = logs.aggregate(Sum('amalan__poin'))['amalan__poin__sum'] or 0
        
        # Total Poin yang didapat (is_done=True)
        earned_points = logs.filter(is_done=True).aggregate(Sum('amalan__poin'))['amalan__poin__sum'] or 0
        
        if total_possible_points == 0:
            return 0
            
        return (earned_points / total_possible_points) * 100

    @staticmethod
    def generate_daily_amalan(pengurus, tanggal=None):
        """
        Generate Checklist Amalan Harian untuk Pengurus.
        """
        if not tanggal:
            tanggal = timezone.now().date()
            
        # Ambil semua jenis amalan aktif (harian)
        jenis_amalan = JenisAmalan.objects.filter(kategori__iexact='Harian', tenant=pengurus.tenant)
        
        created_count = 0
        for ja in jenis_amalan:
            obj, created = LogAmalan.objects.get_or_create(
                pengurus=pengurus,
                tanggal=tanggal,
                amalan=ja,
                tenant=pengurus.tenant,
                defaults={'is_done': False}
            )
            if created:
                created_count += 1
        return created_count

    @staticmethod
    def update_realisasi_kpi(pengurus, periode):
        """
        Update nilai RealisasiKPI secara otomatis berdasarkan data Absensi, Tugas, dll.
        """
        targets = TargetKPI.objects.filter(pengurus=pengurus, periode=periode)
        
        for t in targets:
            source = t.indikator.sumber_data
            value = 0
            
            if source == KamusKPI.Sumber.AUTO_ABSENSI:
                value = PerformanceService.calculate_attendance_score(pengurus, periode.start_date, periode.end_date)
            elif source == KamusKPI.Sumber.AUTO_TUGAS:
                value = PerformanceService.calculate_task_score(pengurus, periode.start_date, periode.end_date)
            elif source == KamusKPI.Sumber.AUTO_IBADAH:
                value = PerformanceService.calculate_amalan_score(pengurus, periode.start_date, periode.end_date)
            
            # Update Realisasi jika ada auto-value
            if source in [KamusKPI.Sumber.AUTO_ABSENSI, KamusKPI.Sumber.AUTO_TUGAS, KamusKPI.Sumber.AUTO_IBADAH]:
                realisasi, _ = RealisasiKPI.objects.get_or_create(target_kpi=t, tenant=t.tenant, defaults={'realisasi': 0})
                realisasi.realisasi = value
                realisasi.save() # Trigger save() method for nilai_akhir calculation
