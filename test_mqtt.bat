@echo off
echo ========================================
echo        PRUEBA DE CONEXION MQTT
echo ========================================
echo.

echo Probando conexion al broker...
echo.

cd "C:\Program Files\mosquitto"

echo 1. Publicando mensaje de prueba...
mosquitto_pub -h localhost -p 1883 -u network_monitor -P monitor123 -t mensaje_grupo -m "{\"type\":\"test\",\"message\":\"Conexion exitosa\",\"timestamp\":\"2024-01-01T12:00:00\"}"

echo.
echo 2. Si no hay errores, la conexion es exitosa!
echo.
pause
