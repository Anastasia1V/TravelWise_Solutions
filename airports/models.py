# airports/models.py
from django.db import models


class Airport(models.Model):
    icao = models.CharField(  # Поле для ICAO кода
        max_length=8,  # Для кодов типа NTGA, YARY и т.д. 4 символа, но 8 с запасом.
        unique=True,
        db_index=True,
        help_text="ICAO code of the airport"
    )
    name = models.CharField(max_length=255, help_text="Full name of the airport")
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=10, blank=True, null=True)  # Для ISO кодов стран (PF, AU, EG)
    latitude = models.FloatField(blank=True, null=True, help_text="Latitude in decimal degrees")
    longitude = models.FloatField(blank=True, null=True, help_text="Longitude in decimal degrees")

    # Можете добавить другие поля из CSV, если они вам нужны в модели:
    # elevation = models.IntegerField(blank=True, null=True)
    # airport_type = models.CharField(max_length=50, blank=True, null=True, db_column='type') # db_column если имя поля в модели отличается от заголовка CSV ('type' - зарезервированное слово)

    def __str__(self):
        return f"{self.name} ({self.icao})"

    class Meta:
        verbose_name = "Airport"
        verbose_name_plural = "Airports"
        ordering = ['name']