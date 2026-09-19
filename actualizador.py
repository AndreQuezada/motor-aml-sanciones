import schedule
import time
import subprocess
from datetime import datetime

def ejecutar_etl():
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚀 DESPERTANDO AL ROBOT ETL...")
    print("Iniciando descarga y actualización de listas globales. Por favor, no apagues el sistema.")
    
    # Esta línea es la que presiona "Enter" por ti para ejecutar el ETL
    resultado = subprocess.run(["python", "etl.py"], capture_output=True, text=True)
    
    if resultado.returncode == 0:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✅ ACTUALIZACIÓN COMPLETADA CON ÉXITO.")
        print("La base de datos tiene los sancionados del día de hoy. Volviendo a dormir...")
    else:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ❌ ERROR DURANTE LA ACTUALIZACIÓN:")
        print(resultado.stderr)

# ---------------------------------------------------------
# CONFIGURACIÓN DEL RELOJ
# ---------------------------------------------------------

# MODO PRODUCCIÓN: Se actualiza todos los días a las 2:00 AM (cuando nadie usa el sistema)
schedule.every().day.at("02:00").do(ejecutar_etl)

# MODO PRUEBA: Quita el "#" de la línea de abajo para que se actualice cada 2 minutos y puedas ver cómo funciona hoy.
#schedule.every(2).minutes.do(ejecutar_etl)

print("🤖 Robot Actualizador Iniciado.")
print("El sistema está monitoreando el reloj en segundo plano...")
print("Presiona Ctrl + C en esta terminal si deseas apagar el robot.")

# Bucle infinito: Mantiene al programa vivo revisando la hora constantemente
while True:
    schedule.run_pending()
    time.sleep(30) # Revisa su reloj cada 30 segundos para no consumir memoria