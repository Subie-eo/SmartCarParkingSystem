from django.core.management.base import BaseCommand
from parking.models import ParkingSlot

class Command(BaseCommand):
    help = 'List all parking slots with details'

    def handle(self, *args, **options):
        slots = ParkingSlot.objects.all().order_by('slot_id')
        self.stdout.write(f'Found {slots.count()} slot(s)')
        for s in slots:
            self.stdout.write(f'- slot_id={s.slot_id} slot_name={s.slot_name} level={s.level} pricing={s.pricing_category} occupied={s.is_occupied} pk={s.pk}')
