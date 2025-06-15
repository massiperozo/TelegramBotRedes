# 🤖 Bot de Monitoreo de Red en Telegram

Este es un bot de Telegram diseñado para ayudarte a diagnosticar y monitorear la conectividad de red de tus hosts. Puedes realizar **pings**, **traceroutes** y configurar un **monitoreo constante** para recibir alertas si un host se vuelve inalcanzable o vuelve a estar en línea.

---

## ✨ Características

- 🌐 **Ping:** Envía paquetes ICMP a un dominio o IP para medir la latencia y la pérdida de paquetes.
- 📡 **Traceroute:** Traza la ruta de los paquetes a un destino, mostrando todos los saltos intermedios (routers).
- 🟢 **Monitoreo Recurrente:** Configura el bot para que haga ping a un host cada 15 segundos y te alerte si cambia de estado (alcanzable/inalcanzable).
- 📚 **Documentación Integrada:** Accede a explicaciones detalladas sobre Ping, Traceroute y el monitoreo, incluyendo cómo interpretar los resultados, directamente desde el bot.
- 🗣️ **Interfaz Amigable:** Menú desplegable con botones y mensajes claros con emojis para una experiencia de usuario intuitiva.

---

## 🛠️ Requisitos

Antes de ejecutar el bot, asegúrate de tener instalado lo siguiente:

- **Python 3.8 o superior:** Puedes descargarlo desde [python.org](https://www.python.org/).
- **Comandos `ping` y `traceroute` (o `tracert` en Windows):** Suelen venir preinstalados en la mayoría de los sistemas operativos (Windows, Linux, macOS).

---

## 🚀 Instalación y Configuración

### 1. Clona el Repositorio (o descarga el código)

Si usas git:

```bash
git clone <URL_DE_TU_REPOSITORIO>
cd <nombre_de_la_carpeta_del_repositorio>
```

Si no, descarga los archivos del bot y navega al directorio donde los guardaste.

### 2. Crea un Entorno Virtual (Recomendado)

Es una buena práctica usar un entorno virtual para gestionar las dependencias de Python:

```bash
python -m venv venv
```

Activa el entorno virtual:

- **Windows:**

```bash
.\venv\Scripts\activate
```

- **macOS/Linux:**

```bash
source venv/bin/activate
```

### 3. Instala las Dependencias

El bot utiliza la librería `python-telegram-bot`. Instálala usando pip:

```bash
pip install python-telegram-bot httpx
```

> **Nota:** `httpx` es una dependencia de `python-telegram-bot`, pero es bueno asegurarnos que está explícitamente instalada si hubiera algún problema de compatibilidad indirecta.

### 4. Obtén tu Token de Bot de Telegram

Para que tu bot funcione, necesitas un token de la API de Telegram:

1. Abre Telegram y busca a `@BotFather`.
2. Inicia un chat con él y envía el comando `/newbot`.
3. Sigue las instrucciones de BotFather para darle un nombre a tu bot y un nombre de usuario (debe terminar en `bot`, ej. `MiMonitorBot`).
4. BotFather te proporcionará un token de acceso HTTP API. Cópialo; es una cadena larga de números y letras.

### 5. Configura el Archivo del Bot

Abre el archivo principal de tu bot (probablemente `monitor_bot.py` o similar) en tu editor de código preferido.

Busca la línea que dice:

```python
TOKEN = "YOUR_BOT_TOKEN"
```

Reemplaza `"YOUR_BOT_TOKEN"` con el token que obtuviste de BotFather. Asegúrate de que el token esté dentro de las comillas.

```python
TOKEN = "7733059910:AAGxkZsxiIbHUgAojSSLKN_17Zm-CZU0xpM"  # Ejemplo, usa tu token real
```

Guarda el archivo.

---

## ▶️ Ejecución del Bot

Una vez que hayas completado la configuración, puedes ejecutar el bot desde tu terminal:

```bash
python monitor_bot.py
```

El bot se iniciará y comenzará a escuchar los mensajes de Telegram. Deberías ver un mensaje en la terminal como: `Bot iniciado y escuchando mensajes de Telegram...`

---

## 💬 Cómo Usar el Bot en Telegram

1. **Inicia el bot:** Abre Telegram y busca el nombre de usuario de tu bot (el que le diste a BotFather, ej. `@MiMonitorBot`).
2. **Envía el comando `/start` al bot.**
3. El bot te dará la bienvenida y mostrará un menú desplegable con varias opciones.
4. **Usa los Botones:** Toca los botones del menú para interactuar. Por ejemplo:
   - Toca 🌐 **Ping Host:** El bot te pedirá el dominio o IP a pinear. Escribe `google.com` (o la IP) y envíalo.
   - Toca 🟢 **Iniciar Monitoreo:** El bot te pedirá el dominio o IP a monitorear. Envía el host y recibirás alertas periódicas.
   - Toca 📚 **Ayuda:** Para ver la guía completa de uso y la documentación de red.
5. **Comandos Directos:** También puedes escribir los comandos directamente si lo prefieres (ej., `/ping google.com` aunque el bot te pedirá el destino en un paso separado para mayor claridad).

---

## 🛑 Detener el Bot

Para detener el bot, simplemente presiona `Ctrl + C` en la terminal donde se está ejecutando el script.

---

## ⚠️ Notas Importantes

- El bot requiere una conexión a internet constante para comunicarse con la API de Telegram.
- El monitoreo recurrente solo estará activo mientras el script del bot esté en ejecución. Si el script se detiene, el monitoreo se pausará hasta que lo reinicies.
- Asegúrate de que los comandos `ping` y `traceroute` (`tracert`) estén disponibles en la ruta de tu sistema para que el bot pueda ejecutarlos.

## Creadores:
- Massiel Perozo
- Jorge Ramírez