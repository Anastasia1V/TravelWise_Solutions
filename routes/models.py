from django.db import models
from django.conf import settings
from core.models import Currency


class Route(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    details = models.JSONField(default=list, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    # --- ИЗМЕНЕНО/ДОБАВЛЕНО: Начало ---
    calculation_currency = models.ForeignKey(
        Currency,
        on_delete=models.SET_NULL,  # Если валюту удалят, это поле станет NULL
        null=True,  # Может быть не выбрана
        blank=True,  # Необязательно для заполнения в формах
        help_text="Выбранная валюта для расчета итоговой стоимости всего маршрута"
    )
    # --- ИЗМЕНЕНО/ДОБАВЛЕНО: Конец ---

    # --- ИЗМЕНЕНО/ДОБАВЛЕНО: Начало ---
    @property
    def get_total_cost_display(self):
        """
        Рассчитывает и возвращает общую стоимость всех деталей маршрута,
        сконвертированную в self.calculation_currency.
        Возвращает словарь {'total_amount': Decimal, 'currency_code': str, 'errors': list}
        или None, если не удается посчитать.
        """
        if not self.details or not self.calculation_currency:
            return None  # Нет деталей или не выбрана валюта для расчета

        total_amount_calculated = Decimal('0.00')
        conversion_errors = []
        successful_conversions = 0

        for detail_item in self.details:
            cost_amount_str = detail_item.get('cost_amount')
            original_currency_code = detail_item.get('cost_currency_code')

            if cost_amount_str and original_currency_code:
                try:
                    original_amount = Decimal(cost_amount_str)
                    # Конвертируем на текущую дату (или дату маршрута, если она есть и актуальна)
                    # Для простоты пока используем None, чтобы convert_currency взял последнюю дату курсов
                    converted_amount = convert_currency(
                        original_amount,
                        original_currency_code,
                        self.calculation_currency.code,  # Целевая валюта
                        date_for_conversion=None  # Или self.created.date, или другая логика даты
                    )

                    if converted_amount is not None:
                        total_amount_calculated += converted_amount
                        successful_conversions += 1
                    else:
                        conversion_errors.append(
                            f"Не удалось конвертировать {original_amount} {original_currency_code} для детали: {detail_item.get('desc', 'Без описания')}"
                        )
                except InvalidOperation:
                    conversion_errors.append(
                        f"Некорректная сумма '{cost_amount_str}' в детали: {detail_item.get('desc', 'Без описания')}"
                    )

        if successful_conversions > 0 or not conversion_errors:  # Если хоть что-то сконвертировалось или не было ошибок
            return {
                'total_amount': total_amount_calculated.quantize(Decimal('0.01')),
                'currency_code': self.calculation_currency.code,
                'currency_symbol': self.calculation_currency.symbol or self.calculation_currency.code,
                'errors': conversion_errors,
                'has_errors': bool(conversion_errors)
            }
        else:  # Если ничего не удалось сконвертировать и были только ошибки
            return {'errors': conversion_errors, 'has_errors': True, 'total_amount': Decimal('0.00'),
                    'currency_code': self.calculation_currency.code}

    def get_processed_details_for_display(self):
        """
        Возвращает список деталей, где стоимость (если есть) также сконвертирована
        в self.calculation_currency.
        """
        if not self.details:
            return []

        processed_list = []
        target_currency_code = self.calculation_currency.code if self.calculation_currency else None

        for detail_item in self.details:
            item_copy = detail_item.copy()

            # Обогащение именами аэропортов (если вы это делали и сохраняли dep_name, arr_name)
            if item_copy.get('type') == 'flight_manual_icao':
                item_copy['display_dep_name'] = item_copy.get('dep_name', item_copy.get('dep_icao_manual', 'N/A'))
                item_copy['display_arr_name'] = item_copy.get('arr_name', item_copy.get('arr_icao_manual', 'N/A'))

            # Конвертация стоимости, если есть стоимость и выбрана расчетная валюта
            cost_amount_str = item_copy.get('cost_amount')
            original_currency_code = item_copy.get('cost_currency_code')

            if cost_amount_str and original_currency_code and target_currency_code:
                try:
                    original_amount = Decimal(cost_amount_str)
                    converted_amount = convert_currency(
                        original_amount,
                        original_currency_code,
                        target_currency_code,
                        date_for_conversion=None  # Или другая логика даты
                    )
                    if converted_amount is not None:
                        item_copy['converted_cost_amount'] = converted_amount.quantize(Decimal('0.01'))
                        item_copy['converted_cost_currency_code'] = target_currency_code
                    else:
                        item_copy['conversion_error'] = f"Не удалось конвертировать в {target_currency_code}"
                except InvalidOperation:
                    item_copy['conversion_error'] = f"Некорректная сумма: {cost_amount_str}"

            processed_list.append(item_copy)
        return processed_list

    # --- ИЗМЕНЕНО/ДОБАВЛЕНО: Конец ---
    def __str__(self):
        return f"{self.name} (by {self.owner.username if hasattr(self.owner, 'username') else self.owner.pk})"  # Немного улучшил __str__