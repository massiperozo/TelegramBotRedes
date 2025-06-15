import logging
import subprocess
import re
import platform
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# --- 1. Configuración Inicial ---

# ¡IMPORTANTE!: Reemplaza 'YOUR_BOT_TOKEN' con el token que te dio BotFather
TOKEN = "7733059910:AAGxkZsxiIbHUgAojSSLKN_17Zm-CZU0xpM" 

# Intervalo de verificación para el monitoreo recurrente (en segundos)
MONITOR_INTERVAL_SECONDS = 15
# Número de solicitudes ping para el monitoreo recurrente (para una verificación rápida)
MONITOR_PING_COUNT = 1 

# Estados para la conversación
PING_STATE = 1
TRACEROUTE_STATE = 2
MONITOR_STATE = 3

# Configura el log
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- 2. Módulo de Captura de Comandos (Análisis de Salida) ---

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

# --- 3. Definición del Teclado Personalizado y Comandos ---

# Opciones para el menú principal
main_menu_keyboard = [
    [KeyboardButton("🌐 Ping Host"), KeyboardButton("📡 Traceroute Host")],
    [KeyboardButton("🟢 Iniciar Monitoreo"), KeyboardButton("🔴 Detener Monitoreo")],
    [KeyboardButton("📚 Ayuda")]
]

reply_markup = ReplyKeyboardMarkup(main_menu_keyboard, resize_keyboard=True, one_time_keyboard=False)

# --- 4. Bot de Telegram (Manejo de Comandos y Respuestas) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envía un mensaje de bienvenida y muestra el teclado personalizado."""
    user = update.effective_user
    await update.message.reply_html(
        f"👋 ¡Hola, {user.mention_html()}! Soy tu bot de monitoreo de red. \n"
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

async def handle_help_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el botón 'Ayuda' y muestra instrucciones detalladas."""
    help_message = (
        "📚 **Guía de Uso del Bot de Monitoreo de Redes**\n\n"
        "Aquí tienes las instrucciones para usar las funciones principales: 👇\n\n"
        "•   **🌐 Ping Host**: Si tocas este botón, o escribes `/ping`, te pediré que me envíes el **dominio o dirección IP** (ej. `google.com` o `8.8.8.8`) que deseas verificar. Luego ejecutaré un ping de 4 solicitudes y te mostraré la latencia promedio. ¡Ideal para chequear la conectividad! 🚀\n\n"
        "•   **📡 Traceroute Host**: Si tocas este botón, o escribes `/traceroute`, te pediré el **dominio o dirección IP** (ej. `google.com` o `8.8.8.8`) para trazar la ruta. Te mostraré todos los saltos que toma la conexión. ¡Útil para ver el camino de tus datos! 🛣️\n\n"
        "•   **🟢 Iniciar Monitoreo**: Al tocar este botón, o escribir `/start_monitor`, te pediré un **dominio o IP** para empezar a monitorearlo cada 15 segundos. Si el host deja de ser alcanzable, o vuelve a serlo, ¡te enviaré una **ALERTA**! 🚨\n\n"
        "•   **🔴 Detener Monitoreo**: Este botón, o el comando `/stop_monitor`, detendrá cualquier monitoreo recurrente que esté en curso. 🛑\n\n"
        "•   **📚 Ayuda**: ¡Este botón que acabas de presionar! Muestra esta guía completa. 📖\n\n"
        "¡Recuerda que si necesitas ingresar un dominio o IP, simplemente envíamelo después de seleccionar la acción! 😉\n\n"
        "--- --- ---\n\n"
        "📝 **Documentación Detallada de Redes**\n\n"
        "Para que entiendas mejor los resultados:\n\n"
        "### 🌐 ¿Qué es Ping?\n"
        "El comando `ping` es una herramienta de diagnóstico que mide la accesibilidad de un host en una red IP y el tiempo que tarda en enviar y recibir paquetes. Funciona enviando paquetes *ICMP Echo Request* al destino y esperando respuestas *ICMP Echo Reply*.\n\n"
        "**¿Cómo interpretar los resultados de Ping?**\n"
        "•   **Latencia (Tiempo de respuesta)**: Se mide en milisegundos (ms). Indica qué tan rápido responde el host. \n"
        "    •   `Menos de 50 ms`: Muy buena latencia. Ideal para juegos y aplicaciones en tiempo real. ✨\n"
        "    •   `50-150 ms`: Latencia aceptable. Suficiente para navegación y streaming. 👍\n"
        "    •   `Más de 150 ms`: Latencia alta. Puede causar retrasos notables y una experiencia lenta. 🐌\n"
        "•   **Pérdida de Paquetes**: Se expresa en porcentaje (%). Indica cuántos paquetes enviados no regresaron. \n"
        "    •   `0% de pérdida`: Conexión perfecta. ✅\n"
        "    •   `1-5% de pérdida`: Leve pérdida. Puede no ser notoria pero indica inestabilidad. ⚠️\n"
        "    •   `Más de 5% de pérdida`: Pérdida significativa. Causará interrupciones, desconexiones y lentitud. 💔\n"
        "•   **Host inalcanzable**: Si no se recibe ninguna respuesta, significa que el destino no está disponible, no responde a pings, o hay un problema de enrutamiento/firewall. 🚫\n\n"
        "### 📡 ¿Qué es Traceroute (Tracert)?\n"
        "El comando `traceroute` (o `tracert` en Windows) es una herramienta que muestra la ruta que toman los paquetes de datos para llegar a un destino. Lo hace enviando una serie de paquetes y midiendo el tiempo que tarda cada *salto* (router o dispositivo intermedio) en responder.\n\n"
        "**¿Cómo interpretar los resultados de Traceroute?**\n"
        "•   **Saltos**: Cada línea numerada representa un salto o un dispositivo (router) en la ruta. Verás la dirección IP de cada salto y el tiempo de respuesta.\n"
        "•   **Tiempos de respuesta por salto**: Si un salto específico muestra tiempos de respuesta muy altos, puede indicar un cuello de botella o congestión en ese punto de la red. ⏳\n"
        "•   **Asteriscos (`*`) o 'Request timed out'**: Esto significa que un salto no respondió dentro del tiempo esperado. Puede ser por:\n"
        "    •   **Firewall**: El dispositivo está bloqueando las solicitudes de `traceroute`. 🛡️\n"
        "    •   **Congestión**: El router está tan sobrecargado que no puede responder a tiempo. 🚦\n"
        "    •   **Problema de enrutamiento**: El paquete no pudo seguir la ruta. ❌\n"
        "•   **Número de saltos**: Un número excesivo de saltos puede indicar una ruta ineficiente o problemas. 📈\n\n"
        "### 🔔 ¿Qué es el Monitoreo Recurrente?\n"
        "Esta función permite que el bot **vigile continuamente** la accesibilidad de un host específico en segundo plano. En lugar de que tú tengas que pedir un `ping` cada vez, el bot lo hace automáticamente cada {MONITOR_INTERVAL_SECONDS} segundos.\n\n"
        "**¿Cómo interpretar las alertas de Monitoreo?**\n"
        "•   **🚨 ¡ALERTA! El host (...) se encuentra INALCANZABLE. 💔**: Esto significa que el host que estás monitoreando ha dejado de responder a los pings. Esto puede indicar que está caído, desconectado, o hay un problema grave en la red que impide la comunicación.\n"
        "•   **✅ ¡Atención! El host (...) ahora es ALCANZABLE de nuevo. 🎉**: Esta es una buena noticia. El host que previamente estaba inalcanzable ahora ha vuelto a responder a los pings, indicando que el problema se ha resuelto y la conectividad ha sido restaurada."
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
        else:
            response_message = (
                f"⚠️ El host `{user_input}` parece inalcanzable (pérdida de paquetes). 💔\n"
                f"```\n{result.get('output', 'Salida no disponible')}\n```"
            )
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

# --- 5. Módulo de Monitoreo de Alertas (Tareas en Segundo Plano) ---

async def monitor_host_periodically(chat_id: int, target: str, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Función que se ejecuta periódicamente para monitorear un host y enviar alertas."""
    last_state_reachable = True 
    logger.info(f"Iniciando monitoreo periódico para {target} en chat {chat_id}")

    while True:
        try:
            logger.info(f"Verificando {target}...")
            ping_result = execute_ping(target, count=MONITOR_PING_COUNT) 

            current_state_reachable = ping_result['success']
            
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
        "Recibirás alertas si cambia de estado. 🔔",
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

# --- 6. Función Principal (Iniciar el Bot) ---

def main() -> None:
    """Función principal para configurar e iniciar el bot de Telegram."""
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
    application.add_handler(MessageHandler(filters.Regex("^📚 Ayuda$"), handle_help_button))

    # Importante: Este manejador debe ir al final
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    # Manejador para comandos desconocidos (si escriben /algo_raro)
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))


    logger.info("Bot iniciado y escuchando mensajes de Telegram...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()