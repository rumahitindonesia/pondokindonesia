from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Absensi
from .services.performance import PerformanceService

@receiver(post_save, sender=Absensi)
def create_amalan_log(sender, instance, created, **kwargs):
    """
    Generate checklist amalan harian saat pengurus melakukan absen masuk.
    """
    if created:
        PerformanceService.generate_daily_amalan(instance.pengurus, instance.tanggal)
