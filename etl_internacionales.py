import pandas as pd
from pymongo import MongoClient
import requests
from io import StringIO

# Conexión a tu MongoDB
MONGO_URI = "mongodb+srv://quezors191_db_user:gUCE0yKkTB4kV13L@admin.xdbxdz9.mongodb.net/?appName=admin"
client = MongoClient(MONGO_URI)
db = client["antecedentes_db"]
coleccion = db["sanciones"]

# URLs directas de los CSVs de OpenSanctions
FUENTES_INTERNACIONALES = {
    "INTERPOL (Notificaciones Rojas)": "https://data.opensanctions.org/datasets/latest/interpol_red_notices/targets.simple.csv",
    "UNIÓN EUROPEA (Sanciones)": "https://data.opensanctions.org/datasets/latest/eu_fsf/targets.simple.csv"
}

def actualizar_listas_internacionales():
    print("Iniciando extracción de Interpol, Unión Europea y State Dept...")
    registros_totales = []
    
    for nombre_fuente, url in FUENTES_INTERNACIONALES.items():
        print(f"Descargando {nombre_fuente}...")
        try:
            # Simulamos ser un navegador para que no nos bloqueen la descarga
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                # Pandas lee el CSV en memoria al instante
                df = pd.read_csv(StringIO(response.text), low_memory=False)
                
                # Descartamos los registros que no tengan nombre
                df = df.dropna(subset=['name'])
                
                for index, row in df.iterrows():
                    nombre = str(row['name']).strip().upper()
                    
                    # Extraemos contexto adicional
                    paises = str(row.get('countries', ''))
                    paises = paises if paises != 'nan' else "No especificado"
                    
                    nacimiento = str(row.get('birth_dates', ''))
                    nacimiento = nacimiento if nacimiento != 'nan' else "No especificado"
                    
                    alias = str(row.get('aliases', ''))
                    alias = alias if alias != 'nan' else "Ninguno"

                    observaciones = f"Nacionalidad/Países: {paises} | Fecha Nacimiento: {nacimiento} | Alias: {alias}"
                    
                    doc = {
                        "nombre_completo": nombre,
                        "programas": "SANCIONES INTERNACIONALES",
                        "fuente": f"OPENSANCTIONS - {nombre_fuente}",
                        "observaciones": observaciones
                    }
                    registros_totales.append(doc)
                print(f"✅ {nombre_fuente}: Descargada y procesada.")
            else:
                print(f"❌ Error al descargar {nombre_fuente}: Código {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error procesando {nombre_fuente}: {e}")

    if registros_totales:
        print(f"\nSe consolidaron {len(registros_totales)} criminales y terroristas.")
        
        # Eliminamos SOLO los registros anteriores de Interpol/EU/FTO para no duplicar, respetando los de OFAC y ONU
        print("Limpiando registros internacionales antiguos en MongoDB...")
        coleccion.delete_many({"fuente": {"$regex": "OPENSANCTIONS - "}})
        
        print("Inyectando nueva base de datos...")
        coleccion.insert_many(registros_totales)
        print("🚀 ¡Base de datos de Interpol, EU y FTO actualizada con éxito!")
    else:
        print("No se generaron registros nuevos.")

if __name__ == "__main__":
    actualizar_listas_internacionales()