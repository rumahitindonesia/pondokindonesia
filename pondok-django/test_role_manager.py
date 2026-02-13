import sys
import os
import django

sys.path.append('/home/triyono/pondok-django')
import environ
env_file = '/home/triyono/pondok-django/.env'
if os.path.exists(env_file):
    environ.Env.read_env(env_file)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pondokindonesia.settings')
django.setup()

from users.models import Role, User

print("Checking Role managers...")
try:
    print(f"Role.objects: {Role.objects}")
except Exception as e:
    print(f"Role.objects Error: {e}")

try:
    print(f"Role.global_objects: {Role.global_objects}")
except Exception as e:
    print(f"Role.global_objects Error: {e}")

try:
    print(f"Role.all_objects: {Role.all_objects}")
except Exception as e:
    print(f"Role.all_objects Error: {e}")
