# airports/management/commands/load_airports.py
import csv
from django.core.management.base import BaseCommand, CommandError
from airports.models import Airport


class Command(BaseCommand):
    help = 'Loads airport data from the provided CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file_path', type=str, help='The CSV file path for airport data')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file_path']
        self.stdout.write(self.style.SUCCESS(f"Attempting to load airports from: {csv_file_path}..."))

        loaded_count = 0
        skipped_count = 0
        updated_count = 0

        try:
            with open(csv_file_path, mode='r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file)  # Разделитель по умолчанию - запятая

                # Опционально: проверить заголовки один раз
                # if reader.fieldnames:
                #     self.stdout.write(self.style.NOTICE(f"Detected CSV Headers: {reader.fieldnames}"))
                # else: # ... обработка ошибки ...

                for row_number, row in enumerate(reader, 1):
                    # Ключи из вашего нового, чистого CSV
                    csv_key_for_icao = 'icao'
                    csv_key_for_name = 'name'
                    csv_key_for_city = 'city'
                    csv_key_for_country = 'country'
                    csv_key_for_latitude = 'latitude'
                    csv_key_for_longitude = 'longitude'
                    # csv_key_for_elevation = 'elevation' # Если будете использовать
                    # csv_key_for_type = 'type'         # Если будете использовать

                    icao_val = row.get(csv_key_for_icao)
                    name_val = row.get(csv_key_for_name)

                    clean_icao = str(icao_val).strip().upper() if icao_val else ''
                    clean_name = str(name_val).strip() if name_val else ''

                    if not clean_icao or not clean_name:
                        skipped_count += 1
                        continue

                    if len(clean_icao) > 8:
                        skipped_count += 1
                        continue

                    city_val = row.get(csv_key_for_city)
                    country_val = row.get(csv_key_for_country)
                    latitude_val = row.get(csv_key_for_latitude)
                    longitude_val = row.get(csv_key_for_longitude)
                    # elevation_val = row.get(csv_key_for_elevation)
                    # type_val = row.get(csv_key_for_type)

                    try:
                        lat_str = str(latitude_val).strip() if latitude_val else ''
                        lon_str = str(longitude_val).strip() if longitude_val else ''
                        lat_float = float(lat_str) if lat_str else None
                        lon_float = float(lon_str) if lon_str else None
                        # elev_int = int(str(elevation_val).strip()) if elevation_val and str(elevation_val).strip() else None
                    except ValueError:
                        lat_float = None
                        lon_float = None
                        # elev_int = None

                    defaults_for_db = {
                        'name': clean_name,
                        'city': str(city_val).strip() if city_val else None,
                        'country': str(country_val).strip().upper() if country_val else None,
                        'latitude': lat_float,  # Имя поля из вашей модели
                        'longitude': lon_float,  # Имя поля из вашей модели
                        # 'elevation': elev_int,
                        # 'airport_type': str(type_val).strip() if type_val else None
                    }

                    # Имя поля ICAO в вашей модели Airport (вы сказали, что это 'icao')
                    model_pk_field_name = 'icao'

                    try:
                        airport, created = Airport.objects.update_or_create(
                            **{model_pk_field_name: clean_icao},  # Используем ** для динамического имени поля
                            defaults=defaults_for_db
                        )
                        if created:
                            loaded_count += 1
                        else:
                            updated_count += 1

                        if (loaded_count + updated_count) % 1000 == 0 and (loaded_count + updated_count) > 0:
                            self.stdout.write(self.style.SUCCESS(
                                f"Processed {row_number} rows. Loaded: {loaded_count}, Updated: {updated_count}..."))

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Row {row_number} ({clean_icao}): DB Error: {e}"))
                        skipped_count += 1

            self.stdout.write(self.style.SUCCESS(
                f"Airport loading complete. "
                f"Total rows examined: {row_number}. "
                f"Successfully created: {loaded_count}. "
                f"Successfully updated: {updated_count}. "
                f"Skipped: {skipped_count}."
            ))

        except FileNotFoundError:
            raise CommandError(f"Error: File not found at {csv_file_path}")
        except Exception as e:
            import traceback
            self.stderr.write(self.style.ERROR(f"An critical error occurred: {e}"))
            self.stderr.write(traceback.format_exc())