@echo off
echo ========================================
echo      INICIANDO MOSQUITTO BROKER
echo ========================================
echo.

cd "C:\Program Files\mosquitto"
echo Iniciando broker MQTT en puerto 1883...
echo Presiona Ctrl+C para detener
echo.

mosquitto -c mosquitto.conf -v
