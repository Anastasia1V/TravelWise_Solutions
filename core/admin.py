# core/admin.py
from django.contrib import admin
from .models import Currency, ExchangeRate


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'symbol')
    search_fields = ('code', 'name')
    ordering = ('code',)


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ('currency_code', 'rate', 'date', 'last_updated')  # Используем кастомный метод для currency_code
    list_filter = ('date', 'currency__code')  # Фильтруем по коду валюты
    search_fields = ('currency__code', 'currency__name')
    date_hierarchy = 'date'  # Удобная навигация по датам
    ordering = ('-date', 'currency__code')
    list_select_related = ('currency',)  # Оптимизация запроса для отображения currency.code

    def currency_code(self, obj):  # Кастомное поле для отображения кода валюты
        return obj.currency.code

    currency_code.short_description = 'Код валюты'  # Название колонки в админке
    currency_code.admin_order_field = 'currency__code'  # Включаем сортировку по этой колонке