import chardet
import locale
from django.utils.timezone import localtime
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from django.views import View
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.views.generic import TemplateView, DetailView
from django.utils.timezone import localtime, get_current_timezone
from django.utils.dateformat import DateFormat
from django.db.models import Min, Max, Count
from .models import *
from django.shortcuts import get_object_or_404
import random
from django.http import HttpResponse, Http404 
import io
import plotly.graph_objects as go
import ast
import base64
from django.http import JsonResponse


nameWeb = "Fresh Fruit"

class DetailViewTrip(DetailView):
    model = Trip
    template_name = 'web/views/detail_trip.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trip = self.get_object()
        sensors = Sensor.objects.filter(trip=trip)

        # Configurar paginación
        paginator = Paginator(sensors, 10)
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
            product_id = request.POST.get('product')
            microorganism_id = request.POST.get('microorganisms')

            # Validar que todos los campos requeridos estén presentes
            if not all([license_plate, driver, origin, destination, departure_date, arrival_date, product_id, microorganism_id]):
                raise ValueError("All fields are required.")

            # Obtener las relaciones de ProductType y Microorganism
            product = get_object_or_404(ProductType, id=product_id)
            microorganism = get_object_or_404(Microorganism, id=microorganism_id)

            # Crear y guardar el objeto Trip
            trip = Trip(
                license_plate=license_plate,
                driver=driver,
                shipment= shipment,
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                arrival_date=arrival_date,
                product=product,
                microorganisms=microorganism,
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
                "error": f"Error saving trip: {e}",
            }
            return render(request, self.template_name, context)

class Trips(TemplateView):
    template_name = "web/views/trips.html"

    def get_queryset(self):
        trips = Trip.objects.order_by('-arrival_date')
        paginator = Paginator(trips, 10)
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
                'min_temp': min_temp,
                'max_temp': max_temp,
                'total_records': total_records,
                'min_date': min_date,
                'max_date': max_date,
                'decimal_days': round(decimal_days, 2),
                'decimal_hours': round(decimal_hours, 2),
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
        return context


class RecordAdd(View):
    template_name = "web/views/add_record.html"

    def get(self, request, trip_id, *args, **kwargs):
        trip = get_object_or_404(Trip, id=trip_id)
        context = {
            "nameWeb": nameWeb,
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
            context = self.get_context_with_error(trip, "No file uploaded!")
            return render(request, self.template_name, context)

        if not pallet_location_id or not sensor_position_id:
            context = self.get_context_with_error(trip, "Pallet Location and Sensor Position are required!")
            return render(request, self.template_name, context)

        try:
            raw_data = uploaded_file.read()
            detected_encoding = chardet.detect(raw_data)["encoding"] or "utf-8"
            lines = raw_data.decode(detected_encoding).splitlines()

            # Extraer información del sensor
            device = "Unknown"
            serial_number = "Unknown"

            for line in lines:
                line = line.strip()
                if line.startswith("Modelo de dispositivo:") or line.startswith("Model :"):
                    device = line.split(":", 1)[1].strip()
                elif line.startswith("Número de serie:") or line.startswith("S/N :"):
                    serial_number = line.split(":", 1)[1].strip()
                elif line.startswith("No."):
                    break

            # Obtener ubicaciones
            pallet_location = get_object_or_404(PalletLocation, id=pallet_location_id)
            sensor_position = get_object_or_404(SensorLocation, id=sensor_position_id)

            # Crear o actualizar sensor
            sensor, created = Sensor.objects.get_or_create(
                serial_number=serial_number,
                trip=trip,
                defaults={
                    "device": device,
                    "tag": sensor_tag,
                    "pallet_location": pallet_location,
                    "sensor_position": sensor_position,
                },
            )

            if not created:
                # Actualizar información del sensor existente si es necesario
                sensor.device = device
                if sensor_tag and sensor.tag != sensor_tag:
                    sensor.tag = sensor_tag
                sensor.pallet_location = pallet_location
                sensor.sensor_position = sensor_position
                sensor.save()

            # Procesar las líneas de datos
            is_data_section = False
            records = []
            errors = []
            current_tz = get_current_timezone()

            for line in lines:
                line = line.strip()
                if line.startswith("No."):
                    is_data_section = True
                    continue

                if is_data_section:
                    try:
                        parts = [part.strip() for part in line.split() if part.strip()]
                        if len(parts) < 3:
                            continue

                        number = int(parts[0])
                        time_str = f"{parts[1]} {parts[2]} {parts[-3]} {parts[-2]}"
                        temperature_str = parts[-1]

                        time_str = time_str.replace("a. m.", "AM").replace("p. m.", "PM").strip()
                        date_format = "%d/%m/%Y %I:%M:%S %p"
                        naive_time = datetime.strptime(time_str, date_format)
                        aware_time = current_tz.localize(naive_time)

                        if not (trip.departure_date <= aware_time <= trip.arrival_date):
                            errors.append(f"Time '{aware_time}' out of trip range.")
                            continue

                        temperature = float(temperature_str)

                        records.append(Record(
                            sensor=sensor,
                            number=number,
                            time=aware_time,
                            temperature=temperature
                        ))
                    except Exception as e:
                        errors.append(f"Error parsing line '{line}': {e}")
                        continue

            Record.objects.bulk_create(records, batch_size=1000)

            success_message = f"Sensor {'created' if created else 'updated'} successfully. Imported {len(records)} records."
            if errors:
                success_message += f" Encountered {len(errors)} errors."

            context = {
                "nameWeb": nameWeb,
                "title": "Add Sensor Data",
                "trip": trip,
                "sensor_locations": SensorLocation.objects.all(),
                "pallet_locations": PalletLocation.objects.all(),
                "errors": errors,
                "success_message": success_message,
            }
            return render(request, self.template_name, context)

        except Exception as e:
            context = self.get_context_with_error(trip, f"Unexpected error: {e}")
            return render(request, self.template_name, context)

    def get_context_with_error(self, trip, error_message):
        return {
            "nameWeb": nameWeb,
            "title": "Add Sensor Data",
            "trip": trip,
            "sensor_locations": SensorLocation.objects.all(),
            "pallet_locations": PalletLocation.objects.all(),
            "error": error_message,
        }

class AnalysisViewSensor(DetailView):
    model = Sensor
    template_name = "web/views/analysis.html"
    context_object_name = 'sensor'
    cifra = 5  # Definir la cantidad de cifras significativas

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        records = self.object.records.order_by('time')

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
            decimal_days = np.round(time_difference.days + time_difference.seconds / 86400, self.cifra)
            decimal_hours = np.round(time_difference.total_seconds() / 3600, self.cifra)

            # Crear DataFrame desde los registros
            values = records.values_list('number', 'time', 'temperature')
            df = pd.DataFrame(list(values), columns=['number', 'time', 'temperature'])

            pTemUp = (sum(df['temperature'] > TemLimUp) / len(df['temperature'])) * 100
            pTemLow = (sum(df['temperature'] < TemLimLow) / len(df['temperature'])) * 100

            if pTemUp > pTemLimUp:
                message = 'SHIPMENT REJECTED'
                description = f"The percentage of temperatures exceeding the allowed limit ({TemLimUp}) reached {pTemUp}%, surpassing the permitted threshold of {pTemLimUp}."
                do = "api_generate_temperatures_up"
            elif pTemLow > pTemLimLow:
                message = 'SHIPMENT ACCEPTED'
                description = f"SHIPMENT ACCEPTED: For more than {pTemLow}% of the shipping time, the temperature remained below the lower threshold of {TemLimLow}."
                do = "api_generate_temperatures_low"
            else:
                message = 'ANALYZING SHIPMENT'
                description = "The algorithm and the mathematical model are being executed to analyze the shipment."
                do = "graficar_algoritmo"
                
            #do = "api_generate_temperatures_low"
            # Actualizar contexto
            context.update({
                "min_temp": min_temp,
                "max_temp": max_temp,
                "total_records": total_records,
                "min_date": min_date,
                "max_date": max_date,
                "decimal_days": decimal_days,
                "decimal_hours": decimal_hours,
                "message":message,
                "description":description,
                "do": do, 
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

        return context

class Analysis:
    def __init__(self, sensor=None):
        self.sensor = sensor  # Asigna el sensor al atributo de la clase
        self.cifra = self.get_cifra()  # Recupera el valor de 'cifra' desde Parameters
        self.ecuacion = self.get_equation_parameters()
    def get_cifra(self):
        """
        Recupera el valor de 'cifra' desde el modelo Parameters.
        """
        cifra_param = Parameters.objects.filter(name='cifra').first()
        if cifra_param:
            return int(cifra_param.value)
        return 5  # Valor por defecto si no se encuentra
    def get_equation_parameters(self):
        if not self.sensor or not self.sensor.trip:
            raise ValueError("Sensor or associated trip is required to fetch equation parameters.")

        product = self.sensor.trip.product
        microorganism = self.sensor.trip.microorganism

        equation = Equation.objects.filter(product=product).filter(microorganism=microorganism).first()
        if not equation:
            raise ValueError(f"No equation found for product '{product}' and microorganism '{microorganisms}'.")

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
            df['LPD'] = np.round(eval(lpa_form, {"__builtins__": None}, variables), self.cifra).where(df['mT'].notna(), np.nan)

            df['LPA'] = (df['dt'] / df['LPD']).cumsum()

            # calculos de LPA >=1 
            # Constantes para calculos LPA >=1
            # Recuperar los parámetros de la ecuación
            
            k_b, a_b, k_n, a_n = 0.5757, 3.0481, 0.1226, 0.0517
            
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
            
            t_h_at_max_lpa = str(round(df['t_h'].iloc[mask[0]],self.cifra))+' hours'

            if len(mask) > 1:
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
                    logN_2 = round(b_2 * (dt_2 ** n_2), self.cifra)
                    df.at[i, 'logN'] = logN_2

                    # Modelo compuesto
                    logNc_2 = round(bc * (dt_2 ** nc), self.cifra)
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
                    
                    # Calcular mRPI si existen suficientes registros
                    if pd.notna(logN) and pd.notna(df['logN'].iloc[i - 120]) and pd.notna(logNc) and pd.notna(df['logNc'].iloc[i - 120]):
                        mRPI = round((logN - df['logN'].iloc[i - 120]) / (logNc - df['logNc'].iloc[i - 120]), self.cifra)
                    else:
                        mRPI = pd.NA

                    df.at[i, 'mRPI'] = mRPI
           
            # Convertir valores de LPA > 1 a pd.NA
            df.loc[df['LPA'] > 1, 'LPA'] = pd.NA
        
        # Simula datos de ejemplo (ajusta según tu implementación real)
        context = {
            't': df['t_h'] , # Reemplaza con tus datos reales
            'LPA': df['LPA'].tolist(),
            'RPI': df['RPI'].tolist(),
            'mRPI': df['mRPI'].tolist(),
            'T': df['temperature'],
            'title': aux,
            't_h_at_max_lpa':t_h_at_max_lpa
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
            {"name": "LPA", "y": LPA, "color": "green", "dash": "solid", "yaxis": "y1"},
            {"name": "RPI", "y": RPI, "color": "red", "dash": "solid", "yaxis": "y1"},
            {"name": "mRPI", "y": mRPI, "color": "orange", "dash": "dot", "yaxis": "y1"},
            {"name": "Temperature", "y": T, "color": "blue", "dash": "solid", "yaxis": "y2"}
        ]

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
                title="RPI and LPA",
                range=[0, 3],
                dtick=0.5,
                titlefont=dict(color="green", size=28),
                tickfont=dict(size=24, color="green"),
                showgrid=True,
                zeroline=False,
                side="left"
            ),
            yaxis2=dict(
                title="Temperature (°C)",
                range=[0, 12],
                dtick=2,
                titlefont=dict(color="blue", size=28),
                tickfont=dict(size=24, color="blue"),
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

    # Retornar imagen codificada y texto en JSON
    return JsonResponse({
        "message": "Analysis generated successfully.",
        "image": image_base64,
        "t_h_at_max_lpa": context['t_h_at_max_lpa']
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

