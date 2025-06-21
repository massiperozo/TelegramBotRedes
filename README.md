
# 🤖 Bot de Monitoreo de Red en Telegram con MQTT

Este es un bot de Telegram diseñado para ayudarte a diagnosticar y monitorear la conectividad de red de tus hosts con integración completa de **MQTT** para telemetría en tiempo real. Puedes realizar **pings**, **traceroutes** y configurar un **monitoreo constante** para recibir alertas si un host se vuelve inalcanzable o vuelve a estar en línea, mientras todos los datos se publican automáticamente a un broker MQTT para visualización en series de tiempo.

---

## ✨ Características

- 🌐 **Ping:** Envía paquetes ICMP a un dominio o IP para medir la latencia y la pérdida de paquetes.
- 📡 **Traceroute:** Traza la ruta de los paquetes a un destino, mostrando todos los saltos intermedios (routers).
- 🟢 **Monitoreo Recurrente:** Configura el bot para que haga ping a un host cada 15 segundos y te alerte si cambia de estado (alcanzable/inalcanzable).
- 📊 **Integración MQTT:** Todos los datos se publican automáticamente a un broker MQTT con timestamps para series de tiempo.
- 📈 **Visualización en Tiempo Real:** Usa MQTT Explorer para ver gráficos de latencia y saltos en tiempo real.
- 🔐 **Autenticación MQTT:** Broker configurado con usuario y contraseña para seguridad.
- 📚 **Documentación Integrada:** Accede a explicaciones detalladas sobre Ping, Traceroute y el monitoreo, incluyendo cómo interpretar los resultados, directamente desde el bot.
- 🗣️ **Interfaz Amigable:** Menú desplegable con botones y mensajes claros con emojis para una experiencia de usuario intuitiva.

---

## 🛠️ Requisitos del Sistema

Antes de ejecutar el bot, asegúrate de tener instalado lo siguiente:

- **Windows 10/11** (las instrucciones están optimizadas para Windows)
- **Python 3.8 o superior:** Puedes descargarlo desde [python.org](https://www.python.org/).
- **Permisos de Administrador:** Necesarios para instalar y configurar el broker MQTT.
- **Conexión a Internet:** Para comunicación con Telegram y descarga de componentes.
- **Comandos `ping` y `tracert`:** Vienen preinstalados en Windows.

---

## 🚀 Instalación y Configuración Completa

### PARTE 1: Configuración Básica de Python y Telegram

#### 1. Clona el Repositorio (o descarga el código)

Si usas git:

```bash
git clone <URL_DE_TU_REPOSITORIO>
cd <nombre_de_la_carpeta_del_repositorio>
```

Si no, descarga los archivos del bot y navega al directorio donde los guardaste.

#### 2. Crea un Entorno Virtual (Recomendado)

Es una buena práctica usar un entorno virtual para gestionar las dependencias de Python:

```shellscript
python -m venv venv
```

Activa el entorno virtual:

```shellscript
.\venv\Scripts\activate
```

#### 3. Instala las Dependencias

El bot utiliza las librerías `python-telegram-bot` y `paho-mqtt`. Instálalas usando pip:

```shellscript
pip install python-telegram-bot==20.7 paho-mqtt==1.6.1 httpx
```

#### 4. Obtén tu Token de Bot de Telegram

Para que tu bot funcione, necesitas un token de la API de Telegram:

1. Abre Telegram y busca a `@BotFather`.
2. Inicia un chat con él y envía el comando `/newbot`.
3. Sigue las instrucciones de BotFather para darle un nombre a tu bot y un nombre de usuario (debe terminar en `bot`, ej. `MiMonitorBot`).
4. BotFather te proporcionará un token de acceso HTTP API. Cópialo; es una cadena larga de números y letras.


#### 5. Configura el Token en el Archivo del Bot

Abre el archivo `mqtt_bot.py` en tu editor de código preferido.

Busca la línea que dice:

```python
TOKEN = "7733059910:AAGxkZsxiIbHUgAojSSLKN_17Zm-CZU0xpM"
```

Reemplaza el token con el tuyo:

```python
TOKEN = "TU_TOKEN_AQUI"  # Reemplaza con tu token real
```

### PARTE 2: Instalación y Configuración del Broker MQTT

#### 6. Descargar e Instalar Mosquitto MQTT Broker

1. **Descargar Mosquitto:**

1. Ve a [https://mosquitto.org/download/](https://mosquitto.org/download/)
2. Descarga **mosquitto-2.0.18-install-windows-x64.exe** (o la versión más reciente)
3. **IMPORTANTE:** Ejecuta el instalador **como Administrador**



2. **Instalar Mosquitto:**

1. Sigue el asistente de instalación
2. Instala en la ruta por defecto: `C:\Program Files\mosquitto`
3. Marca todas las opciones durante la instalación





#### 7. Configurar Autenticación del Broker MQTT

1. **Abrir Command Prompt como Administrador:**

1. Presiona `Win + R`
2. Escribe `cmd`
3. Presiona `Ctrl + Shift + Enter` (para ejecutar como administrador)



2. **Navegar al directorio de Mosquitto:**

```bat
cd "C:\Program Files\mosquitto"
```


3. **Crear archivo de configuración:**

```bat
echo # Configuracion Mosquitto para Proyecto de Redes > mosquitto.conf
echo listener 1883 >> mosquitto.conf
echo allow_anonymous false >> mosquitto.conf
echo password_file passwd >> mosquitto.conf
echo log_dest file mosquitto.log >> mosquitto.conf
echo log_type all >> mosquitto.conf
```


4. **Crear usuario y contraseña:**

```bat
mosquitto_passwd -c passwd network_monitor
```

1. Cuando te pida la contraseña, ingresa: `monitor123`
2. Presiona Enter para confirmar





#### 8. Probar el Broker MQTT

1. **Iniciar el broker (en Command Prompt como Administrador):**

```bat
cd "C:\Program Files\mosquitto"
mosquitto -c mosquitto.conf -v
```


2. **Deberías ver algo como:**

```plaintext
1704110400: mosquitto version 2.0.18 starting
1704110400: Config loaded from mosquitto.conf
1704110400: Opening ipv4 listen socket on port 1883
1704110400: mosquitto version 2.0.18 running
```


3. **Mantén esta ventana abierta** - el broker debe estar ejecutándose para que funcione el sistema.


### PARTE 3: Instalación del Explorador MQTT

#### 9. Descargar e Instalar MQTT Explorer

1. **Descargar MQTT Explorer:**

1. Ve a [http://mqtt-explorer.com/](http://mqtt-explorer.com/)
2. Descarga **MQTT-Explorer-Setup-0.4.0-beta1.exe** (o la versión más reciente)
3. Instala normalmente (no requiere permisos de administrador)



2. **Configurar conexión en MQTT Explorer:**

1. Abre MQTT Explorer
2. Haz clic en **"+ Create Connection"**
3. Configura los siguientes datos:

1. **Name:** `Monitor Local`
2. **Host:** `localhost`
3. **Port:** `1883`
4. **Username:** `network_monitor`
5. **Password:** `monitor123`



4. Haz clic en **"CONNECT"**



3. **Verificar conexión:**

1. Si todo está bien, verás "Connected" en verde
2. En el panel izquierdo aparecerá el tópico `mensaje_grupo` cuando empiecen a llegar datos





### PARTE 4: Configuración del Firewall de Windows

#### 10. Permitir Tráfico MQTT en el Firewall

1. **Abrir Firewall de Windows:**

1. Presiona `Win + R`
2. Escribe `wf.msc`
3. Presiona Enter



2. **Crear regla de entrada:**

1. Haz clic en **"Reglas de entrada"** en el panel izquierdo
2. Haz clic en **"Nueva regla..."** en el panel derecho
3. Selecciona **"Puerto"** → Siguiente
4. Selecciona **"TCP"** y **"Puertos locales específicos"**
5. Ingresa `1883` → Siguiente
6. Selecciona **"Permitir la conexión"** → Siguiente
7. Marca todos los perfiles → Siguiente
8. Nombre: `MQTT Broker Port 1883` → Finalizar





### PARTE 5: Ejecutar el Sistema Completo

#### 11. Iniciar Todos los Componentes

**Necesitarás 3 ventanas de Command Prompt/Terminal:**

1. **Ventana 1 - Broker MQTT (como Administrador):**

```bat
cd "C:\Program Files\mosquitto"
mosquitto -c mosquitto.conf -v
```


2. **Ventana 2 - Bot de Telegram:**

```bat
cd ruta\a\tu\proyecto
.\venv\Scripts\activate
python bot.py
```


3. **Ventana 3 - Suscriptor MQTT (opcional, para debug):**

```bat
cd ruta\a\tu\proyecto
.\venv\Scripts\activate
python mqtt_subscriber.py
```


4. **MQTT Explorer:** Mantén abierto y conectado


#### 12. Probar el Sistema

1. **En Telegram:**

1. Busca tu bot y envía `/start`
2. Prueba el botón "🌐 Ping Host" con `google.com`
3. Verifica que recibas la respuesta del bot



2. **En MQTT Explorer:**

1. Deberías ver aparecer datos en el tópico `mensaje_grupo`
2. Los datos incluyen timestamp, latencia, destino, etc.



3. **En el Suscriptor (si lo ejecutaste):**

1. Verás los mensajes JSON formateados en la consola





---

## 💬 Cómo Usar el Bot en Telegram

1. **Inicia el bot:** Abre Telegram y busca el nombre de usuario de tu bot.
2. **Envía el comando `/start` al bot.**
3. El bot te dará la bienvenida y mostrará un menú desplegable con varias opciones:


### Opciones Disponibles:

- **🌐 Ping Host:** Realiza ping a un dominio/IP y publica resultados a MQTT
- **📡 Traceroute Host:** Ejecuta traceroute y publica saltos a MQTT
- **🟢 Iniciar Monitoreo:** Monitoreo continuo con alertas y datos MQTT
- **🔴 Detener Monitoreo:** Detiene el monitoreo activo
- **📊 Estado MQTT:** Verifica el estado de conexión MQTT
- **📚 Ayuda:** Guía completa de uso


### Ejemplo de Uso:

1. Toca **🌐 Ping Host**
2. El bot te pedirá el destino
3. Envía `google.com`
4. Recibirás la respuesta en Telegram
5. Los datos aparecerán automáticamente en MQTT Explorer


---

## 📊 Visualización de Datos en MQTT Explorer

### Estructura de Datos MQTT:

Los mensajes se publican en formato JSON en el tópico `mensaje_grupo`:

```json
{
  "type": "ping",
  "destination": "google.com",
  "latency_ms": 25.5,
  "success": true,
  "timestamp": "2024-01-01T12:00:00.000Z",
  "unix_timestamp": 1704110400
}
```

### Tipos de Mensajes:

- **`ping`:** Resultados de comandos ping
- **`traceroute`:** Resultados de traceroute con saltos
- **`monitoring`:** Datos del monitoreo continuo


### Crear Gráficos de Series de Tiempo:

1. En MQTT Explorer, selecciona el tópico `mensaje_grupo`
2. Haz clic en la pestaña **"Chart"**
3. Configura el campo `latency_ms` para ver la latencia en tiempo real
4. Los timestamps permiten crear gráficos históricos


---

## 🛑 Detener el Sistema

Para detener completamente el sistema:

1. **Bot de Telegram:** Presiona `Ctrl + C` en la ventana del bot
2. **Broker MQTT:** Presiona `Ctrl + C` en la ventana del broker
3. **Suscriptor:** Presiona `Ctrl + C` si lo estás ejecutando
4. **MQTT Explorer:** Simplemente cierra la aplicación


---

## 🔧 Solución de Problemas Comunes

### El bot no se conecta a MQTT:

- Verifica que el broker Mosquitto esté ejecutándose
- Confirma que el usuario y contraseña sean correctos
- Revisa que el puerto 1883 esté abierto en el firewall


### MQTT Explorer no se conecta:

- Verifica la configuración de conexión (host, puerto, usuario, contraseña)
- Asegúrate de que el broker esté ejecutándose
- Revisa los logs del broker en `C:\Program Files\mosquitto\mosquitto.log`


### El bot no responde en Telegram:

- Verifica que el token sea correcto
- Confirma que tengas conexión a internet
- Revisa los logs en la consola del bot


### Comandos ping/tracert no funcionan:

- Verifica que estés en Windows (los comandos están optimizados para Windows)
- Confirma que los comandos `ping` y `tracert` funcionen desde Command Prompt


### Error "Access Denied" al configurar Mosquitto:

- Asegúrate de ejecutar Command Prompt como Administrador
- Verifica que tengas permisos de escritura en `C:\Program Files\mosquitto`


### El broker no inicia:

- Revisa el archivo de configuración `mosquitto.conf`
- Verifica que el archivo `passwd` exista
- Consulta los logs en `mosquitto.log`


---

## 📁 Estructura del Proyecto

```plaintext
proyecto-mqtt-bot/
├── mqtt_bot.py              # Bot principal con integración MQTT
├── mqtt_subscriber.py       # Suscriptor para debug (opcional)
├── requirements.txt         # Dependencias de Python
├── setup_mqtt.bat          # Script de instalación (Windows)
├── setup_mosquitto_config.bat  # Configuración de Mosquitto
├── start_mosquitto.bat     # Iniciar broker fácilmente
├── test_mqtt.bat           # Probar conexión MQTT
└── README.md               # Este archivo
```

---

## ⚠️ Notas Importantes

- **El broker MQTT debe estar ejecutándose** antes de iniciar el bot
- **Mantén las 3 ventanas abiertas** durante el uso (broker, bot, y opcionalmente suscriptor)
- **El monitoreo recurrente** solo funciona mientras el bot esté activo
- **Los datos MQTT** se almacenan temporalmente; para persistencia considera usar una base de datos
- **Firewall:** Asegúrate de que el puerto 1883 esté permitido
- **Permisos:** El broker requiere permisos de administrador para ejecutarse
- **Configuración MQTT:** Usuario: `network_monitor`, Contraseña: `monitor123`, Puerto: `1883`


---

## 🎯 Casos de Uso del Proyecto

Este sistema es ideal para:

- **Administradores de red:** Monitoreo remoto de infraestructura
- **Estudiantes:** Aprendizaje de protocolos de red y MQTT
- **DevOps:** Integración con sistemas de monitoreo existentes
- **IoT:** Base para sistemas de telemetría más complejos
- **Investigación:** Recolección de datos de latencia y conectividad


---

## 🚀 Extensiones Futuras

Posibles mejoras al proyecto:

- **Base de datos:** Almacenamiento persistente de métricas
- **Dashboard web:** Interfaz web para visualización avanzada
- **Alertas múltiples:** Email, SMS, webhooks
- **Métricas adicionales:** Jitter, ancho de banda, pérdida de paquetes
- **Múltiples brokers:** Soporte para brokers remotos y en la nube
- **API REST:** Interfaz programática para integración


---

## 📋 Lista de Verificación de Instalación

Usa esta lista para verificar que todo esté configurado correctamente:

- Python 3.8+ instalado
- Entorno virtual creado y activado
- Dependencias instaladas (`python-telegram-bot`, `paho-mqtt`)
- Token de Telegram configurado en `mqtt_bot.py`
- Mosquitto MQTT Broker instalado
- Archivo de configuración `mosquitto.conf` creado
- Usuario MQTT `network_monitor` creado con contraseña `monitor123`
- Broker MQTT iniciado y ejecutándose
- MQTT Explorer instalado y configurado
- Conexión MQTT Explorer exitosa
- Regla de firewall para puerto 1883 creada
- Bot de Telegram iniciado sin errores
- Prueba de ping desde Telegram exitosa
- Datos aparecen en MQTT Explorer


---

## 👥 Creadores

- **Massiel Perozo** - Desarrollo y documentación
- **Jorge Ramírez** - Implementación y testing


---

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

---

## 🆘 Soporte

Si tienes problemas con la instalación o ejecución:

1. Revisa la sección de **Solución de Problemas**
2. Verifica que todos los **Requisitos del Sistema** estén cumplidos
3. Asegúrate de seguir el **orden exacto** de los pasos de instalación
4. Usa la **Lista de Verificación** para confirmar cada paso
5. Contacta a los creadores para soporte adicional


---

**¡Disfruta monitoreando tu red con este bot inteligente! 🤖📡**
