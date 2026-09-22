import requests
import csv
import io
from pymongo import MongoClient

# 1. Configuración de MongoDB Atlas
MONGO_URI = "mongodb+srv://quezors191_db_user:gUCE0yKkTB4kV13L@admin.xdbxdz9.mongodb.net/?appName=admin"
client = MongoClient(MONGO_URI)
coleccion = client["antecedentes_db"]["sanciones"]

def actualizar_lista_ofac():
    print("Iniciando descarga masiva de la lista OFAC (Lista Clinton)...")
    url_ofac = "https://www.treasury.gov/ofac/downloads/sdn.csv"
    
    try:
        # Los servidores de EE.UU. bloquean bots básicos. Usamos un User-Agent para simular ser un navegador web.
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        respuesta = requests.get(url_ofac, headers=headers, timeout=60)
        respuesta.raise_for_status()
        
        # 2. Leer y parsear el CSV directamente desde la memoria
        contenido = respuesta.content.decode('utf-8', errors='replace')
        lector_csv = csv.reader(io.StringIO(contenido))
        
        registros_a_insertar = []
        
        # 3. Extraer los datos (El CSV de OFAC no tiene cabeceras; Nombre=Columna 1, Tipo=Columna 2)
        for fila in lector_csv:
            if len(fila) >= 3:
                nombre = fila[1].strip().upper()
                tipo_entidad = fila[2].strip().lower()
                
                # Clasificar si es persona física o empresa/embarcación
                tipo = "Persona Física" if tipo_entidad == "individual" else "Entidad / Empresa"
                
                if nombre:
                    registros_a_insertar.append({
                        "nombre_completo": nombre,
                        "fuente": "OFAC - SDN List (EE.UU.)",
                        "tipo": tipo,
                        "alerta": "ALTA"
                    })
        
        # 4. Inyectar datos a MongoDB Atlas
        if registros_a_insertar:
            print(f"Descarga completa. Limpiando registros antiguos e insertando {len(registros_a_insertar)} nuevos...")
            
            # Borrar los registros anteriores de OFAC para evitar duplicados
            coleccion.delete_many({"fuente": "OFAC - SDN List (EE.UU.)"})
            
            # Insertar la nueva lista masiva
            coleccion.insert_many(registros_a_insertar)
            print(f"¡Éxito total! Se han guardado {len(registros_a_insertar)} registros de la OFAC en tu base de datos.")
            
    except Exception as e:
        print(f"Error crítico en el proceso ETL de OFAC: {e}")

if __name__ == "__main__":
    actualizar_lista_ofac()