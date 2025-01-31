#  estándar de Python
import csv
import io
import random
import ast
import base64
import re
import locale
from datetime import datetime, timedelta

#  de terceros
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import chardet

#  Django - Utilidades
from django.utils.timezone import localtime, get_current_timezone
from django.utils.dateformat import DateFormat
from django.contrib import messages

#  Django - Vistas y atajos
from django.views import View
from django.views.generic import TemplateView, DetailView
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator

#  Django - Modelos y respuestas HTTP
from django.db.models import Min, Max, Count
from django.http import HttpResponse, Http404, JsonResponse

# Modelos locales
from .models import *

nameWeb = "Fresh Fruit"

class DeleteSensorView(View):
    def post(self, request, sensor_id):
        """
        Elimina un sensor y todos los registros asociados.
        """
        sensor = get_object_or_404(Sensor, id=sensor_id)

        # Guardar información para mensaje
        sensor_info = f"Sensor {sensor.serial_number} ({sensor.device})"
        
        # Eliminar el sensor (se eliminan los registros en cascada)
        sensor.delete()

        messages.success(request, f"{sensor_info} and all related records were deleted successfully.")
        
        return JsonResponse({"status": "success", "message": f"{sensor_info} deleted successfully."})

class DeleteTripView(View):
    def post(self, request, trip_id):
        """
        Elimina un Trip y todas sus referencias en cascada (sensores y registros).
        """
        trip = get_object_or_404(Trip, id=trip_id)

        # Guardar información para mostrar mensaje
        trip_info = f"{trip.license_plate} ({trip.departure_date} - {trip.arrival_date})"
        
        # Eliminar el trip (se eliminan los sensores y registros en cascada)
        trip.delete()

        messages.success(request, f"Trip {trip_info} and all related data were deleted successfully.")
        
        return JsonResponse({"status": "success", "message": f"Trip {trip_info} deleted successfully."})

class DetailViewTrip(DetailView):
    model = Trip
    template_name = 'web/views/detail_trip.html'
    npaginas = 5
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trip = self.get_object()
        sensors = Sensor.objects.filter(trip=trip)

        # Configurar paginación
        paginator = Paginator(sensors, self.npaginas)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['trip'] = trip
        context['sensors'] = page_obj
        
        return context

class AddTrip(View):
    template_name = "web/views/add_trip.html"

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests and render the form with context data.
        """
        context = {
            "nameWeb": nameWeb,
            "title": "Add Trip",
            "products": ProductType.objects.all(),
            "microorganisms": Microorganism.objects.all(),
            "timezones": TimeZoneChoices.objects.all(),  # Pass timezone choices to the template
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to create a new Trip.
        """
        try:
            # Validar y obtener datos del formulario
            license_plate = request.POST.get('license_plate')
            shipment = request.POST.get('shipment')
            driver = request.POST.get('driver')
            origin = request.POST.get('origin')
            destination = request.POST.get('destination')
            departure_date = request.POST.get('departure_date')
            arrival_date = request.POST.get('arrival_date')
            departure_timezone_id = request.POST.get('departure_timezone')
            arrival_timezone_id = request.POST.get('arrival_timezone')
            product_id = request.POST.get('product')
            microorganism_id = request.POST.get('microorganisms')

            # Validar que todos los campos requeridos estén presentes
            if not all([license_plate, driver, origin, destination, departure_date, arrival_date, departure_timezone_id, arrival_timezone_id, product_id, microorganism_id]):
                raise ValueError("All fields are required.")

            # Obtener las relaciones de ProductType, Microorganism y TimeZoneChoices
            product = get_object_or_404(ProductType, id=product_id)
            microorganism = get_object_or_404(Microorganism, id=microorganism_id)
            departure_timezone = get_object_or_404(TimeZoneChoices, id=departure_timezone_id)
            arrival_timezone = get_object_or_404(TimeZoneChoices, id=arrival_timezone_id)

            # Crear y guardar el objeto Trip
            trip = Trip(
                license_plate=license_plate,
                driver=driver,
                shipment=shipment,
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                departure_timezone=departure_timezone,
                arrival_date=arrival_date,
                arrival_timezone=arrival_timezone,
                product=product,
                microorganism=microorganism,
            )
            trip.save()

            # Redirigir a la página principal después de guardar
            return redirect("home")
        except ValueError as ve:
            # Manejar errores de validación
            context = {
                "nameWeb": nameWeb,
                "title": "Add Trip",
                "products": ProductType.objects.all(),
                "microorganisms": Microorganism.objects.all(),
                "timezones": TimeZoneChoices.objects.all(),
                "error": f"Validation Error: {ve}",
            }
            return render(request, self.template_name, context)
        except Exception as e:
            # Manejar otros errores
            context = {
                "nameWeb": nameWeb,
                "title": "Add Trip",
                "products": ProductType.objects.all(),
                "microorganisms": Microorganism.objects.all(),
                "timezones": TimeZoneChoices.objects.all(),
                "error": f"Error saving trip: {e}",
            }
            return render(request, self.template_name, context)

class Trips(TemplateView):
    template_name = "web/views/trips.html"
    npaginas = 5
    def get_queryset(self):
        trips = Trip.objects.order_by('-arrival_date')
        paginator = Paginator(trips, self.npaginas)
        page = self.request.GET.get('page')
        return paginator.get_page(page)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total_trips = Trip.objects.count()
        unique_drivers = Trip.objects.values('driver').distinct().count()
        context.update({
            "nameWeb": nameWeb,
            "title": "Trips",
            "data": self.get_queryset(),
            "total_trips": total_trips,
            "unique_drivers": unique_drivers,
        })
        return context

class DetailViewSensor(DetailView):
    model = Sensor
    template_name = "web/views/detail.html"
    context_object_name = 'sensor'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        records = self.object.records.all().order_by('time')

        max_temp_param = Parameters.objects.filter(name='maxTemp').first()
        min_temp_param = Parameters.objects.filter(name='minTemp').first()

        max_temp_value = max_temp_param.value if max_temp_param else None
        min_temp_value = min_temp_param.value if min_temp_param else None

        if records.exists():
            min_temp = records.aggregate(Min('temperature'))['temperature__min']
            max_temp = records.aggregate(Max('temperature'))['temperature__max']
            total_records = records.count()
            min_date = records.aggregate(Min('time'))['time__min']
            max_date = records.aggregate(Max('time'))['time__max']
            time_difference = max_date - min_date
            decimal_days = time_difference.days + time_difference.seconds / 86400
            decimal_hours = time_difference.total_seconds() / 3600

            labels = [DateFormat(record.time).format('Y-m-d H:i:s') for record in records]
            data = [record.temperature for record in records]

            context.update({
                'min_temp': str(round(min_temp, 2)).replace(",", "."),
                'max_temp': str(round(max_temp, 2)).replace(",", "."),
                'total_records': total_records,
                'min_date': min_date,
                'max_date': max_date,
                'decimal_days': str(round(decimal_days, 2)).replace(",", "."),
                'decimal_hours': str(round(decimal_hours, 2)).replace(",", "."),
                'labels': labels,
                'data': data,
            })
        else:
            context.update({
                'min_temp': None,
                'max_temp': None,
                'total_records': 0,
                'min_date': None,
                'max_date': None,
                'decimal_days': 0,
                'decimal_hours': 0,
                'labels': [],
                'data': [],
            })

        context.update({
            'parameter_max_temp': max_temp_value,
            'parameter_min_temp': min_temp_value,
        })

        context["nameWeb"] = nameWeb
        context["title"] = f"Sensor Details {self.object.serial_number}"
        context['LimitTemperatureUp']   = Parameters.objects.filter(name='max_temp').first().value
        context['LimitTemperatureDown'] = Parameters.objects.filter(name='min_temp').first().value
       
        return context


class RecordAdd(View):
    template_name = "web/views/add_record.html"

    def get(self, request, trip_id, *args, **kwargs):
        trip = get_object_or_404(Trip, id=trip_id)
        context = {
            "nameWeb": "Sensor Data Upload",
            "title": "Add Sensor Data",
            "trip": trip,
            "sensor_locations": SensorLocation.objects.all(),
            "pallet_locations": PalletLocation.objects.all(),
        }
        return render(request, self.template_name, context)

    def post(self, request, trip_id, *args, **kwargs):
        trip = get_object_or_404(Trip, id=trip_id)
        uploaded_file = request.FILES.get("data_file")
        pallet_location_id = request.POST.get("pallet_location")
        sensor_position_id = request.POST.get("sensor_position")
        sensor_tag = request.POST.get("sensor_tag", "").strip()

        if not uploaded_file:
            return self.get_context_with_error(trip, "No file uploaded!")

        if not pallet_location_id or not sensor_position_id:
            return self.get_context_with_error(trip, "Pallet Location and Sensor Position are required!")

        try:
            raw_data = uploaded_file.read()
            detected_encoding = chardet.detect(raw_data)["encoding"] or "utf-8"
            decoded_file = io.StringIO(raw_data.decode(detected_encoding))

            file_extension = uploaded_file.name.split(".")[-1].lower()

            # Extraer información del sensor
            sensor_data = self.extract_sensor_info(decoded_file, file_extension)
            if not sensor_data:
                return self.get_context_with_error(trip, "Failed to extract sensor information!")

            # Crear o actualizar el sensor
            pallet_location = get_object_or_404(PalletLocation, id=pallet_location_id)
            sensor_position = get_object_or_404(SensorLocation, id=sensor_position_id)
            estado = get_object_or_404(Status, state='Pending')

            timezone = None
            if sensor_data.get("timezone"):
                timezone = TimeZoneChoices.objects.filter(value=sensor_data["timezone"]).first()

            sensor, created = Sensor.objects.get_or_create(
                serial_number=sensor_data["serial_number"],
                trip=trip,
                defaults={
                    "device": sensor_data["device"],
                    "tag": sensor_tag,
                    "pallet_location": pallet_location,
                    "sensor_position": sensor_position,
                    "timezone": timezone,
                    "status": estado
                },
            )

            if not created:
                sensor.device = sensor_data["device"]
                if sensor_tag and sensor.tag != sensor_tag:
                    sensor.tag = sensor_tag
                sensor.pallet_location = pallet_location
                sensor.sensor_position = sensor_position
                sensor.timezone = timezone
                sensor.save()

            # Extraer y guardar registros de temperatura
            decoded_file.seek(0)  # Volver al inicio del archivo
            records, last = self.extract_temperature_records(decoded_file, file_extension, trip, sensor, sensor_data["timezone"])

            if records:
                Record.objects.bulk_create(records, batch_size=1000)
            
            success_message = f"Sensor {'created' if created else 'updated'} successfully. Imported {len(records)} records."
            return render(request, self.template_name, {
                "nameWeb": "Sensor Data Upload",
                "title": "Add Sensor Data",
                "trip": trip,
                "sensor_locations": SensorLocation.objects.all(),
                "pallet_locations": PalletLocation.objects.all(),
                "success_message": success_message,
                "po": last
            })

        except Exception as e:
            return self.get_context_with_error(trip, f"Unexpected error: {e}")

    def extract_sensor_info(self, file, file_extension):
        """Extrae la información del sensor del archivo CSV o TXT"""
        sensor_info = {
            "serial_number": "Unknown",
            "device": "Unknown",
            "timezone": None,
        }

        if file_extension == "csv":
            reader = csv.reader(file)
            for row in reader:
                if len(row) < 2:
                    continue
                key, value = row[0].strip(), row[1].strip()
                if key.startswith("Modelo de dispositivo") or key.startswith("Model"):
                    sensor_info["device"] = value
                elif key.startswith("Número de serie")  or key.startswith("S/N") :
                    sensor_info["serial_number"] = value
                elif key.startswith("Zona horaria")  or key.startswith("Timezone"):
                    sensor_info["timezone"] = value
                elif key.lower().startswith("no."):  # Fin de los metadatos
                    break

        elif file_extension == "txt":
            for line in file:
                line = line.strip()
                if line.startswith("Modelo de dispositivo:") or line.startswith("Model :"):
                    sensor_info["device"] = line.split(":", 1)[1].strip()
                elif line.startswith("Número de serie:") or line.startswith("S/N :"):
                    sensor_info["serial_number"] = line.split(":", 1)[1].strip()
                elif line.startswith("Zona horaria:") or line.startswith("Timezone :") :
                    sensor_info["timezone"] = line.split(":", 1)[1].strip()
                elif line.startswith("No."):  # Fin de los metadatos
                    break

        return sensor_info

    def extract_temperature_records(self, file, file_extension, trip, sensor, timezone):
        """Extrae registros de temperatura del archivo CSV o TXT"""
        records = []
        current_tz = get_current_timezone()
        errors = []
        is_data_section = False

        tz = str(timezone)

        departure_date  = str(trip.departure_date) 
        departure_tz   = str(trip.departure_timezone.value)

        arrival_date   = str(trip.arrival_date)
        arrival_tz     = str(trip.arrival_timezone.value)

        # Verificar si timezone es un diccionario, un objeto o None
        
        n_departure_date = self.convertir_zona_horaria(departure_date, departure_tz, tz)
        n_arrival_date = self.convertir_zona_horaria(arrival_date, arrival_tz, tz)
        
        last = departure_date +' ### '+ departure_tz + ' ###'+ tz +' === '+ n_departure_date.strftime("%Y-%m-%d %H:%M:%S")

        last = last +str(arrival_date) +' ### '+str( arrival_tz) + '### '+ tz +' === ' +n_arrival_date.strftime("%Y-%m-%d %H:%M:%S")
        
        if file_extension == "csv":
            reader = csv.reader(file)
            records = []
            
            for row in reader:
                try:
                    # Validar que la fila tenga al menos 3 columnas
                    if len(row) < 3:
                        print(f"Ignorando fila incompleta: {row}")  # Diagnóstico
                        continue

                    # Limpiar espacios extra en cada columna
                    number = int(row[0].strip())
                    time_str = row[1].strip()
                    temperature = float(row[2].strip())

                    # Formatear la hora correctamente
                    time_str = time_str.replace("a. m.", "AM").replace("p. m.", "PM").strip()
                    naive_time = datetime.strptime(time_str, "%d/%m/%Y %I:%M:%S %p")
                        
                    if (naive_time <= n_arrival_date) and (naive_time >= n_departure_date):
                        records.append(Record(
                            sensor=sensor,
                            number=number,
                            time=naive_time,
                            temperature=temperature
                        ))

                except ValueError as e:
                    print(f"Error procesando fila {row}: {e}")  # Diagnóstico

                
        elif file_extension == "txt":
            
            for line in file:
                line = line.strip()
                if line.lower().startswith("no."):
                    is_data_section = True
                    continue
                if is_data_section:
                    try:
                        parts = [part.strip() for part in line.split() if part.strip()]
                        if len(parts) < 3:
                            continue

                        number = int(parts[0])
                        time_str = f"{parts[1]} {parts[2]} {parts[-3]} {parts[-2]}"
                        temperature = float(parts[-1])

                        time_str = time_str.replace("a. m.", "AM").replace("p. m.", "PM").strip()
                        naive_time = datetime.strptime(time_str, "%d/%m/%Y %I:%M:%S %p")
                        
                        if (naive_time <= n_arrival_date) and (naive_time >= n_departure_date):
                            records.append(Record(
                                sensor=sensor,
                                number=number,
                                time=naive_time,
                                temperature=temperature
                            ))
                        
                    except Exception as e:
                        print(f"Error parsing TXT line '{line}': {e}")
            #last = last +' len: '+ str(len(records))
        last = ''
        return records , last

    
    def convertir_zona_horaria(self, fecha_str, zona_origen, zona_destino):

        # Extraer el formato UTC ±HH:MM usando regex
        match_origen = re.match(r"UTC ([+-])(\d{2}):(\d{2})", zona_origen)
        match_destino = re.match(r"UTC ([+-])(\d{2}):(\d{2})", zona_destino)

        if not match_origen or not match_destino:
            raise ValueError(f"Formato de zona horaria inválido: {zona_origen} o {zona_destino}")

        # Extraer valores de la zona horaria original y destino
        signo_origen, horas_origen, minutos_origen = match_origen.groups()
        signo_destino, horas_destino, minutos_destino = match_destino.groups()

        # Calcular el desplazamiento en minutos
        offset_origen = int(signo_origen + horas_origen) * 60 + int(signo_origen + minutos_origen)
        offset_destino = int(signo_destino + horas_destino) * 60 + int(signo_destino + minutos_destino)

        # Diferencia de tiempo entre la zona de origen y destino
        diferencia_tiempo = offset_destino - offset_origen

        # Convertir string a datetime (sin zona horaria)
        fecha_dt = datetime.strptime(fecha_str[:19], "%Y-%m-%d %H:%M:%S")

        # Aplicar la diferencia de tiempo
        fecha_convertida = fecha_dt + timedelta(minutes=diferencia_tiempo)

        return fecha_convertida


    def get_context_with_error(self, trip, error_message):
        """Devuelve el contexto con un mensaje de error"""
        return render(self.template_name, {
            "nameWeb": "Sensor Data Upload",
            "title": "Add Sensor Data",
            "trip": trip,
            "sensor_locations": SensorLocation.objects.all(),
            "pallet_locations": PalletLocation.objects.all(),
            "error": error_message,
        })


class AnalysisViewSensor(DetailView):
    model = Sensor
    template_name = "web/views/analysis.html"
    context_object_name = 'sensor'
    
    def get_cifra(self):
        """
        Recupera el valor de 'cifra' desde el modelo Parameters.
        """
        cifra_param = Parameters.objects.filter(name='cifraFront').first()
        if cifra_param:
            return int(cifra_param.value)
        return 10  # Valor por defecto si no se encuentra

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        records = self.object.records.order_by('time')
        cifra = self.get_cifra()
          # Definir la cantidad de cifras significativas
        if records.exists():

            TemLimUp  = Parameters.objects.filter(name='max_temp').first().value
            TemLimLow = Parameters.objects.filter(name='min_temp').first().value
            pTemLimUp = Parameters.objects.filter(name='time_fraccion_max_temp').first().value
            pTemLimLow = Parameters.objects.filter(name='time_fraccion_min_temp').first().value

            stats = records.aggregate(
                min_temp=Min('temperature'),
                max_temp=Max('temperature'),
                total_records=Count('id'),
                min_date=Min('time'),
                max_date=Max('time'),
            )
            min_temp = stats['min_temp']
            max_temp = stats['max_temp']
            total_records = stats['total_records']
            min_date = stats['min_date']
            max_date = stats['max_date']

            # Calcular diferencia de tiempo
            time_difference = max_date - min_date
            decimal_days = np.round(time_difference.days + time_difference.seconds / 86400, cifra)
            decimal_hours = np.round(time_difference.total_seconds() / 3600, cifra)

            # Crear DataFrame desde los registros
            values = records.values_list('number', 'time', 'temperature')
            df = pd.DataFrame(list(values), columns=['number', 'time', 'temperature'])

            pTemUp = np.round((sum(df['temperature'] > TemLimUp) / len(df['temperature'])) * 100, 2)
            pTemLow = np.round((sum(df['temperature'] < TemLimLow) / len(df['temperature'])) * 100,2)

            if pTemUp > pTemLimUp:
                message = 'SHIPMENT REJECTED'
                description = f"The percentage of temperatures exceeding the allowed limit ({TemLimUp}) reached {pTemUp}%, surpassing the permitted threshold of {pTemLimUp}."
                do = "api_generate_temperatures_up"
                estado= get_object_or_404(Status, state='Rejected')
                self.object.status = estado
            elif pTemLow > pTemLimLow:
                message = 'SHIPMENT ACCEPTED'
                description = f"SHIPMENT ACCEPTED: For more than {pTemLow}% of the shipping time, the temperature remained below the lower threshold of {TemLimLow}."
                do = "api_generate_temperatures_low"
                estado= get_object_or_404(Status, state='Approved')
                self.object.status= estado
            else:
                message = 'SHIPMENT ANALYSIS'
                description = "The algorithm and the mathematical model are being executed to analyze the shipment."
                do = "graficar_algoritmo"
                estado= get_object_or_404(Status, state='Analysis')
                self.object.status = estado
            # Guardar el estado actualizado
            self.object.save()
            # Actualizar contexto
            context.update({
                "min_temp": str(round(min_temp, 2)).replace(",", "."),
                "max_temp": str(round(max_temp, 2)).replace(",", "."),
                "total_records": total_records,
                "min_date": min_date,
                "max_date": max_date,
                "decimal_days": str(round(decimal_days, 2)).replace(",", "."),
                "decimal_hours": str(round(decimal_hours, 2)).replace(",", "."),
                "message":message,
                "description":description,
                "do": do, 
                "object": self.object
            })

        else:
            context.update({
                "min_temp": None,
                "max_temp": None,
                "total_records": 0,
                "min_date": None,
                "max_date": None,
                "decimal_days": 0,
                "decimal_hours": 0,
                "message":'NO DATA',
                "description":'CHECK DATABASE',
                "do":"nothing"
            })

        context["nameWeb"] = nameWeb
        context["title"] = f"Sensor Details {self.object.serial_number}"
        context['LimitTemperatureUp']   = Parameters.objects.filter(name='max_temp').first().value
        context['LimitTemperatureDown'] = Parameters.objects.filter(name='min_temp').first().value
       
        return context

class Analysis:
    def __init__(self, sensor=None):
        self.sensor = sensor  # Asigna el sensor al atributo de la clase
        self.cifra = self.get_cifra() # Recupera el valor de 'cifra' desde Parameters
        self.ecuacion = self.get_equation_parameters()
    def get_cifra(self):
        """
        Recupera el valor de 'cifra' desde el modelo Parameters.
        """
        cifra_param = Parameters.objects.filter(name='cifra').first()
        if cifra_param:
            return int(cifra_param.value)
        return 10  # Valor por defecto si no se encuentra
    def get_equation_parameters(self):
        if not self.sensor or not self.sensor.trip:
            raise ValueError("Sensor or associated trip is required to fetch equation parameters.")

        product = self.sensor.trip.product
        microorganism = self.sensor.trip.microorganism

        equation = Equation.objects.filter(product=product).filter(microorganism=microorganism).first()
        if not equation:
            raise ValueError(f"No equation found for product '{product}' and microorganism '{microorganism}'.")

        return {
            'LPD_form': equation.LPD_form,
            'LPD_parameters': equation.LPD_parameters,
            'b_form': equation.b_form,
            'b_parameters': equation.b_parameters,
            'n_form': equation.n_form,
            'n_parameters': equation.n_parameters,
            'Tc': equation.Tc,
            'dtu': equation.dtu,
        }
          
    def get_context_data(self, **kwargs):
        # Usa self.sensor para obtener datos específicos
        if not self.sensor:
            raise ValueError("Sensor is required to generate context data.")
        
        records = self.sensor.records.order_by('time')
        description = ""
        product = self.sensor.trip.product.name
        microorganism = self.sensor.trip.microorganism.name
        
        if records.exists():
            # Calcular estadísticas básicas
            stats = records.aggregate(
                min_temp=Min('temperature'),
                max_temp=Max('temperature'),
                total_records=Count('id'),
                min_date=Min('time'),
                max_date=Max('time'),
            )
            min_temp = stats['min_temp']
            max_temp = stats['max_temp']
            total_records = stats['total_records']
            min_date = stats['min_date']
            max_date = stats['max_date']

            # Calcular diferencia de tiempo
            time_difference = max_date - min_date
            decimal_days = np.round(time_difference.days + time_difference.seconds / 86400, self.cifra)
            decimal_hours = np.round(time_difference.total_seconds() / 3600, self.cifra)

            # Crear DataFrame desde los registros
            values = records.values_list('number', 'time', 'temperature')
            df = pd.DataFrame(list(values), columns=['number', 'time', 'temperature'])

            # Calcular columnas vectorizadas
            df["t_h"] = (pd.to_datetime(df["time"]) - min_date).dt.total_seconds() / 3600
            df["t"] = df["t_h"] / 24
            df["dt"] = df["t"].diff().fillna(0)
            df["mT"] = (df["temperature"] + df["temperature"].shift(1)) / 2

            # Constantes
            #k, a, =  1.30, -0.14

            parm = ast.literal_eval(self.ecuacion['LPD_parameters'])
            lpa_form = self.ecuacion['LPD_form']
            k = float(parm['k'])
            a = float(parm['a'])
            variables = {
                'k': k,
                'a': a,
                'mT': df['mT']
            }
            
            # Calcular LPD y LPA
            #df['LPD'] = np.round(k * (df['mT'] ** a), self.cifra).where(df['mT'].notna(), np.nan)
            
            if product == "UNTREATED" and microorganism =="MOLDS_YEASTS":
                df['LPA'] = np.ones(len(df['dt']))
            else:
                df['LPD'] = np.round(eval(lpa_form, {"__builtins__": None}, variables), self.cifra).where(df['mT'].notna(), np.nan)

                df['LPA'] = (df['dt'] / df['LPD']).cumsum()

            # calculos de LPA >=1 
            # Constantes para calculos LPA >=1
            # Recuperar los parámetros de la ecuación
            
            b_param = eval(self.ecuacion['b_parameters'])
            n_param = eval(self.ecuacion['n_parameters'])
            
            k_b= float(b_param['k_b'])
            a_b= float(b_param['a_b'])
            k_n= float(n_param['k_n'])
            a_n= float(n_param['a_n'])

            #Tc = 4
            tc_str = self.ecuacion['Tc']  # Esto devuelve "{'Tc': 4.0}"
            tc_dict = ast.literal_eval(tc_str)  # Convierte la cadena a un diccionario
            Tc = float(tc_dict['Tc']) # Accede al valor numérico

            #dtu =  1 / (24 * 60 * 60)
            dtu_str = self.ecuacion['dtu'] 
            dtu_dict = eval(dtu_str)
            dtu = dtu_dict['dtu']

            #calculo de bc y nc

            b_form = self.ecuacion['b_form']
            n_form = self.ecuacion['n_form']
            
            variables_b_form_Tc = {
                'k_b': k_b,
                'a_b': a_b,
                'mT': Tc,
                'np': np 
            }

            variables_n_form_Tc = {
                'k_n': k_n,
                'a_n': a_n,
                'mT': Tc,
                'np': np 
            }

            #aux= str(b_form+str(variables_b_form_Tc) )
            aux='LPA, RPI, mRPI, and Temperature Analysis'
            #bc = k_b * np.log(Tc) + a_b
            #nc = k_n * (Tc ** a_n)

            bc = np.round(eval(b_form, {"__builtins__": None}, variables_b_form_Tc), self.cifra)
            nc = np.round(eval(n_form, {"__builtins__": None}, variables_n_form_Tc), self.cifra)

            # Crear máscara
            mask = df.index[df['LPA'] >= 1]
            
            if len(mask) == 0: # LPA < 1
                max_position = df['LPA'].idxmax()
                t_h_at_max_lpa = str(round(df['t_h'].loc[max_position],2))+' hours'  # valor th de LPA <1
                t_h_at_max_lpa_porcent = str(round(float(df['LPA'].iloc[max_position])*100,0))+ ' %'
                message = 'SHIPMENT ACCEPTED'
                df['RPI'] = pd.NA
                df['mRPI'] = pd.NA
            if len(mask) > 1:
                t_h_at_max_lpa = str(round(df['t_h'].iloc[mask[0]],2))+' hours'  # valor th de LPA =1
                t_h_at_max_lpa_porcent = str(round(float(df['LPA'].iloc[mask[0]])*100,0))+ ' %'
                i = mask[1]
                mT_2 = df.at[i, 'mT']
                dt_2 = df.at[i, 'dt']

                variables_b_form = {
                    'k_b': k_b,
                    'a_b': a_b,
                    'mT': mT_2,
                    'np': np 
                }
                variables_n_form = {
                    'k_n': k_n,
                    'a_n': a_n,
                    'mT': mT_2,
                    'np': np 
                }

                if pd.notna(mT_2) and pd.notna(dt_2):
                    #b_2 = round(k_b * np.log(mT_2) + a_b, self.cifra)
                    b_2 = np.round(eval(b_form, {"__builtins__ns__": None}, variables_b_form), self.cifra)
                    #n_2 = round(k_n * (mT_2 ** a_n), self.cifra)
                    n_2 = np.round(eval(n_form, {"__builtins__": None}, variables_n_form), self.cifra)
                    df.at[i, 'b'] = b_2
                    df.at[i, 'n'] = n_2

                    # Modelo original
                    logN_2 = round(b_2 * (( dt_2 +(1/24) )** n_2), self.cifra)
                    df.at[i, 'logN'] = logN_2

                    # Modelo compuesto
                    logNc_2 = round(bc * ( (dt_2+(1/24) )** nc), self.cifra)
                    df.at[i, 'logNc'] = logNc_2

                    # RPI
                    RPI_2 = round(logN_2 / logNc_2, self.cifra) if logNc_2 > 0 else pd.NA
                    df.at[i, 'RPI'] = RPI_2
                    max_temp = str(RPI_2)+'-'+str(i)+'-'+str(logN_2)+'-'+str(logNc_2)    
            # Procesar posiciones 3 en adelante  
            if len(mask) > 2:
                indices = mask[2:]
                for i in indices:
                    mT = df['mT'].iloc[i]
                    dt = df['dt'].iloc[i]
                    variables_b_form = {
                        'k_b': k_b,
                        'a_b': a_b,
                        'mT': mT,
                        'np': np 
                    }
                    variables_n_form = {
                        'k_n': k_n,
                        'a_n': a_n,
                        'mT': mT,
                        'np': np 
                    }
                    b = np.round(eval(b_form, {"__builtins__ns__": None}, variables_b_form), self.cifra)
                    n = np.round(eval(n_form, {"__builtins__": None}, variables_n_form), self.cifra)
                    
                    #b = round(k_b * np.log(mT) + a_b, self.cifra)
                    #n = round(k_n * (mT ** a_n), self.cifra)

                    df.at[i, 'b'] = b
                    df.at[i, 'n'] = n

                    # Modelo original
                    prev_logN = df['logN'].iloc[i - 1] 
                    
                    tx = round((prev_logN / b) ** (1 / n) , self.cifra)
                    Na = round(b * ((tx + dtu) ** n) , self.cifra)
                    Nb = round(b * ((tx - dtu) ** n) , self.cifra)
                    mu = round((Na - Nb) / dtu, self.cifra)
                    df.at[i, 'tx'] = tx
                    df.at[i, 'Na'] = Na
                    df.at[i, 'Nb'] = Nb
                    df.at[i, 'mu'] = mu

                    logN = round(mu * dt  + prev_logN , self.cifra)
                    df.at[i, 'logN'] = logN

                    # Modelo compuesto
                    prev_logNc = df['logNc'].iloc[i - 1] 
                    
                    txc = round((prev_logNc / bc) ** (1 / nc) , self.cifra)
                    Nac = round(bc * ((txc + dtu) ** nc) , self.cifra)
                    Nbc = round(bc * ((txc - dtu) ** nc) , self.cifra)
                    muc = round((Nac - Nbc) / dtu, self.cifra)
                    df.at[i, 'txc'] = txc
                    df.at[i, 'Nac'] = Nac
                    df.at[i, 'Nbc'] = Nbc
                    df.at[i, 'muc'] = muc

                    logNc = round(muc * dt  + prev_logNc , self.cifra)
                    df.at[i, 'logNc'] = logNc

                    # RPI y mRPI  
                    RPI = round(logN / logNc, self.cifra) if logNc > 0 else pd.NA
                    df.at[i, 'RPI'] = RPI
                    
                    # Calcular mRPI si existen suficientes registros y el denominador no es 0, NaN o Inf
                    # Calcular mRPI si existen suficientes registros y el denominador no es 0, NaN o Inf
                    if (
                        pd.notna(logN) and 
                        pd.notna(df['logN'].iloc[i - 120]) and 
                        pd.notna(logNc) and 
                        pd.notna(df['logNc'].iloc[i - 120])
                    ):
                        denominator = logNc - df['logNc'].iloc[i - 120]

                        if denominator == 0 or pd.isna(denominator) or np.isinf(denominator):
                            mRPI = pd.NA  # O puedes asignar otro valor como 0
                        else:
                            mRPI = round((logN - df['logN'].iloc[i - 120]) / denominator, self.cifra)
                    else:
                        mRPI = pd.NA

                    df.at[i, 'mRPI'] = mRPI
                    #df.at[i, 'RPI'] = logNc
                    #df.at[i, 'mRPI'] = logN
                
                ultimo_valor = mask[-1]
                if df.loc[ultimo_valor, 'RPI']  <= 1:
                    message = 'SHIPMENT ACCEPTED'
                    description = 'RPI <= 1'
                else:
                    message = 'SHIPMENT REJECTED'
                    description = 'RPI > 1'

            # Convertir valores de LPA > 1 a pd.NA
            if product == "UNTREATED" and microorganism =="MOLDS_YEASTS":
                df['LPA'] = 0
            else:
                df.loc[df['LPA'] > 1, 'LPA'] = pd.NA
            
            '''
            df['dtu'] = dtu
            df['bc'] = bc
            df['nc'] = nc
            '''
        # Simula datos de ejemplo (ajusta según tu implementación real)
        '''
        context = {
            't': df['t_h'] , # Reemplaza con tus datos reales
            'LPA': df['LPA'].tolist(),
            'RPI': df['RPI'].tolist(),
            'mRPI': df['mRPI'].tolist(),
            'T': df['temperature'],
            'title': aux,
            't_h_at_max_lpa': t_h_at_max_lpa,
            't_h_at_max_lpa_porcent': t_h_at_max_lpa_porcent,
            'message': message,
            'description': description,
            'mT': df['mT'],
            'b': df['b'],
            'n': df['n'],
            'tx': df['tx'],
            'Na': df['Na'],
            'Nb': df['Nb'],
            'mu': df['mu'],
            'logN': df['logN'],
            'bc': df['bc'],
            'nc': df['nc'],
            'txc': df['txc'],
            'Nac': df['Nac'],
            'Nbc': df['Nbc'],
            'muc': df['muc'],
            'logNc': df['logNc']
        }
        '''
        context = {
            't': df['t_h'] , # Reemplaza con tus datos reales
            'LPA': df['LPA'].tolist(),
            'RPI': df['RPI'].tolist(),
            'mRPI': df['mRPI'].tolist(),
            'T': df['temperature'],
            'title': aux,
            't_h_at_max_lpa': t_h_at_max_lpa,
            't_h_at_max_lpa_porcent': t_h_at_max_lpa_porcent,
            'message': message,
            'description': description
        }
        return context

    def generate_plotly_graph(self, t, LPA, RPI, mRPI, T, title):
        """
        Genera un gráfico usando Plotly basado en los datos proporcionados.

        :param t: Lista de tiempos (eje X).
        :param LPA: Lista de datos para LPA.
        :param RPI: Lista de datos para RPI.
        :param mRPI: Lista de datos para mRPI.
        :param T: Lista de datos de temperatura.
        :return: Figura Plotly.
        """
        # Crear una figura con múltiples trazas (líneas)
        # Definir trazos y colores
        traces = [
            {"name": "LPA", "y": LPA, "color": "purple", "dash": "solid", "yaxis": "y1"},
            {"name": "RPI", "y": RPI, "color": "purple", "dash": "dot", "yaxis": "y1"},
            {"name": "mRPI", "y": mRPI, "color": "orange", "dash": "dot", "yaxis": "y1"},
            {"name": "Temperature", "y": T, "color": "green", "dash": "solid", "yaxis": "y2"}
        ]

        # Obtener los valores de TemLimLow y TemLimUp desde los parámetros
        tem_lim_low_param = Parameters.objects.filter(name='min_temp').first()
        tem_lim_up_param = Parameters.objects.filter(name='max_temp').first()
        if not tem_lim_low_param or not tem_lim_up_param:
            return JsonResponse({"error": "Temperature limit parameters not found."}, status=404)

        TemLimLow = tem_lim_low_param.value
        TemLimUp = tem_lim_up_param.value


        # Crear figura y agregar trazos
        fig = go.Figure()
        for trace in traces:
            fig.add_trace(go.Scatter(
                x=t, y=trace["y"],
                mode="lines",
                name=trace["name"],
                line=dict(color=trace["color"], dash=trace["dash"]),
                yaxis=trace["yaxis"]
            ))

        # Trazar el límite superior de temperatura
        fig.add_trace(go.Scatter(
            x=t, 
            y=[TemLimUp] * len(t), 
            mode='lines',
            name='TemLimUp',
            line=dict(color='red', dash='dash'),
            yaxis=trace["yaxis"]
        ))
        # Trazar el límite superior de temperatura
        fig.add_trace(go.Scatter(
            x=t, 
            y=[TemLimLow] * len(t), 
            mode='lines',
            name='TemLimLow',
            line=dict(color='blue', dash='dash'),
            yaxis=trace["yaxis"]
        ))
        # Configuración del diseño
        layout = dict(
            title=dict(
                text=title,
                font=dict(size=28)
            ),
            xaxis=dict(
                title="Time (h)",
                range=[0, 30],
                dtick=5,
                showgrid=True,
                zeroline=False,
                titlefont=dict(size=28),
                tickfont=dict(size=24)
            ),
            yaxis=dict(
                title="LPA, RPI and mRPI",
                range=[0, 3],
                dtick=1,
                titlefont=dict(color="purple", size=28),
                tickfont=dict(size=24, color="purple"),
                showgrid=True,
                zeroline=False,
                side="left"
            ),
            yaxis2=dict(
                title="Temperature (°C)",
                range=[0, 21],
                dtick=3,
                titlefont=dict(color="green", size=28),
                tickfont=dict(size=24, color="green"),
                overlaying="y",
                side="right",
                showgrid=False,
                zeroline=False
            ),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.2,
                xanchor="center",
                x=0.5,
                font=dict(size=24)
            ),
            template="plotly_white",
            width=1280,
            height=720
        )
        fig.update_layout(layout)
        # Configurar el fondo y las líneas de la cuadrícula
        fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='gray')
        fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='gray')

        return fig

def api_generate_graph(request, pk):
    """
    Genera un gráfico para el sensor especificado por su ID y lo devuelve como JSON con texto y la imagen en base64.
    """
    try:
        sensor = Sensor.objects.get(id=pk)
    except Sensor.DoesNotExist:
        return JsonResponse({"error": "Sensor not found"}, status=404)

    analysis_view = Analysis(sensor=sensor)
    context = analysis_view.get_context_data()

    fig = analysis_view.generate_plotly_graph(
        t=context['t'],
        LPA=context['LPA'],
        RPI=context['RPI'],
        mRPI=context['mRPI'],
        T=context['T'],
        title=context['title']
    )

    # Guardar la figura en un buffer como una imagen PNG
    buf = io.BytesIO()
    fig.write_image(buf, format='png')
    buf.seek(0)

    # Codificar la imagen en base64
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    # Determinar el estado según el mensaje del contexto
    status_name = None
    if context['message'] == 'SHIPMENT REJECTED':
        status_name = 'Rejected'
    elif context['message'] == 'SHIPMENT ACCEPTED':
        status_name = 'Approved'

    # Asignar estado al sensor si se determina un nuevo estado
    if status_name:
        try:
            estado = Status.objects.get(state=status_name)
            if sensor.status != estado:  # Evita actualizar si ya tiene el estado correcto
                sensor.status = estado
                sensor.save()
        except Status.DoesNotExist:
            return JsonResponse({"error": f"Status '{status_name}' not found"}, status=500)

    # Retornar imagen codificada y texto en JSON
    return JsonResponse({
        "image": image_base64,
        "t_h_at_max_lpa": context['t_h_at_max_lpa'],
        "t_h_at_max_lpa_porcent": context['t_h_at_max_lpa_porcent'],
        "message": context['message'],
        "description": context['description']
    })

def api_generate_temperatures_up(request, pk):
    """
    Genera un gráfico de Temperatura vs Tiempo en horas para el sensor especificado.
    Muestra las temperaturas registradas y el límite superior de temperatura (TemLimUp).
    """
    try:
        # Obtener el sensor por su ID
        sensor = get_object_or_404(Sensor, id=pk)

        # Obtener los registros asociados al sensor
        records = sensor.records.order_by('time')
        if not records.exists():
            return JsonResponse({"error": "No records found for the specified sensor."}, status=404)

        # Obtener el valor de TemLimUp desde los parámetros
        tem_lim_up_param = Parameters.objects.filter(name='max_temp').first()
        if not tem_lim_up_param:
            return JsonResponse({"error": "TemLimUp parameter not found."}, status=404)

        TemLimUp = tem_lim_up_param.value

        # Extraer datos para el gráfico
        times = [(record.time - records.first().time).total_seconds() / 3600 for record in records]
        temperatures = [record.temperature for record in records]

        # Crear el gráfico con Plotly
        fig = go.Figure()

        # Trazar las temperaturas registradas
        fig.add_trace(go.Scatter(
            x=times, 
            y=temperatures, 
            mode='lines',
            name='Temperature',
            line=dict(color='blue')
        ))

        # Trazar el límite superior de temperatura
        fig.add_trace(go.Scatter(
            x=times, 
            y=[TemLimUp] * len(times), 
            mode='lines',
            name='TemLimUp',
            line=dict(color='red', dash='dash')
        ))

        # Configurar el diseño del gráfico
        fig.update_layout(
            title="Temperature vs Time (Hours)",
            xaxis=dict(
                title="Time (hours)",
                showgrid=True,
                zeroline=False
            ),
            yaxis=dict(
                title="Temperature (°C)",
                showgrid=True,
                zeroline=False
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            ),
            template="plotly_white",
            width=1280,
            height=720
        )

        # Guardar la figura en un buffer como una imagen PNG
        buf = io.BytesIO()
        fig.write_image(buf, format='png')
        buf.seek(0)

        # Codificar la imagen en base64
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')

        # Retornar imagen codificada y texto en JSON
        return JsonResponse({
            "message": "Temperature vs Time graph generated successfully.",
            "image": image_base64
        })

    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)

def api_generate_temperatures_low(request, pk):
    """
    Genera un gráfico de Temperatura vs Tiempo en horas para el sensor especificado.
    Muestra las temperaturas registradas y el límite inferior de temperatura (TemLimLow).
    """
    try:
        # Obtener el sensor por su ID
        sensor = get_object_or_404(Sensor, id=pk)

        # Obtener los registros asociados al sensor
        records = sensor.records.order_by('time')
        if not records.exists():
            return JsonResponse({"error": "No records found for the specified sensor."}, status=404)

        # Obtener el valor de TemLimLow desde los parámetros
        tem_lim_low_param = Parameters.objects.filter(name='min_temp').first()
        if not tem_lim_low_param:
            return JsonResponse({"error": "TemLimLow parameter not found."}, status=404)

        TemLimLow = tem_lim_low_param.value

        # Extraer datos para el gráfico
        times = [(record.time - records.first().time).total_seconds() / 3600 for record in records]
        temperatures = [record.temperature for record in records]

        # Crear el gráfico con Plotly
        fig = go.Figure()

        # Trazar las temperaturas registradas
        fig.add_trace(go.Scatter(
            x=times, 
            y=temperatures, 
            mode='lines',
            name='Temperature',
            line=dict(color='blue')
        ))

        # Trazar el límite inferior de temperatura
        fig.add_trace(go.Scatter(
            x=times, 
            y=[TemLimLow] * len(times), 
            mode='lines',
            name='TemLimLow',
            line=dict(color='green', dash='dash')
        ))

        # Configurar el diseño del gráfico
        fig.update_layout(
            title="Temperature vs Time (Hours)",
            xaxis=dict(
                title="Time (hours)",
                showgrid=True,
                zeroline=False
            ),
            yaxis=dict(
                title="Temperature (°C)",
                showgrid=True,
                zeroline=False
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            ),
            template="plotly_white",
            width=1280,
            height=720
        )

        # Guardar la figura en un buffer como una imagen PNG
        buf = io.BytesIO()
        fig.write_image(buf, format='png')
        buf.seek(0)

        # Codificar la imagen en base64
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')

        # Retornar imagen codificada y texto en JSON
        return JsonResponse({
            "message": "Temperature vs Time graph generated successfully.",
            "image": image_base64
        })

    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)

def api_generate_temperatures_limits(request, pk):
    """
    Genera un gráfico de Temperatura vs Tiempo en horas para el sensor especificado.
    Muestra las temperaturas registradas, el límite inferior de temperatura (TemLimLow) y el límite superior (TemLimUp).
    """
    try:
        # Obtener el sensor por su ID
        sensor = get_object_or_404(Sensor, id=pk)

        # Obtener los registros asociados al sensor
        records = sensor.records.order_by('time')
        if not records.exists():
            return JsonResponse({"error": "No records found for the specified sensor."}, status=404)

        # Obtener los valores de TemLimLow y TemLimUp desde los parámetros
        tem_lim_low_param = Parameters.objects.filter(name='min_temp').first()
        tem_lim_up_param = Parameters.objects.filter(name='max_temp').first()
        if not tem_lim_low_param or not tem_lim_up_param:
            return JsonResponse({"error": "Temperature limit parameters not found."}, status=404)

        TemLimLow = tem_lim_low_param.value
        TemLimUp = tem_lim_up_param.value

        # Extraer datos para el gráfico
        times = [(record.time - records.first().time).total_seconds() / 3600 for record in records]
        temperatures = [record.temperature for record in records]

        # Crear el gráfico con Plotly
        fig = go.Figure()

        # Trazar las temperaturas registradas
        fig.add_trace(go.Scatter(
            x=times, 
            y=temperatures, 
            mode='lines',
            name='Temperature',
            line=dict(color='green')
        ))

        # Trazar el límite inferior de temperatura
        fig.add_trace(go.Scatter(
            x=times, 
            y=[TemLimLow] * len(times), 
            mode='lines',
            name='TemLimLow',
            line=dict(color='blue', dash='dash')
        ))

        # Trazar el límite superior de temperatura
        fig.add_trace(go.Scatter(
            x=times, 
            y=[TemLimUp] * len(times), 
            mode='lines',
            name='TemLimUp',
            line=dict(color='red', dash='dash')
        ))

        # Configurar el diseño del gráfico
        fig.update_layout(
            title="Temperature vs Time (Hours)",
            xaxis=dict(
                title="Time (hours)",
                showgrid=True,
                zeroline=False
            ),
            yaxis=dict(
                title="Temperature (°C)",
                showgrid=True,
                zeroline=False
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            ),
            template="plotly_white",
            width=1280,
            height=720
        )

        # Guardar la figura en un buffer como una imagen PNG
        buf = io.BytesIO()
        fig.write_image(buf, format='png')
        buf.seek(0)

        # Codificar la imagen en base64
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')

        # Retornar imagen codificada y texto en JSON
        return JsonResponse({
            "message": "Temperature vs Time graph with limits generated successfully.",
            "image": image_base64
        })

    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)

def api_export_csv_analysis(request, pk):
    """
    Exporta los datos de análisis del sensor especificado por su ID en formato CSV.
    """
    # Obtener el sensor
    sensor = get_object_or_404(Sensor, id=pk)

    # Generar el análisis
    analysis_view = Analysis(sensor=sensor)
    context = analysis_view.get_context_data()

    # Obtener los valores de TemLimLow y TemLimUp desde los parámetros
    tem_lim_low_param = Parameters.objects.filter(name='min_temp').first()
    tem_lim_up_param = Parameters.objects.filter(name='max_temp').first()
    if not tem_lim_low_param or not tem_lim_up_param:
        return JsonResponse({"error": "Temperature limit parameters not found."}, status=404)

    TemLimLow = tem_lim_low_param.value
    TemLimUp = tem_lim_up_param.value

    # Crear la respuesta HTTP con encabezado para CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="sensor_{pk}_analysis.csv"'

    # Crear el escritor CSV
    writer = csv.writer(response)

    # Escribir encabezados
    writer.writerow(['t', 'LPA', 'RPI', 'mRPI', 'T', 'Temperature Low Limit (°C)', 'Temperature High Limit (°C)'])

    # Procesar los datos asegurándose de manejar correctamente NaN, NAType y valores no numéricos
    keys = ['t', 'LPA', 'RPI', 'mRPI', 'T']


    #writer.writerow(['t','mT' ,'LPA','b','n', 'tx','Na','Nb','mu','logN','bc','nc', 'txc','Nac','Nbc','muc','logNc'  , 'RPI', 'mRPI'])
    #keys = ['t','mT' ,'LPA','b','n', 'tx','Na','Nb','mu','logN','bc','nc', 'txc','Nac','Nbc','muc','logNc'  , 'RPI', 'mRPI']


    data_arrays = []

    for key in keys:
        raw_data = context.get(key, [])
        clean_data = []
        for x in raw_data:
            try:
                # Convertir a float, manejando NAType y valores no numéricos
                clean_data.append(float(x))
            except (ValueError, TypeError):
                # Reemplazar valores inválidos con 0
                clean_data.append(0)
        data_arrays.append(np.array(clean_data, dtype=np.float64))

    # Escribir los datos al archivo CSV
    for row in zip(*data_arrays):
        writer.writerow(list(row) + [TemLimLow, TemLimUp])

    # Retornar la respuesta
    return response

def api_export_temperatures_up_csv(request, pk):
    """
    Exporta los registros de temperatura de un sensor específico en formato CSV,
    incluyendo el límite superior de temperatura (TemLimUp).
    """
    try:
        # Obtener el sensor por su ID
        sensor = get_object_or_404(Sensor, id=pk)

        # Obtener los registros asociados al sensor
        records = sensor.records.order_by('time')
        if not records.exists():
            return JsonResponse({"error": "No records found for the specified sensor."}, status=404)

        # Obtener el valor de TemLimUp desde los parámetros
        tem_lim_up_param = Parameters.objects.filter(name='max_temp').first()
        if not tem_lim_up_param:
            return JsonResponse({"error": "TemLimUp parameter not found."}, status=404)

        TemLimUp = tem_lim_up_param.value

        # Crear la respuesta HTTP con tipo de contenido CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename=\"sensor_{sensor.id}_data_with_limit.csv\"'

        # Crear un escritor CSV
        writer = csv.writer(response)

        # Escribir el encabezado del archivo CSV
        writer.writerow(['Time', 'Temperature (°C)', 'Temperature Limit (°C)'])

        # Escribir los registros con TemLimUp
        for record in records:
            writer.writerow([record.time, record.temperature, TemLimUp])

        return response

    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)

def api_export_temperatures_low_csv(request, pk):
    """
    Exporta los registros de temperatura de un sensor específico en formato CSV,
    incluyendo el límite inferior de temperatura (TemLimLow).
    """
    try:
        # Obtener el sensor por su ID
        sensor = get_object_or_404(Sensor, id=pk)

        # Obtener los registros asociados al sensor
        records = sensor.records.order_by('time')
        if not records.exists():
            return JsonResponse({"error": "No records found for the specified sensor."}, status=404)

        # Obtener el valor de TemLimLow desde los parámetros
        tem_lim_low_param = Parameters.objects.filter(name='min_temp').first()
        if not tem_lim_low_param:
            return JsonResponse({"error": "TemLimLow parameter not found."}, status=404)

        TemLimLow = tem_lim_low_param.value

        # Crear la respuesta HTTP con tipo de contenido CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="sensor_{sensor.id}_data_with_low_limit.csv"'

        # Crear un escritor CSV
        writer = csv.writer(response)

        # Escribir el encabezado del archivo CSV
        writer.writerow(['Time', 'Temperature (°C)', 'Temperature Low Limit (°C)'])

        # Escribir los registros con TemLimLow
        for record in records:
            writer.writerow([record.time, record.temperature, TemLimLow])

        return response

    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)

def api_export_temperatures_limits_csv(request, pk):
    """
    Exporta los registros de temperatura de un sensor específico en formato CSV,
    incluyendo los límites inferior (TemLimLow) y superior (TemLimUp) de temperatura.
    """
    try:
        # Obtener el sensor por su ID
        sensor = get_object_or_404(Sensor, id=pk)

        # Obtener los registros asociados al sensor
        records = sensor.records.order_by('time')
        if not records.exists():
            return JsonResponse({"error": "No records found for the specified sensor."}, status=404)

        # Obtener los valores de TemLimLow y TemLimUp desde los parámetros
        tem_lim_low_param = Parameters.objects.filter(name='min_temp').first()
        tem_lim_up_param = Parameters.objects.filter(name='max_temp').first()
        if not tem_lim_low_param or not tem_lim_up_param:
            return JsonResponse({"error": "Temperature limit parameters not found."}, status=404)

        TemLimLow = tem_lim_low_param.value
        TemLimUp = tem_lim_up_param.value

        # Crear la respuesta HTTP con tipo de contenido CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="sensor_{sensor.id}_data_with_limits.csv"'

        # Crear un escritor CSV
        writer = csv.writer(response)

        # Escribir el encabezado del archivo CSV
        writer.writerow(['Time', 'Temperature (°C)', 'Temperature Low Limit (°C)', 'Temperature High Limit (°C)'])

        # Escribir los registros con TemLimLow y TemLimUp
        for record in records:
            writer.writerow([record.time, record.temperature, TemLimLow, TemLimUp])

        return response

    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)

