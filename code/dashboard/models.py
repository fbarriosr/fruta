from django.db import models
from admin_auto_filters.filters import AutocompleteFilter
from autoslug import AutoSlugField
from django.utils import timezone
from import_export.admin import ImportExportModelAdmin
from django.utils.timezone import now  # Import the 'now' function
from pytz import timezone, all_timezones
import uuid
import os


class TimeZoneChoices(models.Model):
    """
    Model to store timezone choices with a unique ID and value.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    value = models.CharField(max_length=10, unique=True)  # Value in format 'UTC ±HH:MM'

    def __str__(self):
        return self.value

class ProductType(models.Model):
    """
    Model to represent product types.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)  # e.g., "UNTREATED", "HTST"
    description = models.CharField(max_length=255)  # e.g., "Untreated", "HTST"

    def __str__(self):
        return self.description


class Microorganism(models.Model):
    """
    Model to represent microorganism types.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)  # e.g., "PSYCHROPHILES", "MOLDS_YEASTS"
    description = models.CharField(max_length=255)  # e.g., "Psychrophiles", "Molds and Yeasts"

    def __str__(self):
        return self.description


class SensorLocation(models.Model):
    """
    Model for Sensor Location Choices.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)  # e.g., "BOTTOM", "CENTER", "TOP"
    description = models.CharField(max_length=255)  # e.g., "Bottom", "Center", "Top"

    def __str__(self):
        return self.description


class PalletLocation(models.Model):
    """
    Model for Pallet Locations as integers (1 to 25).
    """
    id = models.AutoField(primary_key=True)
    position = models.PositiveIntegerField(unique=True)  # Range from 1 to 25

    def __str__(self):
        return str(self.position)

class Parameters(models.Model):
    name = models.CharField(max_length=50, unique=True)  # Nombre del parámetro
    value = models.FloatField()  # Valor del parámetro

    def __str__(self):
        return f"{self.name}: {self.value}"

class Trip(models.Model):
    """
    Model to represent a refrigerated trip with timezone support.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shipment = models.CharField(max_length=255, default='')  # Shipment
    license_plate = models.CharField(max_length=255)  # Vehicle identification
    driver = models.CharField(max_length=255)  # Driver's name
    origin = models.CharField(max_length=255)  # Origin location
    destination = models.CharField(max_length=255)  # Destination location
    departure_date = models.DateTimeField()  # Departure date and time
    departure_timezone = models.ForeignKey(
        TimeZoneChoices,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='departure_trips'
    )  # Departure timezone as ForeignKey
    arrival_date = models.DateTimeField()  # Arrival date and time
    arrival_timezone = models.ForeignKey(
        TimeZoneChoices,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='arrival_trips'
    )  # Arrival timezone as ForeignKey
    product = models.ForeignKey(
        'ProductType',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trips"
    )  # Product type as foreign key
    microorganism = models.ForeignKey(
        'Microorganism',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trips"
    )  # Microorganism type as foreign key

    def __str__(self):
        return f"Trip {self.license_plate} ({self.departure_date} - {self.arrival_date})"


class Status(models.Model):
    """
    Model to represent decision messages.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    state = models.CharField(max_length=255)  # Decision text

    def __str__(self):
        return self.state


class Sensor(models.Model):
    """
    Model to represent sensor data.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.CharField(max_length=255)  # Device model
    serial_number = models.CharField(max_length=50)  # Unique serial number
    description = models.TextField()  # Description of the sensor or device
    pallet_location = models.ForeignKey(
        'PalletLocation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sensors'
    )  # Pallet location as foreign key
    trip = models.ForeignKey(
        'Trip',
        on_delete=models.CASCADE,  # Elimina los sensores cuando se borra un trip
        related_name="sensors",
        null=True,
        blank=True, 
    )
    sensor_position = models.ForeignKey(
        'SensorLocation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sensors'
    )  # Sensor position as foreign key
    tag = models.CharField(max_length=255, null=True, default='No Tag')  # New field for tags

    # New fields
    time_range = models.CharField(max_length=255, null=True, blank=True, default='')  # Time Range
    max_temperature = models.FloatField(null=True, blank=True, default=None)  # Max Temperature
    min_temperature = models.FloatField(null=True, blank=True, default=None)  # Min Temperature
    lpa_max_time = models.CharField(max_length=255, null=True, blank=True, default='')  # LPA MAX TIME
    analysis = models.ImageField(upload_to='sensor_analysis/', null=True, blank=True, default=None)  # Analysis image
    status = models.ForeignKey(
        'Status',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sensors'
    )  # Status as ForeignKey
    total_records = models.PositiveIntegerField(default=0)  # Total Records
    timezone = models.ForeignKey(
        TimeZoneChoices,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='timezone_sensors'
    )  # Departure timezone as ForeignKey

    def __str__(self):
        return f"{self.device} - {self.serial_number}"


class Record(models.Model):
    sensor = models.ForeignKey(
        Sensor,
        on_delete=models.CASCADE,  # Elimina los registros cuando se borra un sensor
        related_name="records",
        null=True,
        blank=True
    )
    number = models.PositiveIntegerField()
    time = models.DateTimeField()
    temperature = models.FloatField()

    def __str__(self):
        return f"Record {self.number} - {self.temperature}°C"
def default_tc():
    return {"Tc": 4.0}

def default_dtu():
    return {"dtu": 1 / (24 * 60 * 60)}

class Equation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Fórmula matemática en notación LaTeX o descripción textual
    LPD_form = models.TextField(
        help_text="Ingrese la fórmula en formato LaTeX o texto.",
        blank=True,
        default=""
    )

    # Parámetros de la ecuación (clave-valor)
    LPD_parameters = models.JSONField(
        help_text="Ingrese los parámetros como un diccionario, e.g., {'a': 2.5, 'b': 1.0}.",
        blank=True,
        default=dict
    )

    # Fórmula matemática en notación LaTeX o descripción textual
    b_form = models.TextField(
        help_text="Ingrese la fórmula en formato LaTeX o texto.",
        blank=True,
        default=""
    )

    # Parámetros de la ecuación (clave-valor)
    b_parameters = models.JSONField(
        help_text="Ingrese los parámetros como un diccionario, e.g., {'a': 2.5, 'b': 1.0}.",
        blank=True,
        default=dict
    )

    n_form = models.TextField(
        help_text="Ingrese la fórmula en formato LaTeX o texto.",
        blank=True,
        default=""
    )

    # Parámetros de la ecuación (clave-valor)
    n_parameters = models.JSONField(
        help_text="Ingrese los parámetros como un diccionario, e.g., {'a': 2.5, 'b': 1.0}.",
        blank=True,
        default=dict
    )

    Tc = models.JSONField(
        help_text="Ingrese los parámetros como un diccionario, e.g., {'Tc': 4.0}.",
        blank=True,
        default=default_tc
    )

    dtu = models.JSONField(
        help_text="Ingrese los parámetros como un diccionario, e.g., {'dtu':  1 / (24 * 60 * 60)}.",
        blank=True,
        default=default_dtu
    )

    # Fecha de creación y última modificación
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Relaciones con ProductType y Microorganism
    product = models.ForeignKey(
        ProductType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="equations"
    )
    microorganism = models.ForeignKey(
        Microorganism,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="equations"
    )

    def __str__(self):
        return f"{self.microorganism} + {self.product}" if self.microorganism and self.product else "Equation"

    def clean(self):
        # Validar que parameters sea un diccionario con valores numéricos
        if not isinstance(self.LPD_parameters, dict):
            raise ValidationError("El campo 'LPD_parameters' debe ser un diccionario.")

        for key, value in self.LPD_parameters.items():
            if not isinstance(value, (int, float)):
                raise ValidationError(f"El valor de '{key}' debe ser numérico.")

    def evaluate(self, **kwargs):
        """
        Evalúa la ecuación si se proporcionan los valores de los parámetros.
        """
        from sympy import sympify
        from sympy.abc import x, y, z  # Puedes definir las variables necesarias

        try:
            # Convierte la fórmula a una expresión de sympy
            expr = sympify(self.LPD_form)

            # Validar si las variables necesarias están en la fórmula
            required_vars = set(kwargs.keys())
            formula_vars = {str(symbol) for symbol in expr.free_symbols}

            if not required_vars.issubset(formula_vars):
                missing_vars = required_vars - formula_vars
                return f"Faltan variables en la fórmula: {', '.join(missing_vars)}"

            # Evalúa la fórmula con los parámetros proporcionados
            return expr.subs(kwargs)
        except Exception as e:
            return f"Error al evaluar la fórmula: {e}"
