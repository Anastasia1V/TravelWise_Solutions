from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Route


@login_required
def my_routes(request):
    qs = Route.objects.filter(owner=request.user)
    return render(request, 'routes/my_routes.html', {'routes': qs})


@login_required
def create_route(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            return render(request, 'routes/create_route.html', {'error': 'Название обязательно'})
        details = []
        for key, desc in request.POST.items():
            if key.startswith('desc_'):
                idx = key.split('_', 1)[1]
                t = request.POST.get(f'type_{idx}')
                v = request.POST.get(f'val_{idx}', '')
                v2 = request.POST.get(f'val2_{idx}', '')
                if t in ['time_range', 'date_range']:
                    details.append({'desc': desc, 'type': t, 'value': [v, v2]})
                else:
                    details.append({'desc': desc, 'type': t, 'value': v})
        Route.objects.create(owner=request.user, name=name, details=details)
        return redirect('routes:my_routes')
    return render(request, 'routes/create_route.html')


@login_required
def view_route(request, route_id):
    route = get_object_or_404(Route, id=route_id, owner=request.user)
    return render(request, 'routes/view_route.html', {'route': route})


@login_required
def edit_route(request, route_id):
    route = get_object_or_404(Route, id=route_id, owner=request.user)

    if request.method == 'POST':
        # ... (Ваша логика POST-запроса для сохранения изменений,
        #      которая должна быть АНАЛОГИЧНА create_route в части обработки деталей,
        #      используя total_fields и индексированные имена полей) ...
        # Например:
        name = request.POST.get('name', '').strip()
        new_details_list = []  # Собираем новые/обновленные детали
        try:
            total_fields = int(request.POST.get('total_fields', 0))
        except ValueError:
            messages.error(request, 'Ошибка в данных формы.')
            total_fields = 0

        for i in range(total_fields):
            item_type = request.POST.get(f'type_{i}')
            item_desc = request.POST.get(f'desc_{i}', '').strip()
            if not item_type: continue
            current_detail_data = {'type': item_type, 'desc': item_desc}

            if item_type == 'flight_manual_icao':
                dep_icao = request.POST.get(f'dep_icao_manual_{i}', '').strip().upper()
                arr_icao = request.POST.get(f'arr_icao_manual_{i}', '').strip().upper()
                flight_dt = request.POST.get(f'flight_datetime_{i}', '')
                if dep_icao and arr_icao:
                    current_detail_data['dep_icao_manual'] = dep_icao
                    current_detail_data['arr_icao_manual'] = arr_icao
                    if flight_dt: current_detail_data['flight_datetime'] = flight_dt
                    new_details_list.append(current_detail_data)
                else:
                    messages.warning(request, f"Для 'Рейс' №{i + 1} не указаны оба ICAO. Не сохранено.")

            elif item_type in ['time_range', 'date_range', 'hotel']:
                val1 = request.POST.get(f'val1_{i}', '')
                val2 = request.POST.get(f'val2_{i}', '')
                if item_type == 'hotel':
                    hotel_name_val = request.POST.get(f'val_{i}', '')
                    if hotel_name_val and val1 and val2:
                        current_detail_data['value'] = hotel_name_val
                        current_detail_data['dates_hotel'] = [val1, val2]
                        new_details_list.append(current_detail_data)
                    else:
                        messages.warning(request, f"Для 'Гостиница' №{i + 1} не заполнены (название, даты).")
                elif val1 and val2:
                    current_detail_data['value'] = [val1, val2]
                    new_details_list.append(current_detail_data)
                else:
                    messages.warning(request, f"Для диапазона '{item_type}' №{i + 1} не указаны оба значения.")

            elif item_type:
                val_simple = request.POST.get(f'val_{i}', '')
                if val_simple:
                    current_detail_data['value'] = val_simple
                    new_details_list.append(current_detail_data)
                else:
                    messages.warning(request, f"Для '{item_type}' №{i + 1} не указано значение.")

        if name or new_details_list:  # Сохраняем, если есть имя или хотя бы 1 деталь
            route.name = name if name else route.name
            route.details = new_details_list  # ПОЛНОСТЬЮ ЗАМЕНЯЕМ СТАРЫЕ ДЕТАЛИ НОВЫМИ
            route.save()
            messages.success(request, f"Маршрут '{route.name}' успешно обновлен.")
        else:
            messages.error(request, "Нельзя сохранить маршрут без названия и деталей.")
            # Важно передать route обратно, чтобы форма осталась заполненной
            return render(request, 'routes/edit_route.html', {'route': route})

        return redirect('routes:view_route', route_id=route.id)

    # Для GET-запроса: просто передаем существующий объект route
    # Шаблон edit_route.html будет использовать route.details для отображения
    return render(request, 'routes/edit_route.html', {'route': route})

def home_redirect(request, *args, **kwargs):
    if request.user.is_authenticated:
        return redirect('accounts:welcome')
    return redirect('accounts:login')
