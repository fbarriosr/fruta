# Utiliza la imagen base de Python 3.8
FROM python:3.8

# Establece variables de entorno para evitar interacciones durante la instalación
ENV DEBIAN_FRONTEND=noninteractive

# Actualiza la lista de paquetes e instala locales
RUN apt-get update && \
    apt-get install -y locales && \
    # Genera la configuración regional es_CL.UTF-8
    sed -i '/es_CL.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen es_CL.UTF-8 && \
    # Limpia la caché de apt para reducir el tamaño de la imagen
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Establece las variables de entorno para la configuración regional
ENV LANG=es_CL.utf8
ENV LANGUAGE=es_CL:es
ENV LC_ALL=es_CL.utf8

# Crea el directorio para almacenar el contenido del proyecto
RUN mkdir /code

# Define /code como el directorio de trabajo
WORKDIR /code

# Copia el archivo de requerimientos al directorio de trabajo
COPY requirements.txt /code/

# Instala los requerimientos descritos en requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia el contenido del proyecto al directorio de trabajo /code
COPY . /code/
