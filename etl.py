import pandas as pd
from pymongo import MongoClient
import requests
import io
import xml.etree.ElementTree as ET
import json

# Conexión maestra a MongoDB Atlas
MONGO_URI = "mongodb+srv://quezors191_db_user:gUCE0yKkTB4kV13L@admin.xdbxdz9.mongodb.net/?appName=admin"
client = MongoClient(MONGO_URI)
coleccion = client["antecedentes_db"]["sanciones"]

def extraer_y_transformar_ofac():
    print("📥 1. Descargando OFAC (EE. UU.)...")
    url = "https://www.treasury.gov/ofac/downloads/sdn.csv"
    columnas = ["id_entidad", "nombre_completo", "tipo", "programas", "titulo", "call_sign", "tipo_buque", "tonelaje", "grt", "bandera", "propietario", "observaciones"]
    response = requests.get(url)
    df = pd.read_csv(io.StringIO(response.text), names=columnas, header=None)
    df = df[df['tipo'].str.strip().str.lower() == 'individual'] 
    df_limpio = df[['id_entidad', 'nombre_completo', 'programas', 'titulo', 'observaciones']].copy()
    df_limpio['nombre_completo'] = df_limpio['nombre_completo'].str.upper()
    df_limpio = df_limpio.fillna("No registrado")
    df_limpio['fuente'] = 'OFAC - Lista SDN (EE. UU.)'
    return df_limpio.to_dict(orient='records')

def extraer_y_transformar_onu():
    print("📥 2. Descargando ONU (Internacional)...")
    try:
        url = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"
        response = requests.get(url, timeout=20)
        root = ET.fromstring(response.content)
        datos_onu = []
        for individuo in root.findall('.//INDIVIDUAL'):
            nombres = [nodo.text.strip() for tag in ['FIRST_NAME', 'SECOND_NAME', 'THIRD_NAME'] if (nodo := individuo.find(tag)) is not None and nodo.text]
            nodo_obs = individuo.find('.//COMMENTS1')
            observaciones = nodo_obs.text.strip() if nodo_obs is not None and nodo_obs.text else "No registrado"
            nodo_prog = individuo.find('UN_LIST_TYPE')
            datos_onu.append({
                "id_entidad": individuo.find('DATAID').text if individuo.find('DATAID') is not None else "N/A",
                "nombre_completo": " ".join(nombres).upper(),
                "programas": nodo_prog.text if nodo_prog is not None else "No especificado",
                "fuente": "ONU - Consejo de Seguridad",
                "observaciones": observaciones
            })
        return datos_onu
    except Exception:
        print("⚠️ Error descargando ONU, saltando fuente...")
        return []

def extraer_opensanctions():
    print("📥 3. Descargando OpenSanctions (Mundo)... (Puede tardar 2-3 mins)")
    url = "https://data.opensanctions.org/datasets/latest/sanctions/targets.nested.json"
    datos_os = []
    try:
        with requests.get(url, stream=True, timeout=30) as respuesta:
            for linea in respuesta.iter_lines():
                if linea:
                    registro = json.loads(linea)
                    if registro.get("schema") == "Person":
                        prop = registro.get("properties", {})
                        nombres = prop.get("name", ["No registrado"])
                        agencias = registro.get("datasets", ["GLOBAL"])
                        fuente = "OPENSANCTIONS (" + ", ".join(agencias).upper() + ")"
                        observaciones = f"Nacionalidad: {', '.join(prop.get('nationality', ['N/A']))}; DOB {', '.join(prop.get('birthDate', ['N/A']))};"
                        
                        datos_os.append({
                            "id_entidad": registro.get("id", "N/A"),
                            "nombre_completo": nombres[0].upper(),
                            "programas": "SANCIONES INTERNACIONALES",
                            "fuente": fuente,
                            "observaciones": observaciones
                        })
    except Exception as e:
        print(f"⚠️ Error con OpenSanctions: {e}")
    return datos_os

def cargar_a_mongodb(datos):
    if not datos:
        print("❌ No hay datos para subir. Revisa tu conexión.")
        return

    print(f"\n💾 Preparando {len(datos)} registros para Atlas...")
    coleccion.delete_many({}) # Purgamos los datos viejos
    
    # NUEVO: Inserción en Lotes (Batches) para que Atlas no bloquee la conexión
    lote_tamano = 5000
    for i in range(0, len(datos), lote_tamano):
        lote = datos[i:i + lote_tamano]
        coleccion.insert_many(lote)
        print(f"   -> Subidos exitosamente {i + len(lote)} / {len(datos)} registros...")
        
    print("\n✅ ¡ETL COMPLETADO CON ÉXITO! Tu base de datos global está 100% activa.")

if __name__ == "__main__":
    print("🚀 Iniciando Pipeline de Datos hacia Atlas...")
    datos_totales = extraer_y_transformar_ofac() + extraer_y_transformar_onu() + extraer_opensanctions()
    cargar_a_mongodb(datos_totales)