import paho.mqtt.client as mqtt
import json
import logging
from datetime import datetime

# Configuración MQTT
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_USERNAME = "network_monitor"
MQTT_PASSWORD = "monitor123"
MQTT_TOPIC = "mensaje_grupo"

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def on_connect(client, userdata, flags, rc):
    """Callback cuando se conecta al broker"""
    if rc == 0:
        logger.info("Suscriptor conectado al broker MQTT")
        client.subscribe(MQTT_TOPIC)
        logger.info(f"Suscrito al tópico: {MQTT_TOPIC}")
    else:
        logger.error(f"Error al conectar: {rc}")

def on_message(client, userdata, msg):
    """Callback cuando se recibe un mensaje"""
    try:
        # Decodificar el mensaje JSON
        message = json.loads(msg.payload.decode())
        timestamp = message.get('timestamp', 'N/A')
        msg_type = message.get('type', 'unknown')
        destination = message.get('destination', 'N/A')
        
        print(f"\n{'='*50}")
        print(f"📡 MENSAJE MQTT RECIBIDO")
        print(f"{'='*50}")
        print(f"⏰ Timestamp: {timestamp}")
        print(f"📋 Tipo: {msg_type}")
        print(f"🎯 Destino: {destination}")
        
        if msg_type == "ping":
            latency = message.get('latency_ms')
            success = message.get('success')
            print(f"🌐 Ping - Latencia: {latency}ms, Éxito: {success}")
            
        elif msg_type == "traceroute":
            hop_count = message.get('hop_count')
            success = message.get('success')
            print(f"📡 Traceroute - Saltos: {hop_count}, Éxito: {success}")
            
        elif msg_type == "monitoring":
            latency = message.get('latency_ms')
            success = message.get('success')
            chat_id = message.get('chat_id')
            print(f"🔔 Monitoreo - Chat: {chat_id}, Latencia: {latency}ms, Éxito: {success}")
        
        print(f"📄 Mensaje completo: {json.dumps(message, indent=2)}")
        print(f"{'='*50}\n")
        
    except json.JSONDecodeError:
        logger.error(f"Error al decodificar mensaje JSON: {msg.payload.decode()}")
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")

def on_disconnect(client, userdata, rc):
    """Callback cuando se desconecta"""
    logger.info("Desconectado del broker MQTT")

def main():
    """Función principal del suscriptor"""
    client = mqtt.Client()
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    try:
        logger.info(f"Conectando al broker MQTT en {MQTT_BROKER}:{MQTT_PORT}")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        print(f"\n🚀 SUSCRIPTOR MQTT INICIADO")
        print(f"📡 Broker: {MQTT_BROKER}:{MQTT_PORT}")
        print(f"📋 Tópico: {MQTT_TOPIC}")
        print(f"👤 Usuario: {MQTT_USERNAME}")
        print(f"⏳ Esperando mensajes... (Ctrl+C para salir)\n")
        
        # Mantener el cliente ejecutándose
        client.loop_forever()
        
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo suscriptor...")
        client.disconnect()
    except Exception as e:
        logger.error(f"Error en el suscriptor: {e}")

if __name__ == "__main__":
    main()
