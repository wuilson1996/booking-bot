* Bot Booking
* requisitos para instalacion.
Ubuntu Server 20.04
Django 3.2
Python 3.7 o superior.
Instalar requirements.txt "instalara django en su version 3.2 y todas las dependencias requeridas."

* Base de datos: crear base de datos: booking_bot
- conexiones a Base de datos:
* sqlite3:
DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

* MYSQL y MariaDB
DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',  # Utiliza el backend de MySQL
            'NAME': 'booking_bot',   # Nombre de la base de datos
            'USER': 'usuario',                   # Usuario de la base de datos
            'PASSWORD': 'password',            # Contraseña del usuario
            'HOST': 'localhost',                    # Host, si es local usa 'localhost'
            'PORT': '3306',                         # Puerto de MariaDB, usualmente 3306
        }
    }

En la carpeta service encontramos los servicio a usar para instalar el proyecto en linea.
usando system y nginx.
mas info:
https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu
Podemos apoyarnos en esta documentacion el cual tiene todo lo necesario.

Configuraciones search.
1) vamos al admin django.
2) buscamos la opcion General searchs.
3) agregar general search.
    * url: https://www.booking.com
    * city and country: Madrid, Comunidad de Madrid, España
    * time sleep minutes: 10 or > 0

Configuraciones Process.
1) vamos al admin django.
2) buscamos la opcion Process actives.
3) agregamos los procesos.
    * Date end: 2024-09-15
    * Occupancy: 3
    * Start: 4
    * Position: [0, 1, 2, 3, 4, 9]
    * Active: Descheck
    * Current: Descheck
4) agregaremos 5 procesos iguales. al anterior cambiando algunos parametros.
    * Occupancy: 2
    * Start: 4
    * Position: [0, 1, 2, 3, 4, 9, 14, 19, 24]
    ------------------------------------------
    * Occupancy: 2
    * Start: 3
    * Position: [0, 1, 2, 3, 4]
    ------------------------------------------
    * Occupancy: 3
    * Start: 3
    * Position: [0, 1, 2, 3, 4]
    ------------------------------------------
    * Occupancy: 5
    * Start: 3
    * Position: [0, 1, 2, 3, 4]
    ------------------------------------------
    * Occupancy: 5
    * Start: 4
    * Position: [0, 1, 2, 3, 4, 9]
