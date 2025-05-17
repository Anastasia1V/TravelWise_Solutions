# airports/admin.py
from django.contrib import admin
from .models import Airport


@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    list_display = ('icao', 'name', 'city', 'country')
    search_fields = ('icao', 'name', 'city', 'country')
    list_filter = ('country',)  # Позволит фильтровать по стране

# Альтернативный, более простой способ регистрации, если кастомизация не нужна сразу:
# admin.site.register(Airport)