@echo off
echo ========================================
echo    INSTALACION MQTT PARA WINDOWS
echo ========================================
echo.

echo 1. Descargando Mosquitto MQTT Broker...
echo Visita: https://mosquitto.org/download/
echo Descarga la version para Windows (64-bit)
echo.

echo 2. Instalando dependencias Python...
pip install paho-mqtt
echo.

echo 3. Creando directorio de configuracion...
if not exist "C:\Program Files\mosquitto\config" mkdir "C:\Program Files\mosquitto\config"
echo.

echo 4. Configuracion completada!
echo.
echo PROXIMOS PASOS:
echo - Instalar Mosquitto desde el archivo descargado
echo - Ejecutar setup_mosquitto_config.bat como administrador
echo - Instalar MQTT Explorer desde: http://mqtt-explorer.com/
echo.
pause
