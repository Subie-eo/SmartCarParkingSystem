from django.core.management.base import BaseCommand
from django.db import transaction

from parking.models import ParkingSlot


class Command(BaseCommand):
    help = 'Create parking slots. Usage: manage.py addslots --num 20 --prefix S --start 1 --level L1'

    def add_arguments(self, parser):
        parser.add_argument('--num', type=int, default=20, help='Number of slots to create')
        parser.add_argument('--prefix', type=str, default='S', help='Slot id prefix (e.g., S or A)')
        parser.add_argument('--start', type=int, default=1, help='Start index for numbering')
        parser.add_argument('--level', type=str, default='L1', help='Level (value for level field)')
        parser.add_argument('--force', action='store_true', help='Update existing slots with provided defaults')

    def handle(self, *args, **options):
        num = options['num']
        prefix = options['prefix']
        start = options['start']
        level = options['level']
        force = options['force']

        created = []
        updated = []
        skipped = []

        with transaction.atomic():
            for i in range(start, start + num):
                slot_id = f"{prefix}-{i:03d}"
                slot_name = f"Level {level} Spot {i:03d}" if level else f"Spot {i:03d}"
                defaults = {
                    'slot_name': slot_name,
                    'pricing_category': 'Regular',
                    'is_occupied': False,
                    'level': level,
                }

                if force:
                    slot, created_flag = ParkingSlot.objects.update_or_create(
                        slot_id=slot_id,
                        defaults=defaults
                    )
                    if created_flag:
                        created.append(slot_id)
                    else:
                        # update_or_create returns (obj, True if created)
                        # If not created, we consider it updated
                        updated.append(slot_id)
                else:
                    slot, created_flag = ParkingSlot.objects.get_or_create(
                        slot_id=slot_id,
                        defaults=defaults
                    )
                    if created_flag:
                        created.append(slot_id)
                    else:
                        skipped.append(slot_id)

        self.stdout.write(self.style.SUCCESS(f"Created {len(created)} slots: {created}"))
        if updated:
            self.stdout.write(self.style.SUCCESS(f"Updated {len(updated)} slots: {updated}"))
        if skipped:
            self.stdout.write(self.style.WARNING(f"Skipped (already existed) {len(skipped)} slots: {skipped}"))

        total = ParkingSlot.objects.count()
        self.stdout.write(self.style.SUCCESS(f"Total parking slots in DB: {total}"))
