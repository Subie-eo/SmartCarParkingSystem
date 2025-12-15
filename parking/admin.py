from django.contrib import admin
from .models import ParkingSlot, Booking, PricingRate

# Admin action to free multiple slots at once
@admin.action(description="Mark selected slots as free")
def mark_as_free(modeladmin, request, queryset):
    queryset.update(is_occupied=False)

@admin.register(ParkingSlot)
class ParkingSlotAdmin(admin.ModelAdmin):
    list_display = ('slot_id', 'slot_name', 'level', 'pricing_category', 'is_occupied')
    list_editable = ('is_occupied',)  # Allows admin to manually toggle occupied status
    search_fields = ('slot_id', 'slot_name', 'level')
    list_filter = ('pricing_category', 'is_occupied')
    actions = [mark_as_free]  # Adds bulk free action

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'slot', 'start_time', 'end_time', 'total_fee', 'payment_status')
    list_filter = ('payment_status', 'slot__pricing_category')
    search_fields = ('user__email', 'slot__slot_id', 'slot__slot_name')


@admin.register(PricingRate)
class PricingRateAdmin(admin.ModelAdmin):
    list_display = ('category', 'rate')
    list_editable = ('rate',)
    search_fields = ('category',)
