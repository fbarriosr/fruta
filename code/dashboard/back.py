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
            timezone_value = None

            for line in lines:
                line = line.strip()
                if line.startswith("Modelo de dispositivo:") or line.startswith("Model :"):
                    device = line.split(":", 1)[1].strip()
                elif line.startswith("Número de serie:") or line.startswith("S/N :"):
                    serial_number = line.split(":", 1)[1].strip()
                elif line.startswith("Timezone:") or line.startswith("Zona horaria:"):
                    timezone_value = line.split(":", 1)[1].strip()
                elif line.startswith("No."):
                    break

            # Validar y asignar la zona horaria
            timezone = None
            if timezone_value:
                timezone = TimeZoneChoices.objects.filter(value=timezone_value).first()
                if not timezone:
                    context = self.get_context_with_error(trip, f"Invalid timezone: {timezone_value}")
                    return render(request, self.template_name, context)


            # Obtener ubicaciones
            pallet_location = get_object_or_404(PalletLocation, id=pallet_location_id)
            sensor_position = get_object_or_404(SensorLocation, id=sensor_position_id)

            estado= get_object_or_404(Status, state='Pending')

            # Crear o actualizar sensor
            sensor, created = Sensor.objects.get_or_create(
                serial_number=serial_number,
                trip=trip,
                defaults={
                    "device": device,
                    "tag": sensor_tag,
                    "pallet_location": pallet_location,
                    "sensor_position": sensor_position,
                    "timezone": timezone,
                    'status': estado
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
            records, last = self.extract_temperature_records(decoded_file, file_extension, trip, sensor, timezone)


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
                elif line.startswith("Zona horaria:") or line.startswith("Timezone:") :
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
                    aware_time = current_tz.localize(naive_time)

                    # Construir el string de depuración (opcional)
                    last = f"{number} {time_str} {temperature}"

                    # Crear y agregar el registro a la lista
                    records.append(Record(
                        sensor=sensor,
                        number=number,
                        time=aware_time,
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
                        aware_time = current_tz.localize(naive_time)
                        last= str(number)+' ' +time_str + ' '+ str(temperature)
                        
                        records.append(Record(
                            sensor=sensor,
                            number=number,
                            time=aware_time,
                            temperature=temperature
                        ))
                    except Exception as e:
                        print(f"Error parsing TXT line '{line}': {e}")
            last = last +' len: '+ str(len(records))

        return records , last

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




