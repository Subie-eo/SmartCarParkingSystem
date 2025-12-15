from django.contrib import admin
from .models import ContactInfo


@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'email', 'phone', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    search_fields = ('company_name', 'email', 'phone')
