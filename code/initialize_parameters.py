import os
import django
import uuid
from datetime import datetime
from django.utils.timezone import get_current_timezone
import pytz

# Configurar Django para que el script pueda acceder a los modelos
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NMB.settings')
django.setup()

from dashboard.models import *

# Inicializar datos
def initialize_data():
    """
    Initializes example data in the database, including timezone choices.
    """
    # Inicializar TimeZoneChoices
    timezones = [
        'UTC -12:00', 'UTC -11:00', 'UTC -10:00', 'UTC -09:00', 'UTC -08:00',
        'UTC -07:00', 'UTC -06:00', 'UTC -05:00', 'UTC -04:00', 'UTC -03:00',
        'UTC -02:00', 'UTC -01:00', 'UTC +00:00', 'UTC +01:00', 'UTC +02:00',
        'UTC +03:00', 'UTC +04:00', 'UTC +05:00', 'UTC +06:00', 'UTC +07:00',
        'UTC +08:00', 'UTC +09:00', 'UTC +10:00', 'UTC +11:00', 'UTC +12:00'
    ]

    for tz in timezones:
        TimeZoneChoices.objects.get_or_create(value=tz)

    # Obtener zonas horarias
    departure_tz = pytz.timezone("America/Chicago")  # UTC -06:00
    arrival_tz = pytz.timezone("America/New_York")  # UTC -05:00

    departure_tz_choice = TimeZoneChoices.objects.get(value="UTC -06:00")
    arrival_tz_choice = TimeZoneChoices.objects.get(value="UTC -05:00")

    # Inicializar Status
    statuses = [
        {'state': 'Rejected'},
        {'state': 'Approved'},
        {'state': 'Pending'},
        {'state': 'Analysis'},
    ]
    for status in statuses:
        Status.objects.get_or_create(state=status['state'], defaults={'state': status['state']})

    # Inicializar Parameters
    parameters = [
        {'name': 'max_temp', 'value': 15},
        {'name': 'min_temp', 'value': 2},
        {'name': 'time_fraccion_max_temp', 'value': 10},
        {'name': 'time_fraccion_min_temp', 'value': 90},
        {'name': 'cifra', 'value': 10},
        {'name': 'cifraFront', 'value': 2},
    ]
    for param in parameters:
        Parameters.objects.get_or_create(name=param['name'], defaults={'value': param['value']})

    # Inicializar SensorLocation
    sensor_locations = [
        {'name': 'BOTTOM', 'description': 'Bottom'},
        {'name': 'MIDDLE', 'description': 'Middle'},
        {'name': 'TOP', 'description': 'Top'},
    ]
    for location in sensor_locations:
        SensorLocation.objects.get_or_create(name=location['name'], defaults={'description': location['description']})

    # Inicializar PalletLocation (1 a 28)
    for position in range(1, 29):
        PalletLocation.objects.get_or_create(position=position)

    # Inicializar ProductType
    product_types = [
        {'name': 'UNTREATED', 'description': 'Untreated'},
        {'name': 'OHMIC_HEATING', 'description': 'Ohmic Heating'},
        {'name': 'HTST', 'description': 'HTST'},
    ]
    for product in product_types:
        ProductType.objects.get_or_create(name=product['name'], defaults={'description': product['description']})

    # Inicializar Microorganism
    microorganisms = [
        {'name': 'PSYCHROPHILES', 'description': 'Psychrophiles'},
        {'name': 'MOLDS_YEASTS', 'description': 'Molds and Yeasts'},
    ]
    for microorganism in microorganisms:
        Microorganism.objects.get_or_create(name=microorganism['name'], defaults={'description': microorganism['description']})

    # Inicializar Equation para PSYCHROPHILES y UNTREATED
    microorganism = Microorganism.objects.get(name='PSYCHROPHILES')
    product = ProductType.objects.get(name='UNTREATED')

    Equation.objects.get_or_create(
        microorganism=microorganism,
        product=product,
        defaults={
            'LPD_form': "k*mT**a",
            'LPD_parameters': "{'k': 1.3, 'a': -0.14}",
            'b_form': "k_b * np.log(mT) + a_b",
            'b_parameters': "{'k_b': 0.5757, 'a_b': 3.0481}",
            'n_form': "k_n * (mT ** a_n)",
            'n_parameters': "{'k_n': 0.1226, 'a_n': 0.0517}",
            'Tc': "{'Tc': 4.0}",
            'dtu': "{'dtu':  1 / (24 * 60 * 60)}",
        }
    )

    # Inicializar Equation para PSYCHROPHILES y OHMIC_HEATING
    microorganism = Microorganism.objects.get(name='PSYCHROPHILES')
    product = ProductType.objects.get(name='OHMIC_HEATING')

    Equation.objects.get_or_create(
        microorganism=microorganism,
        product=product,
        defaults={
            'LPD_form': "k*mT**a",
            'LPD_parameters': "{'k': 12.66 , 'a': -0.92 }",
            'b_form': "k_b * np.log(mT) + a_b",
            'b_parameters': "{'k_b': 0.60 , 'a_b': 1.38 }",
            'n_form': "k_n * (mT ** a_n)",
            'n_parameters': "{'k_n': 0.08 , 'a_n': 0.56 }",
            'Tc': "{'Tc': 4.0}",
            'dtu': "{'dtu':  1 / (24 * 60 * 60)}",
        }
    )

    # Inicializar Equation para PSYCHROPHILES y HTST
    microorganism = Microorganism.objects.get(name='PSYCHROPHILES')
    product = ProductType.objects.get(name='HTST')

    Equation.objects.get_or_create(
        microorganism=microorganism,
        product=product,
        defaults={
            'LPD_form': "k*mT**a",
            'LPD_parameters': "{'k': 36.04  , 'a': -1.71  }",
            'b_form': "k_b * np.log(mT) + a_b",
            'b_parameters': "{'k_b': 2.39  , 'a_b': -0.87 }",
            'n_form': "k_n * (mT ** a_n)",
            'n_parameters': "{'k_n': 1.54 , 'a_n': -1.38  }",
            'Tc': "{'Tc': 4.0}",
            'dtu': "{'dtu':  1 / (24 * 60 * 60)}",
        }
    )


    # Inicializar Equation para MOLDS_YEASTS y UNTREATED
    microorganism = Microorganism.objects.get(name='MOLDS_YEASTS')
    product = ProductType.objects.get(name='UNTREATED')

    Equation.objects.get_or_create(
        microorganism=microorganism,
        product=product,
        defaults={
            'LPD_form': "k*mT**a",
            'LPD_parameters': "{'k': 26.78    , 'a': -1.13   }",
            'b_form': "k_b * np.exp(a_b*mT)",
            'b_parameters': "{'k_b': 1.6698   , 'a_b': 0.0374   }",
            'n_form': "k_n *np.log(mT) + a_n",
            'n_parameters': "{'k_n': 0.0145 , 'a_n': 0.1596 }",
            'Tc': "{'Tc': 4.0}",
            'dtu': "{'dtu':  1 / (24 * 60 * 60)}",
        }
    )

    # Inicializar Equation para MOLDS_YEASTS y OHMIC_HEATING
    microorganism = Microorganism.objects.get(name='MOLDS_YEASTS')
    product = ProductType.objects.get(name='OHMIC_HEATING')

    Equation.objects.get_or_create(
        microorganism=microorganism,
        product=product,
        defaults={
            'LPD_form': "k*mT**a",
            'LPD_parameters': "{'k': 6.14   , 'a': -0.51  }",
            'b_form': "k_b * np.exp(a_b*mT) ",
            'b_parameters': "{'k_b': 1.69   , 'a_b': 0.024  }",
            'n_form': "k_n *np.log(mT + a_n)",
            'n_parameters': "{'k_n': 0.02  , 'a_n': 0.09 }",
            'Tc': "{'Tc': 4.0}",
            'dtu': "{'dtu':  1 / (24 * 60 * 60)}",
        }
    )

    # Inicializar Equation para MOLDS_YEASTS y HTST
    microorganism = Microorganism.objects.get(name='MOLDS_YEASTS')
    product = ProductType.objects.get(name='HTST')

    Equation.objects.get_or_create(
        microorganism=microorganism,
        product=product,
        defaults={
            'LPD_form': "k*mT**a",
            'LPD_parameters': "{'k': 26.78    , 'a': -1.13   }",
            'b_form': "k_b * np.exp(a_b*mT) ",
            'b_parameters': "{'k_b': 1.04   , 'a_b': 0.057   }",
            'n_form': "k_n *np.log(mT) + a_n",
            'n_parameters': "{'k_n': -0.00132 , 'a_n': 0.36 }",
            'Tc': "{'Tc': 4.0}",
            'dtu': "{'dtu':  1 / (24 * 60 * 60)}",
        }
    )

    

    # Crear un ejemplo de Trip con zona horaria
    microorganism = Microorganism.objects.get(name="PSYCHROPHILES")
    product = ProductType.objects.get(name="UNTREATED")

    Trip.objects.get_or_create(
        shipment="2",
        license_plate="EJTO 241",
        driver="Fran",
        origin="Los Ángeles, California",
        destination="Houston, Texas",
        departure_date = departure_tz.localize(datetime(2023, 11, 20, 3, 4, 8)).astimezone(pytz.UTC),
        departure_timezone=departure_tz_choice,
        arrival_date = arrival_tz.localize(datetime(2023, 11, 21, 8, 59, 58)).astimezone(pytz.UTC),
        arrival_timezone=arrival_tz_choice,
        product=product,
        microorganism=microorganism
    )

    Trip.objects.get_or_create(
        shipment="1",
        license_plate="EJTO 165",
        driver="Fran",
        origin="Houston, Texas",
        destination="Chicago, Illinois",
        departure_date=departure_tz.localize(datetime(2023, 10, 31, 0,23, 4)),
        departure_timezone=departure_tz_choice,
        arrival_date=arrival_tz.localize(datetime(2023, 11, 1, 6, 18, 54)),
        arrival_timezone=arrival_tz_choice,
        product=product,
        microorganism=microorganism
    )

    # Crear un ejemplo de Trip con zona horaria
    microorganism = Microorganism.objects.get(name="PSYCHROPHILES")
    product = ProductType.objects.get(name="OHMIC_HEATING")

    Trip.objects.get_or_create(
        shipment="2",
        license_plate="EJTO 341",
        driver="Fran",
        origin="Los Ángeles, California",
        destination="Houston, Texas",
        departure_date = departure_tz.localize(datetime(2023, 11, 20, 3, 4, 8)).astimezone(pytz.UTC),
        departure_timezone=departure_tz_choice,
        arrival_date = arrival_tz.localize(datetime(2023, 11, 21, 8, 59, 58)).astimezone(pytz.UTC),
        arrival_timezone=arrival_tz_choice,
        product=product,
        microorganism=microorganism
    )

    # Crear un ejemplo de Trip con zona horaria
    microorganism = Microorganism.objects.get(name="MOLDS_YEASTS")
    product = ProductType.objects.get(name="UNTREATED")

    Trip.objects.get_or_create(
        shipment="2",
        license_plate="EJTO 31",
        driver="Fran",
        origin="Los Ángeles, California",
        destination="Houston, Texas",
        departure_date = departure_tz.localize(datetime(2023, 11, 20, 3, 4, 8)).astimezone(pytz.UTC),
        departure_timezone=departure_tz_choice,
        arrival_date = arrival_tz.localize(datetime(2023, 11, 21, 8, 59, 58)).astimezone(pytz.UTC),
        arrival_timezone=arrival_tz_choice,
        product=product,
        microorganism=microorganism
    )

    print("TimeZoneChoices, Status, Parameters, SensorLocation, PalletLocation, ProductType, Microorganism,Equations and Trips initialized successfully.")

if __name__ == '__main__':
    initialize_data()
