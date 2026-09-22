import requests
import xml.etree.ElementTree as ET
from pymongo import MongoClient

# 1. Configuración de MongoDB Atlas
MONGO_URI = "mongodb+srv://quezors191_db_user:gUCE0yKkTB4kV13L@admin.xdbxdz9.mongodb.net/?appName=admin"
client = MongoClient(MONGO_URI)
coleccion = client["antecedentes_db"]["sanciones"]

def actualizar_lista_onu():
    print("Iniciando descarga de la lista consolidada de la ONU...")
    url_onu = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"
    
    try:
        respuesta = requests.get(url_onu, timeout=30)
        respuesta.raise_for_status()
        
        # 2. Parsear el archivo XML
        root = ET.fromstring(respuesta.content)
        registros_a_insertar = []
        
        # 3. Buscar a todos los individuos en el XML
        for individual in root.findall('.//INDIVIDUAL'):
            first_name = individual.find('.//FIRST_NAME')
            second_name = individual.find('.//SECOND_NAME')
            third_name = individual.find('.//THIRD_NAME')
            
            # Limpiar y concatenar nombres
            partes_nombre = [
                n.text for n in [first_name, second_name, third_name] 
                if n is not None and n.text
            ]
            nombre_completo = " ".join(partes_nombre).strip().upper()
            
            if nombre_completo:
                registros_a_insertar.append({
                    "nombre_completo": nombre_completo,
                    "fuente": "ONU - Consejo de Seguridad",
                    "tipo": "Persona Física",
                    "alerta": "ALTA"
                })
        
        # 4. Inyectar datos a MongoDB Atlas
        if registros_a_insertar:
            # Borrar los registros anteriores de la ONU para no duplicar datos
            coleccion.delete_many({"fuente": "ONU - Consejo de Seguridad"})
            # Insertar la lista nueva
            coleccion.insert_many(registros_a_insertar)
            print(f"¡Éxito! Se han guardado {len(registros_a_insertar)} sancionados de la ONU en la base de datos.")
            
    except Exception as e:
        print(f"Error crítico en el proceso ETL: {e}")

if __name__ == "__main__":
    actualizar_lista_onu()