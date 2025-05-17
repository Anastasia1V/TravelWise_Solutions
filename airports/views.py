# airports/views.py
from django.shortcuts import render, redirect, get_object_or_404  # Добавил get_object_or_404
from django.contrib import messages  # Добавил messages
from .forms import AirportForm  # AirportForm все еще нужен для поля ввода ICAO
from .models import Airport
# from .utils import fetch_airport_info # Больше не нужен для этой функции
from django.http import JsonResponse
from django.db.models import Q


# Функция add_airport теперь будет работать как "find_airport_in_db_and_confirm"
def find_airport_in_db(request):  # Переименовал для ясности, но URL может остаться /add/
    form = AirportForm()  # Инициализируем форму для GET-запроса
    if request.method == 'POST':
        form = AirportForm(request.POST)
        if form.is_valid():
            icao_code = form.cleaned_data['icao'].upper()

            try:
                airport = Airport.objects.get(icao=icao_code)
                # Аэропорт НАЙДЕН в вашей базе данных!
                messages.success(request, f"Аэропорт {airport.name} ({airport.icao}) успешно найден в справочнике.")
                # Вы можете перенаправить на страницу успеха или, например,
                # на страницу деталей этого аэропорта, если такая есть.
                # Пока просто перенаправляем на общую страницу 'success'
                return redirect('airports:success_found', icao_code=airport.icao)  # Создадим новый URL и view для этого
            except Airport.DoesNotExist:
                # Аэропорта НЕТ в вашей базе данных.
                form.add_error('icao', f'Аэропорт с кодом ICAO "{icao_code}" не найден в нашем справочнике.')

    # Для GET-запроса или если форма невалидна (хотя в AirportForm только одно поле обычно)
    return render(request, 'airports/add_airport.html', {'form': form})


# Отдельная страница успеха, если аэропорт найден
def success_airport_found(request, icao_code):
    airport = get_object_or_404(Airport, icao=icao_code)
    # Можно просто сообщение, или вывести немного информации об аэропорте
    context = {
        'message': f"Аэропорт {airport.name} ({airport.icao}) успешно найден!",
        'airport': airport  # Передаем объект аэропорта в шаблон
    }
    return render(request, 'airports/success.html', context)


# Эта функция success может быть для других целей, или можно ее объединить/удалить
def success(request):  # Переименовал, чтобы не было конфликта имен
    context = {
        'message': "Операция выполнена успешно."
    }
    return render(request, 'airports/success.html', context)


# API для автодополнения (остается без изменений, оно работает с вашей БД)
def search_airports_api(request):
    query = request.GET.get('term', '').strip()
    results = []
    if len(query) >= 2:
        airports_qs = Airport.objects.filter(
            Q(icao__icontains=query) |
            Q(name__icontains=query) |
            Q(city__icontains=query)
        ).distinct().order_by('name')[:15]
        for airport in airports_qs:
            label_parts = [airport.name, f"({airport.icao.upper()})"]
            if airport.city:
                label_parts.append(f"- {airport.city}")
            full_label = " ".join(label_parts)
            results.append({
                'id': airport.icao.upper(),
                'label': full_label,
                'value': full_label
            })
    return JsonResponse(results, safe=False)