import os
import sys
from pathlib import Path
import django

# Ensure project root is on sys.path when running this script directly
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CarParking.settings')
django.setup()

from CarParking.models import ParkingSlot

# Configuration: create 20 slots with IDs S-001 .. S-020
NUM = 20
prefix = 'S'
start = 1
created = []
skipped = []

for i in range(start, start + NUM):
    slot_id = f"{prefix}-{i:03d}"
    slot_name = f"Level 1 Spot {i:03d}"
    try:
        slot, created_flag = ParkingSlot.objects.get_or_create(
            slot_id=slot_id,
            defaults={
                'slot_name': slot_name,
                'pricing_category': ParkingSlot.PRICING_STANDARD if i % 5 != 0 else ParkingSlot.PRICING_PREMIUM,
                'is_occupied': False,
                'level': 'L1',
            }
        )
        if created_flag:
            created.append(slot_id)
        else:
            skipped.append(slot_id)
    except Exception as e:
        print(f"Error creating {slot_id}:", e)

print(f"Created {len(created)} slots: {created}")
if skipped:
    print(f"Skipped (already existed) {len(skipped)} slots: {skipped}")

# Print a quick count from DB
print('Total parking slots in DB:', ParkingSlot.objects.count())
