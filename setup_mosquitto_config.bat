@echo off
echo ========================================
echo   CONFIGURACION MOSQUITTO BROKER
echo ========================================
echo.
echo NOTA: Ejecuta este archivo como ADMINISTRADOR
echo.

echo Creando archivo de configuracion...

echo # Configuracion Mosquitto para Proyecto de Redes > "C:\Program Files\mosquitto\mosquitto.conf"
echo # Puerto de escucha >> "C:\Program Files\mosquitto\mosquitto.conf"
echo listener 1883 >> "C:\Program Files\mosquitto\mosquitto.conf"
echo. >> "C:\Program Files\mosquitto\mosquitto.conf"
echo # Permitir conexiones anonimas (para pruebas) >> "C:\Program Files\mosquitto\mosquitto.conf"
echo allow_anonymous false >> "C:\Program Files\mosquitto\mosquitto.conf"
echo. >> "C:\Program Files\mosquitto\mosquitto.conf"
echo # Archivo de contraseñas >> "C:\Program Files\mosquitto\mosquitto.conf"
echo password_file C:\Program Files\mosquitto\passwd >> "C:\Program Files\mosquitto\mosquitto.conf"
echo. >> "C:\Program Files\mosquitto\mosquitto.conf"
echo # Logs >> "C:\Program Files\mosquitto\mosquitto.conf"
echo log_dest file C:\Program Files\mosquitto\mosquitto.log >> "C:\Program Files\mosquitto\mosquitto.conf"
echo log_type all >> "C:\Program Files\mosquitto\mosquitto.conf"

echo.
echo Creando usuario y contraseña...
cd "C:\Program Files\mosquitto"
mosquitto_passwd -c passwd network_monitor
echo.
echo Ingresa la contraseña: monitor123
echo.

echo Configuracion completada!
echo.
echo Para iniciar el broker ejecuta:
echo mosquitto -c "C:\Program Files\mosquitto\mosquitto.conf"
echo.
pause
