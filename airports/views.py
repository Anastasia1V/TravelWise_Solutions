# airports/views.py
from django.shortcuts import render, redirect
from .forms import AirportForm
from .models import Airport
from .utils import fetch_airport_info
from django.http import JsonResponse
from django.db.models import Q
# from django.contrib.auth.decorators import login_required # Раскомментируйте при необходимости


def add_airport(request, icao):
    if request.method == 'POST':
        form = AirportForm(request.POST)
        if form.is_valid():
            icao = form.cleaned_data['icao'].upper()
            info = fetch_airport_info(icao)
            if info:
                Airport.objects.create(
                    icao=icao,
                    name=info['name'],
                    city=info['city'],
                    country=info['country']
                )
                return redirect('airports:success')
            else:
                form.add_error('icao', 'Аэропорт с таким ICAO не найден')
    else:
        form = AirportForm()
    return render(request, 'airports/add_airport.html', {'form': form})


def success(request):
    return render(request, 'airports/success.html')


# @login_required
def search_airports_api(request):
    query = request.GET.get('term', '').strip()  # Оставляем strip(), .upper() сделаем при сравнении с полем
    results = []

    if len(query) >= 2:
        # Поиск по ICAO делаем регистронезависимым, предполагая, что ICAO коды могут быть в разном регистре
        # или пользователь может вводить в любом.
        # Если ICAO в базе всегда UPPERCASE, то можно query.upper() и Q(icao__contains=query.upper())
        airports_qs = Airport.objects.filter(
            Q(icao__icontains=query) |  # Регистронезависимый поиск ICAO
            Q(name__icontains=query) |  # Регистронезависимый поиск по названию
            Q(city__icontains=query)  # Регистронезависимый поиск по городу
        ).distinct().order_by('name')[:15]  # distinct() если возможны дубликаты из-за OR с icontains

        for airport in airports_qs:
            label_parts = [airport.name, f"({airport.icao.upper()})"]  # Показываем ICAO в верхнем регистре
            if airport.city:
                label_parts.append(f"- {airport.city}")
            # if airport.country:
            #     label_parts.append(f", {airport.country}")

            full_label = " ".join(label_parts)
            results.append({
                'id': airport.icao.upper(),  # Возвращаем ICAO в верхнем регистре как ID
                'label': full_label,  # Полная метка для отображения
                'value': full_label  # Это значение jQuery UI Autocomplete по умолчанию подставит в input
            })

    return JsonResponse(results, safe=False)