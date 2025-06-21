import logging
import subprocess
import re
import platform
import asyncio
import json
import time
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import paho.mqtt.client as mqtt

# --- 1. Configuración Inicial ---

# ¡IMPORTANTE!: Reemplaza con tu token real
TOKEN = "7733059910:AAGxkZsxiIbHUgAojSSLKN_17Zm-CZU0xpM" 

# Configuración MQTT
MQTT_BROKER = "localhost"  # Broker local
MQTT_PORT = 1883
MQTT_USERNAME = "network_monitor"  # Usuario que crearemos
MQTT_PASSWORD = "monitor123"       # Contraseña que configuraremos
MQTT_TOPIC = "mensaje_grupo"       # Tópico especificado en el proyecto

# Intervalo de verificación para el monitoreo recurrente (en segundos)
MONITOR_INTERVAL_SECONDS = 15
# Número de solicitudes ping para el monitoreo recurrente
MONITOR_PING_COUNT = 1 

# Estados para la conversación
PING_STATE = 1
TRACEROUTE_STATE = 2
MONITOR_STATE = 3

# Cliente MQTT global
mqtt_client = None

# Configura el log
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- 2. Configuración y Cliente MQTT ---

def on_connect(client, userdata, flags, rc):
    """Callback cuando se conecta al broker MQTT"""
    if rc == 0:
        logger.info("Conectado exitosamente al broker MQTT")
    else:
        logger.error(f"Error al conectar al broker MQTT. Código: {rc}")

def on_publish(client, userdata, mid):
    """Callback cuando se publica un mensaje"""
    logger.info(f"Mensaje publicado con ID: {mid}")

def on_disconnect(client, userdata, rc):
    """Callback cuando se desconecta del broker"""
    logger.info("Desconectado del broker MQTT")

def setup_mqtt_client():
    """Configura y conecta el cliente MQTT"""
    global mqtt_client
    try:
        mqtt_client = mqtt.Client()
        mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        mqtt_client.on_connect = on_connect
        mqtt_client.on_publish = on_publish
        mqtt_client.on_disconnect = on_disconnect
        
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        logger.info("Cliente MQTT configurado y conectado")
        return True
    except Exception as e:
        logger.error(f"Error al configurar cliente MQTT: {e}")
        return False

def publish_to_mqtt(data):
    """Publica datos al broker MQTT"""
    global mqtt_client
    if mqtt_client is None:
        logger.error("Cliente MQTT no está configurado")
        return False
    
    try:
        # Agregar timestamp para series de tiempo
        data['timestamp'] = datetime.now().isoformat()
        data['unix_timestamp'] = int(time.time())
        
        message = json.dumps(data)
        result = mqtt_client.publish(MQTT_TOPIC, message, qos=1)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"Datos publicados a MQTT: {data}")
            return True
        else:
            logger.error(f"Error al publicar a MQTT: {result.rc}")
            return False
    except Exception as e:
        logger.error(f"Error al publicar datos MQTT: {e}")
        return False

# --- 3. Módulo de Captura de Comandos (Análisis de Salida) ---

def execute_ping(destination: str, count: int = 4) -> dict:
    """
    Ejecuta un comando 'ping' al destino especificado y parsea la salida
    para obtener la latencia promedio y si fue exitoso.
    Retorna un diccionario con 'latency_ms', 'success' o 'error'.
    """
    try:
        if platform.system() == "Windows":
            command = ['ping', '-n', str(count), destination] 
        else:
            command = ['ping', '-c', str(count), destination]
        
        process = subprocess.run(command, capture_output=True, text=True, check=False)
        output = process.stdout
        
        latency = None
        success = False

        packets_match = re.search(r'enviados = (\d+), recibidos = (\d+)', output)
        if packets_match and int(packets_match.group(2)) > 0:
            success = True

        if success:
            match_latency_unix = re.search(r'min/avg/max/[^=]*=\s*[\d.]+/([\d.]+)/[\d.]+', output)
            if match_latency_unix:
                latency = float(match_latency_unix.group(1))
            else:
                match_latency_windows_en = re.search(r'Average = ([\d.]+)ms', output)
                match_latency_windows_es = re.search(r'Media = ([\d.]+)ms', output)

                if match_latency_windows_en:
                    latency = float(match_latency_windows_en.group(1))
                elif match_latency_windows_es: 
                    latency = float(match_latency_windows_es.group(1))
        
        return {"latency_ms": latency, "success": success, "output": output}

    except FileNotFoundError:
        return {"error": "El comando 'ping' no fue encontrado en el sistema. Asegúrate de que está en el PATH."}
    except Exception as e:
        logger.error(f"Error inesperado al ejecutar ping: {e}")
        return {"error": f"Ocurrió un error inesperado al hacer ping: {e}"}

def execute_traceroute(destination: str) -> dict:
    """
    Ejecuta un comando 'traceroute' (o 'tracert' en Windows) y parsear la salida
    para obtener la lista de saltos y el conteo.
    Retorna un diccionario con 'hops' (lista de IPs/timeouts), 'hop_count', 'success' o 'error'.
    """
    hops = []
    success = False
    try:
        if platform.system() == "Windows":
            command = ['tracert', '-d', destination] 
        else:
            command = ['traceroute', '-n', destination] 
        
        process = subprocess.run(command, capture_output=True, text=True, check=False, timeout=60)
        output = process.stdout
        
        if "Request timed out" not in output and "***" not in output: 
             if len(output.splitlines()) > 5:
                success = True

        hop_pattern = re.compile(r'^\s*\d+\s+((?:\*|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})|\S+).*$')

        for line in output.splitlines():
            match = hop_pattern.match(line)
            if match:
                ip_or_star = match.group(1).strip()
                if ip_or_star != '*':
                    hops.append(ip_or_star)
                else:
                    hops.append("Timeout (*)")
                    
        return {"hops": hops, "hop_count": len(hops), "success": success, "output": output}

    except FileNotFoundError:
        return {"error": "El comando 'traceroute' o 'tracert' no fue encontrado en el sistema."}
    except subprocess.TimeoutExpired:
        return {"error": "El comando traceroute/tracert excedió el tiempo límite. El destino podría ser inalcanzable."}
    except Exception as e:
        logger.error(f"Error inesperado al ejecutar traceroute: {e}")
        return {"error": f"Ocurrió un error inesperado al hacer traceroute: {e}"}

# --- 4. Definición del Teclado Personalizado y Comandos ---

# Opciones para el menú principal
main_menu_keyboard = [
    [KeyboardButton("🌐 Ping Host"), KeyboardButton("📡 Traceroute Host")],
    [KeyboardButton("🟢 Iniciar Monitoreo"), KeyboardButton("🔴 Detener Monitoreo")],
    [KeyboardButton("📊 Estado MQTT"), KeyboardButton("📚 Ayuda")]
]

reply_markup = ReplyKeyboardMarkup(main_menu_keyboard, resize_keyboard=True, one_time_keyboard=False)

# --- 5. Bot de Telegram (Manejo de Comandos y Respuestas) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envía un mensaje de bienvenida y muestra el teclado personalizado."""
    user = update.effective_user
    await update.message.reply_html(
        f"👋 ¡Hola, {user.mention_html()}! Soy tu bot de monitoreo de red con MQTT. \n"
        "Selecciona una opción del teclado para empezar a diagnosticar tu red. 👇",
        reply_markup=reply_markup 
    )

async def handle_ping_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el botón 'Ping Host', pide el destino."""
    await update.message.reply_text(
        "Por favor, envíame el **dominio o IP** 🎯 que deseas pinear (ej. `google.com` o `8.8.8.8`).",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data['state'] = PING_STATE

async def handle_traceroute_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el botón 'Traceroute Host', pide el destino."""
    await update.message.reply_text(
        "Por favor, envíame el **dominio o IP** 🗺️ para el traceroute (ej. `google.com` o `8.8.8.8`).",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data['state'] = TRACEROUTE_STATE

async def handle_start_monitor_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el botón 'Iniciar Monitoreo', pide el destino."""
    await update.message.reply_text(
        "Por favor, envíame el **dominio o IP** del host que deseas monitorear recurrentemente. 🔔",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data['state'] = MONITOR_STATE

async def handle_stop_monitor_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el botón 'Detener Monitoreo'."""
    await stop_monitor_command(update, context)
    await update.message.reply_text("¿Qué más puedo hacer por ti? 🤔", reply_markup=reply_markup)

async def handle_mqtt_status_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el botón 'Estado MQTT'."""
    global mqtt_client
    if mqtt_client and mqtt_client.is_connected():
        status_message = (
            f"📊 **Estado MQTT**\n\n"
            f"🟢 **Conectado** al broker: `{MQTT_BROKER}:{MQTT_PORT}`\n"
            f"📡 **Tópico**: `{MQTT_TOPIC}`\n"
            f"👤 **Usuario**: `{MQTT_USERNAME}`\n"
            f"⏰ **Intervalo de monitoreo**: {MONITOR_INTERVAL_SECONDS} segundos"
        )
    else:
        status_message = (
            f"📊 **Estado MQTT**\n\n"
            f"🔴 **Desconectado** del broker MQTT\n"
            f"🔧 Verifica que el broker esté ejecutándose en `{MQTT_BROKER}:{MQTT_PORT}`"
        )
    
    await update.message.reply_text(status_message, parse_mode='Markdown', reply_markup=reply_markup)

async def handle_help_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el botón 'Ayuda' y muestra instrucciones detalladas."""
    help_message = (
        "📚 **Guía de Uso del Bot de Monitoreo de Redes con MQTT**\n\n"
        "Aquí tienes las instrucciones para usar las funciones principales: 👇\n\n"
        "•   **🌐 Ping Host**: Ejecuta ping y publica resultados a MQTT\n"
        "•   **📡 Traceroute Host**: Ejecuta traceroute y publica saltos a MQTT\n"
        "•   **🟢 Iniciar Monitoreo**: Monitoreo continuo con alertas y datos MQTT\n"
        "•   **🔴 Detener Monitoreo**: Detiene el monitoreo activo\n"
        "•   **📊 Estado MQTT**: Muestra el estado de conexión MQTT\n"
        "•   **📚 Ayuda**: Esta guía completa\n\n"
        f"📡 **Configuración MQTT:**\n"
        f"Broker: `{MQTT_BROKER}:{MQTT_PORT}`\n"
        f"Tópico: `{MQTT_TOPIC}`\n"
        f"Usuario: `{MQTT_USERNAME}`\n\n"
        "Los datos se publican en formato JSON con timestamp para series de tiempo. "
        "Usa MQTT Explorer para visualizar los datos en tiempo real. 📈"
    )
    await update.message.reply_text(help_message, parse_mode='Markdown', reply_markup=reply_markup)

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Maneja el texto que el usuario envía DESPUÉS de haber seleccionado una opción del menú.
    """
    user_input = update.message.text.strip()
    current_state = context.user_data.get('state')

    if current_state == PING_STATE:
        context.user_data.pop('state')
        await update.message.reply_text(f"🌐 Realizando ping a `{user_input}`... por favor espera. ⏳", parse_mode='Markdown')
        result = execute_ping(user_input)
        
        if "error" in result:
            response_message = f"❌ Error al monitorear `{user_input}`: {result['error']}"
        elif result['success']:
            latency_str = f"{result['latency_ms']:.2f} ms" if result['latency_ms'] is not None else "No disponible"
            response_message = (
                f"✅ Resultados de Ping para `{user_input}`:\n"
                f"Latencia promedio: `{latency_str}`"
            )
            
            # Publicar a MQTT
            mqtt_data = {
                "type": "ping",
                "destination": user_input,
                "latency_ms": result['latency_ms'],
                "success": result['success']
            }
            if publish_to_mqtt(mqtt_data):
                response_message += "\n📡 Datos enviados a MQTT ✅"
            else:
                response_message += "\n⚠️ Error al enviar datos a MQTT"
        else:
            response_message = (
                f"⚠️ El host `{user_input}` parece inalcanzable (pérdida de paquetes). 💔\n"
                f"```\n{result.get('output', 'Salida no disponible')}\n```"
            )
            
            # Publicar fallo a MQTT
            mqtt_data = {
                "type": "ping",
                "destination": user_input,
                "latency_ms": None,
                "success": False,
                "error": "Host inalcanzable"
            }
            publish_to_mqtt(mqtt_data)
            
        await update.message.reply_text(response_message, parse_mode='Markdown', reply_markup=reply_markup)

    elif current_state == TRACEROUTE_STATE:
        context.user_data.pop('state')
        await update.message.reply_text(f"📡 Realizando traceroute a `{user_input}`... esto puede tardar un poco. ⏳", parse_mode='Markdown')
        result = execute_traceroute(user_input)
        
        if "error" in result:
            response_message = f"❌ Error al realizar traceroute a `{user_input}`: {result['error']}"
        elif result['success']:
            if result['hops']:
                hops_list_str = "\n".join([f"  {i+1}. `{hop}`" for i, hop in enumerate(result['hops'])])
                response_message = (
                    f"✅ Saltos para `{user_input}` ({result['hop_count']} saltos): 🗺️\n"
                    f"{hops_list_str}"
                )
                
                # Publicar a MQTT
                mqtt_data = {
                    "type": "traceroute",
                    "destination": user_input,
                    "hop_count": result['hop_count'],
                    "hops": result['hops'],
                    "success": result['success']
                }
                if publish_to_mqtt(mqtt_data):
                    response_message += "\n📡 Datos enviados a MQTT ✅"
                else:
                    response_message += "\n⚠️ Error al enviar datos a MQTT"
            else:
                response_message = f"⚠️ No se pudieron determinar los saltos para `{user_input}`. El destino podría ser inalcanzable. 🤔"
        else:
            response_message = (
                f"⚠️ No se pudo completar el traceroute a `{user_input}`. 💔\n"
                f"```\n{result.get('output', 'Salida no disponible')}\n```"
            )
            
        await update.message.reply_text(response_message, parse_mode='Markdown', reply_markup=reply_markup)

    elif current_state == MONITOR_STATE:
        context.user_data.pop('state')
        context.args = [user_input] 
        await start_monitor_command(update, context)

    else:
        await update.message.reply_text(
            f"🤔 No entiendo '{user_input}'. Por favor, usa los botones del menú o `/help`.",
            reply_markup=reply_markup
        )
        logger.info(f"Comando de texto no reconocido: {user_input}")

# --- 6. Módulo de Monitoreo de Alertas (Tareas en Segundo Plano) ---

async def monitor_host_periodically(chat_id: int, target: str, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Función que se ejecuta periódicamente para monitorear un host y enviar alertas."""
    last_state_reachable = True 
    logger.info(f"Iniciando monitoreo periódico para {target} en chat {chat_id}")

    while True:
        try:
            logger.info(f"Verificando {target}...")
            ping_result = execute_ping(target, count=MONITOR_PING_COUNT) 

            current_state_reachable = ping_result['success']
            
            # Publicar datos de monitoreo a MQTT
            mqtt_data = {
                "type": "monitoring",
                "destination": target,
                "latency_ms": ping_result.get('latency_ms'),
                "success": current_state_reachable,
                "chat_id": chat_id
            }
            publish_to_mqtt(mqtt_data)
            
            if current_state_reachable and not last_state_reachable:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"✅ ¡Atención! El host `{target}` ahora es **ALCANZABLE** de nuevo. 🎉",
                    parse_mode='Markdown'
                )
                logger.info(f"Host {target} recuperado.")
            elif not current_state_reachable and last_state_reachable:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"🚨 ¡ALERTA! El host `{target}` se encuentra **INALCANZABLE**. 💔",
                    parse_mode='Markdown'
                )
                logger.warning(f"Host {target} INALCANZABLE.")
            elif not current_state_reachable and not last_state_reachable:
                logger.info(f"Host {target} sigue INALCANZABLE.")
            else:
                logger.info(f"Host {target} sigue alcanzable.")

            last_state_reachable = current_state_reachable

        except asyncio.CancelledError:
            logger.info(f"Monitoreo para {target} en chat {chat_id} ha sido CANCELADO.")
            break 
        except Exception as e:
            logger.error(f"Error en el monitoreo periódico de {target}: {e}")
        
        await asyncio.sleep(MONITOR_INTERVAL_SECONDS) 

async def start_monitor_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el comando /start_monitor <destino>.
    Inicia el monitoreo recurrente para el destino especificado."""
    if not context.args:
        await update.message.reply_text("Por favor, especifica un host para monitorear. Ejemplo: `/start_monitor google.com`", parse_mode='Markdown')
        return

    target_host = context.args[0]
    chat_id = update.effective_chat.id

    if 'monitoring_task' in context.bot_data and context.bot_data['monitoring_task'] is not None:
        if context.bot_data['monitoring_target'] == target_host:
            await update.message.reply_text(f"Ya estoy monitoreando `{target_host}`. 🧐", parse_mode='Markdown')
        else:
            await update.message.reply_text(f"Ya estoy monitoreando `{context.bot_data['monitoring_target']}`. Por favor, `/stop_monitor` primero si quieres cambiar de host. ⚠️", parse_mode='Markdown')
        return

    context.bot_data['monitoring_target'] = target_host
    context.bot_data['monitoring_chat_id'] = chat_id
    context.bot_data['monitoring_task'] = asyncio.create_task(
        monitor_host_periodically(chat_id, target_host, context)
    )
    
    await update.message.reply_text(
        f"✅ Monitoreo recurrente iniciado para `{target_host}` cada {MONITOR_INTERVAL_SECONDS} segundos. "
        "Recibirás alertas si cambia de estado y los datos se enviarán a MQTT. 🔔📡",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    logger.info(f"Comando /start_monitor recibido para {target_host} en chat {chat_id}")

async def stop_monitor_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el comando /stop_monitor. Detiene el monitoreo recurrente si está activo."""
    if 'monitoring_task' in context.bot_data and context.bot_data['monitoring_task'] is not None:
        context.bot_data['monitoring_task'].cancel()
        context.bot_data['monitoring_task'] = None
        target_host = context.bot_data.get('monitoring_target', 'un host desconocido')
        
        await update.message.reply_text(
            f"🚫 Monitoreo recurrente para `{target_host}` detenido. ¡Descanso! 😴",
            parse_mode='Markdown'
        )
        logger.info(f"Comando /stop_monitor recibido. Monitoreo para {target_host} detenido.")
        context.bot_data.pop('monitoring_target', None)
        context.bot_data.pop('monitoring_chat_id', None)

    else:
        await update.message.reply_text("No hay ningún monitoreo recurrente activo para detener. ✨", parse_mode='Markdown')
        logger.info("Comando /stop_monitor recibido, pero no había monitoreo activo.")

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responde a comandos que el bot no reconoce."""
    await update.message.reply_text(
        f"🤔 Lo siento, no reconozco el comando '{update.message.text}'. "
        "Usa los botones del menú o `/help` para guiarte. 🤷‍♂️",
        reply_markup=reply_markup
    )

# --- 7. Función Principal (Iniciar el Bot) ---

def main() -> None:
    """Función principal para configurar e iniciar el bot de Telegram."""
    # Configurar cliente MQTT
    if not setup_mqtt_client():
        logger.error("No se pudo configurar el cliente MQTT. El bot funcionará sin MQTT.")
    
    application = Application.builder().token(TOKEN).build()

    # Manejadores para comandos tradicionales (si el usuario los escribe)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ping", handle_ping_button))
    application.add_handler(CommandHandler("traceroute", handle_traceroute_button))
    application.add_handler(CommandHandler("start_monitor", handle_start_monitor_button))
    application.add_handler(CommandHandler("stop_monitor", handle_stop_monitor_button))
    application.add_handler(CommandHandler("help", handle_help_button))
    
    # Manejadores para los botones del menú (texto plano)
    application.add_handler(MessageHandler(filters.Regex("^🌐 Ping Host$"), handle_ping_button))
    application.add_handler(MessageHandler(filters.Regex("^📡 Traceroute Host$"), handle_traceroute_button))
    application.add_handler(MessageHandler(filters.Regex("^🟢 Iniciar Monitoreo$"), handle_start_monitor_button))
    application.add_handler(MessageHandler(filters.Regex("^🔴 Detener Monitoreo$"), handle_stop_monitor_button))
    application.add_handler(MessageHandler(filters.Regex("^📊 Estado MQTT$"), handle_mqtt_status_button))
    application.add_handler(MessageHandler(filters.Regex("^📚 Ayuda$"), handle_help_button))

    # Importante: Este manejador debe ir al final
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    # Manejador para comandos desconocidos (si escriben /algo_raro)
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    logger.info("Bot iniciado y escuchando mensajes de Telegram...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
