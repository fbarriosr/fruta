from datetime import datetime, timedelta
import re

# Datos de entrada
fecha_str = "2023-11-21 13:59:58+00:00"
zona_origen = "UTC -06:00"
zona_destino = "UTC -06:00"

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

# Mostrar el resultado final
print(fecha_convertida.strftime("%Y-%m-%d %H:%M:%S"))