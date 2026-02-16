from django.core.management.base import BaseCommand
from core.models import AIKnowledgeBase
from core.services.ai_service import AIService
import time

class Command(BaseCommand):
    help = 'Sync embeddings for all AIKnowledgeBase entries'

    def handle(self, *args, **options):
        items = AIKnowledgeBase.objects.all()
        count = items.count()
        self.stdout.write(f"Starting embedding sync for {count} items...")
        
        success = 0
        failed = 0
        
        for item in items:
            self.stdout.write(f"Processing: {item.topic} (ID: {item.id})...")
            
            # Combine Topic and Content for better semantic meaning
            text_to_embed = f"Topic: {item.topic}\nContent: {item.content}"
            
            emb = AIService.generate_embedding(text_to_embed, tenant=item.tenant)
            
            if emb:
                item.embedding = emb
                item.save()
                success += 1
                self.stdout.write(self.style.SUCCESS(f"Successfully synced embedding for {item.topic}"))
            else:
                failed += 1
                self.stdout.write(self.style.ERROR(f"Failed to generate embedding for {item.topic}"))
            
            # Avoid rate limits
            time.sleep(0.5)

        self.stdout.write(self.style.SUCCESS(f"\nSync Complete! Success: {success}, Failed: {failed}"))
