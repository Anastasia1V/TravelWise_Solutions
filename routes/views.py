# routes/views.py
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Route
# --- ИЗМЕНЕНО: Начало ---
from django.contrib import messages  # Для возможной обратной связи
from core.models import Currency  # Для проверки существования валюты (опционально, но хорошо бы)
from decimal import Decimal, InvalidOperation  # Для работы с суммами


# --- ИЗМЕНЕНО: Конец ---


@login_required
def my_routes(request):  # <--- НЕ ТРОНУТО (если уже было так)
    qs = Route.objects.filter(owner=request.user)
    return render(request, 'routes/my_routes.html', {'routes': qs})


@login_required
def create_route(request):  # <--- Функция будет ИЗМЕНЕНА
    # --- ИЗМЕНЕНО: Начало (для передачи валют в шаблон при GET) ---
    # Для GET-запроса и для ререндеринга формы при ошибке POST
    all_currencies = Currency.objects.all().order_by('name')
    default_calc_currency_code = getattr(settings, 'BASE_CURRENCY_FOR_RATES', 'USD')  # Используем ту же, что для курсов
    context = {
        'currencies': all_currencies
    }
    if request.method == 'GET' and request.GET.get('current_name'):  # Для восстановления имени при ошибке
        context['current_name'] = request.GET.get('current_name')
    # --- ИЗМЕНЕНО: Конец ---

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        # --- ИЗМЕНЕНО: Начало (Получаем выбранную расчетную валюту) ---
        calculation_currency_code = request.POST.get('calculation_currency', '').strip().upper()
        calculation_currency_obj = None
        if calculation_currency_code:
            calculation_currency_obj = Currency.objects.filter(code=calculation_currency_code).first()
            if not calculation_currency_obj:
                messages.error(request, f"Выбранная расчетная валюта '{calculation_currency_code}' не найдена.")
                # context['error'] = ... ; context['posted_data'] = request.POST
                # return render(request, 'routes/create_route.html', context) # Вернуть на форму с ошибкой
        # --- ИЗМЕНЕНО: Конец ---

        if not name:
            # --- ИЗМЕНЕНО: Начало (используем messages и передаем контекст) ---
            messages.error(request, 'Название маршрута обязательно!')
            context['error'] = 'Название обязательно'
            context['current_name'] = name  # request.POST.get('name') уже содержит '' или значение
            # context['posted_data'] = request.POST # Если нужно восстанавливать все поля
            return render(request, 'routes/create_route.html', context)
            # --- ИЗМЕНЕНО: Конец ---

        details = []
        # --- ИЗМЕНЕНО: Начало (переходим на total_fields, если его присылает ваш JS) ---
        # Если ваш JS все еще работает через request.POST.items() и key.startswith('desc_'),
        # то этот новый цикл for i in range(total_fields) не будет работать без адаптации JS.
        # Я оставлю ваш старый цикл, но добавлю в него обработку стоимости.
        # Если вы хотите перейти на total_fields, нужно будет раскомментировать
        # и адаптировать JS.

        # Старая логика итерации тимлида, немного адаптированная:
        processed_indices = set()  # Чтобы не обрабатывать одну и ту же деталь дважды

        for key_post, desc_val_post in request.POST.items():  # Используем другое имя переменной, чтобы не путать с item_desc
            if key_post.startswith('desc_'):
                idx_str = key_post.split('_', 1)[1]
                if idx_str in processed_indices:
                    continue
                processed_indices.add(idx_str)

                item_type = request.POST.get(f'type_{idx_str}')
                item_desc = desc_val_post.strip()  # desc_val_post это значение для ключа desc_{idx_str}

                if not item_type:
                    continue

                current_detail_data = {'type': item_type, 'desc': item_desc}

                # --- ИЗМЕНЕНО: Начало (Добавляем обработку стоимости) ---
                cost_amount_str = request.POST.get(f'cost_amount_{idx_str}', '').strip()
                cost_currency_code = request.POST.get(f'cost_currency_code_{idx_str}', '').strip().upper()

                if cost_amount_str and cost_currency_code:
                    try:
                        cost_amount_decimal = Decimal(cost_amount_str)
                        if cost_amount_decimal < Decimal(0):
                            messages.warning(request,
                                             f"Стоимость для детали (индекс {idx_str}) не может быть отрицательной. Стоимость не сохранена.")
                        elif Currency.objects.filter(code=cost_currency_code).exists():
                            current_detail_data['cost_amount'] = str(cost_amount_decimal.quantize(Decimal('0.01')))
                            current_detail_data['cost_currency_code'] = cost_currency_code
                        else:
                            messages.warning(request,
                                             f"Валюта '{cost_currency_code}' для детали (индекс {idx_str}) не найдена. Стоимость не сохранена.")
                    except InvalidOperation:
                        messages.warning(request,
                                         f"Некорректная сумма '{cost_amount_str}' для детали (индекс {idx_str}). Стоимость не сохранена.")
                elif cost_amount_str or cost_currency_code:  # Если заполнено только одно из полей стоимости
                    messages.warning(request,
                                     f"Для детали (индекс {idx_str}) не указана либо сумма, либо валюта. Стоимость не сохранена.")
                # --- ИЗМЕНЕНО: Конец (Обработка стоимости) ---

                # ВАША СУЩЕСТВУЮЩАЯ ЛОГИКА ДЛЯ ДРУГИХ ПОЛЕЙ ДЕТАЛИ
                if item_type == 'flight_manual_icao':  # Ваш новый тип для рейса
                    dep_icao = request.POST.get(f'dep_icao_manual_{idx_str}', '').strip().upper()
                    arr_icao = request.POST.get(f'arr_icao_manual_{idx_str}', '').strip().upper()
                    flight_dt = request.POST.get(f'flight_datetime_{idx_str}', '')

                    if dep_icao and arr_icao:
                        current_detail_data['dep_icao_manual'] = dep_icao
                        current_detail_data['arr_icao_manual'] = arr_icao
                        if flight_dt:
                            current_detail_data['flight_datetime'] = flight_dt
                        # НЕ ищем имена аэропортов здесь, чтобы было "максимально просто"
                    else:
                        # messages.warning(request, f"Для 'Рейс' (индекс {idx_str}) не указаны оба ICAO. Будут сохранены как есть или пропущены.")
                        # Если не указаны оба, current_detail_data для рейса может быть неполным
                        pass  # Решите, добавлять ли неполную деталь

                elif item_type in ['time_range', 'date_range', 'hotel']:
                    v1 = request.POST.get(f'val1_{idx_str}', '')
                    v2 = request.POST.get(f'val2_{idx_str}', '')
                    if item_type == 'hotel':
                        hotel_name = request.POST.get(f'val_{idx_str}', '')
                        if hotel_name and v1 and v2:
                            current_detail_data['value'] = hotel_name
                            current_detail_data['dates_hotel'] = [v1, v2]
                            # else: пропуск или сообщение
                    elif v1 and v2:
                        current_detail_data['value'] = [v1, v2]
                    # else: пропуск или сообщение

                elif item_type:
                    val_simple = request.POST.get(f'val_{idx_str}', '')
                    if val_simple:
                        current_detail_data['value'] = val_simple
                    # else: пропуск или сообщение

                details.append(current_detail_data)
        # --- ИЗМЕНЕНО: Конец (Адаптация старого цикла) ---
        if not name and not details:
            messages.error(request, 'Нельзя создать пустой маршрут.')
            context['error'] = 'Маршрут не может быть пустым.'
            return render(request, 'routes/create_route.html', context)

        Route.objects.create(owner=request.user, name=name, details=details)
        messages.success(request, f"Маршрут '{name}' успешно создан.")  # Добавил messages
        return redirect('routes:my_routes')

    # --- ИЗМЕНЕНО: Начало (Передаем контекст с валютами для GET) ---
    return render(request, 'routes/create_route.html', context)
    # --- ИЗМЕНЕНО: Конец ---


@login_required
def view_route(request, route_id):  # <--- НЕ ТРОНУТО (его шаблон нужно будет изменить)
    route = get_object_or_404(Route, id=route_id, owner=request.user)
    # Получаем обработанные детали и общую стоимость из методов модели
    processed_details = route.get_processed_details_for_display()
    total_cost_info = route.get_total_cost_display

    context = {
        'route': route,
        'details_to_display': processed_details,
        'total_cost_info': total_cost_info,
    }
    return render(request, 'routes/view_route.html', {'route': route})


@login_required
def edit_route(request, route_id):  # <--- Функция будет ИЗМЕНЕНА (аналогично create_route)
    route = get_object_or_404(Route, id=route_id, owner=request.user)
    # --- ИЗМЕНЕНО: Начало (для передачи валют в шаблон при GET) ---
    all_currencies = Currency.objects.all().order_by('name')
    default_calc_currency_code = getattr(settings, 'BASE_CURRENCY_FOR_RATES', 'USD')

    # Для GET-запроса edit_route, подготовим детали для шаблона
    # (чтобы в форме отобразить уже сохраненные стоимости и валюты)
    details_for_form = []
    if request.method == 'GET' and route.details:
        for detail_item_db in route.details:
            # Просто копируем, фронтенд (JS) должен будет заполнить <select> и <input>
            # на основе этих данных при рендеринге существующих полей.
            details_for_form.append(detail_item_db.copy())

    context = {
        'route': route,  # Оригинальный объект route для имени и т.д.
        'currencies': all_currencies,
        'default_calculation_currency': route.calculation_currency.code if route.calculation_currency else default_calc_currency_code
        # 'details_for_form': details_for_form # Если JS не может сам распарсить route.details
    }
    # При GET запросе, если route.details содержит cost_amount и cost_currency_code,
    # ваш JavaScript в edit_route.html должен будет их прочитать и установить значения
    # в соответствующие поля <input> и <select> для каждой детали.
    # --- ИЗМЕНЕНО: Конец ---

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        # --- ИЗМЕНЕНО: Начало (Получаем выбранную расчетную валюту) ---
        calculation_currency_code = request.POST.get('calculation_currency', '').strip().upper()
        calculation_currency_obj = None
        if calculation_currency_code:
            calculation_currency_obj = Currency.objects.filter(code=calculation_currency_code).first()
            if not calculation_currency_obj:
                messages.error(request, f"Выбранная расчетная валюта '{calculation_currency_code}' не найдена.")
                # context['error'] = ...; context['posted_data'] = request.POST
                # return render(request, 'routes/edit_route.html', context)
        # --- ИЗМЕНЕНО: Конец ---

        new_details = []
        try:
            total_fields = int(request.POST.get('total_fields', 0))  # Ожидаем это поле от JS
        except ValueError:
            messages.error(request, 'Ошибка в данных формы.')
            total_fields = 0

        # Адаптированная логика из create_route для POST в edit_route
        for i in range(total_fields):
            item_type = request.POST.get(f'type_{i}')
            item_desc = request.POST.get(f'desc_{i}', '').strip()
            if not item_type: continue
            current_detail_data = {'type': item_type, 'desc': item_desc}

            # --- ИЗМЕНЕНО: Начало (Копируем обработку стоимости из create_route) ---
            cost_amount_str = request.POST.get(f'cost_amount_{i}', '').strip()
            cost_currency_code = request.POST.get(f'cost_currency_code_{i}', '').strip().upper()
            if cost_amount_str and cost_currency_code:
                try:
                    cost_amount_decimal = Decimal(cost_amount_str)
                    if cost_amount_decimal < Decimal(0):
                        messages.warning(request, f"Стоимость для детали (индекс {i}) не может быть отрицательной.")
                    elif Currency.objects.filter(code=cost_currency_code).exists():
                        current_detail_data['cost_amount'] = str(cost_amount_decimal.quantize(Decimal('0.01')))
                        current_detail_data['cost_currency_code'] = cost_currency_code
                    else:
                        messages.warning(request, f"Валюта '{cost_currency_code}' (деталь {i}) не найдена.")
                except InvalidOperation:
                    messages.warning(request, f"Некорректная сумма '{cost_amount_str}' (деталь {i}).")
            elif cost_amount_str or cost_currency_code:
                messages.warning(request, f"Для детали (индекс {i}) не указана сумма или валюта.")
            # --- ИЗМЕНЕНО: Конец ---

            # ВАША СУЩЕСТВУЮЩАЯ ЛОГИКА ДЛЯ ДРУГИХ ПОЛЕЙ ДЕТАЛИ (адаптированная под итерацию по i)
            if item_type == 'flight_manual_icao':
                dep_icao = request.POST.get(f'dep_icao_manual_{i}', '').strip().upper()
                arr_icao = request.POST.get(f'arr_icao_manual_{i}', '').strip().upper()
                flight_dt = request.POST.get(f'flight_datetime_{i}', '')
                if dep_icao and arr_icao:
                    current_detail_data['dep_icao_manual'] = dep_icao
                    current_detail_data['arr_icao_manual'] = arr_icao
                    if flight_dt: current_detail_data['flight_datetime'] = flight_dt
                # else: пропуск или сообщение

            elif item_type in ['time_range', 'date_range', 'hotel']:
                v1 = request.POST.get(f'val1_{i}', '')
                v2 = request.POST.get(f'val2_{i}', '')
                if item_type == 'hotel':
                    hotel_name = request.POST.get(f'val_{i}', '')
                    if hotel_name and v1 and v2:
                        current_detail_data['value'] = hotel_name
                        current_detail_data['dates_hotel'] = [v1, v2]
                elif v1 and v2:
                    current_detail_data['value'] = [v1, v2]

            elif item_type:
                val_simple = request.POST.get(f'val_{i}', '')
                if val_simple:
                    current_detail_data['value'] = val_simple

            new_details.append(current_detail_data)

        if name or new_details:
            route.name = name if name else route.name
            route.details = new_details
            route.save()
            messages.success(request, f"Маршрут '{route.name}' успешно обновлен.")
        else:
            messages.error(request, "Нельзя сохранить маршрут без названия и деталей.")
            # context['error'] = "..." # Добавить ошибку в контекст для ререндеринга
            # return render(request, 'routes/edit_route.html', context)

        return redirect('routes:view_route', route_id=route.id)

    # --- ИЗМЕНЕНО: Начало (Передаем контекст с валютами и route для GET) ---
    # Если вам не нужен 'details_for_form' и JS сам парсит route.details, то можно проще:
    # return render(request, 'routes/edit_route.html', {'route': route, 'currencies': all_currencies})
    return render(request, 'routes/edit_route.html', context)
    # --- ИЗМЕНЕНО: Конец ---


def home_redirect(request, *args, **kwargs):  # <--- НЕ ТРОНУТО
    if request.user.is_authenticated:
        return redirect('accounts:welcome')
    return redirect('accounts:login')