from fastapi import FastAPI
from pydantic import BaseModel
from pymongo import MongoClient
from thefuzz import process, fuzz
import re
from deep_translator import GoogleTranslator

app = FastAPI(title="API de Antecedentes", version="1.0")

@app.get("/")
def ping():
    return {"mensaje": "El motor AML está despierto y funcionando"}

# Conexión maestra a MongoDB Atlas
MONGO_URI = "mongodb+srv://quezors191_db_user:gUCE0yKkTB4kV13L@admin.xdbxdz9.mongodb.net/?appName=admin"
client = MongoClient(MONGO_URI)
coleccion = client["antecedentes_db"]["sanciones"]

class ConsultaRequest(BaseModel):
    cedula: str
    nombre: str
    apellido: str

def traducir_fuentes(fuentes_crudas):
    if "OPENSANCTIONS" in fuentes_crudas:
        traducciones_agencias = {
            "UA_": "Ucrania", "NZ_": "Nueva Zelanda", "EU_": "Unión Europea",
            "FR_": "Francia", "MC_": "Mónaco", "CA_": "Canadá", "GB_": "Reino Unido",
            "AU_": "Australia", "CH_": "Suiza", "BE_": "Bélgica", "JP_": "Japón",
            "US_": "EE. UU.", "UN_": "ONU", "PL_": "Polonia", "IL_": "Israel"
        }
        paises_detectados = set()
        for clave, pais in traducciones_agencias.items():
            if clave in fuentes_crudas:
                paises_detectados.add(pais)
                
        if paises_detectados:
            return "OpenSanctions (Agencias de: " + ", ".join(list(paises_detectados)) + ")"
        return "OpenSanctions (Listas Consolidadas Globales)"
    return fuentes_crudas

def traducir_motivos(programas_crudos):
    if not programas_crudos or programas_crudos == "No especificado":
        return "Motivo no especificado"
            
    diccionario_delitos = {
        "SDGT": "Terrorismo Internacional", "SDNTK": "Narcotráfico (Carteles)",
        "SDNT": "Narcotráfico", "VENEZUELA": "Corrupción o Abuso de DD.HH. (Venezuela)",
        "IRAN-CON-ARMS-EO": "Tráfico de Armas (Irán)", "SYRIA": "Conflicto / Violación de DD.HH. (Siria)",
        "CYBER2": "Ciberdelincuencia", "TCO": "Crimen Organizado Transnacional",
        "NPWMD": "Armas de Destrucción Masiva", "RUSSIA-EO14024": "Sanciones (Rusia)",
        "GLOBAL-MAGNITSKY": "Corrupción y Violación de DD.HH.", "FTO": "Organización Terrorista",
        "SANCIONES INTERNACIONALES": "Sanciones Financieras Internacionales"
    }
    texto_limpio = programas_crudos.replace("[", " ").replace("]", " ")
    motivos = [delito for codigo, delito in diccionario_delitos.items() if codigo in texto_limpio]
    return " | ".join(motivos) if motivos else programas_crudos

def generar_resumen_espanol(texto_crudo):
    if not texto_crudo or texto_crudo == "No hay detalles públicos adicionales.":
        return "No hay información adicional registrada."
        
    texto = texto_crudo
    
    # 1. FILTRO FORZADO (Asegura el español 100% incluso si se cae el internet)
    diccionario_forzado = {
        "DOB": "Fecha de nacimiento:", "POB": "Lugar de nacimiento:", 
        "a.k.a.": "Alias:", "Gender": "Género:", "Male": "Masculino", "Female": "Femenino",
        "Secondary sanctions risk:": "Riesgo de sanciones secundarias:",
        "Transactions Prohibited For Persons Owned or Controlled By U.S. Financial Institutions:": "Transacciones prohibidas para personas controladas por instituciones financieras de EE. UU.:",
        "North Korea Sanctions Regulations": "Regulaciones de Sanciones a Corea del Norte",
        "sections": "secciones", "section": "sección", "Executive Order": "Orden Ejecutiva",
        "Chairman of the Workers' Party of Korea.": "Presidente del Partido de los Trabajadores de Corea.",
        " Jan ": " Ene ", " Feb ": " Feb ", " Mar ": " Mar ", " Apr ": " Abr ",
        " May ": " May ", " Jun ": " Jun ", " Jul ": " Jul ", " Aug ": " Ago ",
        " Sep ": " Sep ", " Oct ": " Oct ", " Nov ": " Nov ", " Dec ": " Dic "
    }
    for ingles, espanol in diccionario_forzado.items():
        texto = texto.replace(ingles, espanol)

    # 2. TRADUCCIÓN CON IA AUTOMÁTICA (Limitada a 4500 caracteres para evitar bloqueos)
    texto = texto[:4500] if len(texto) > 4500 else texto
    try:
        texto_traducido = GoogleTranslator(source='auto', target='es').translate(texto)
        if texto_traducido:
            texto = texto_traducido
    except Exception as e:
        print(f"⚠️ Advertencia IA de traducción: {e}") 

    # 3. Limpieza de fechas estándar (YYYY-MM-DD a DD/MM/YYYY)
    texto = re.sub(r'(\d{4})-(\d{2})-(\d{2})', r'\3/\2/\1', texto)

    # 4. Diccionario de países ISO para OpenSanctions
    paises_iso = {
        "ru": "Rusia", "pt": "Portugal", "il": "Israel", "ve": "Venezuela", "ir": "Irán",
        "kp": "Corea del Norte", "sy": "Siria", "cu": "Cuba", "cn": "China", "af": "Afganistán",
        "us": "EE. UU.", "gb": "Reino Unido", "co": "Colombia", "mx": "México", "es": "España", 
        "sa": "Arabia Saudita", "ae": "Emiratos Árabes Unidos", "tr": "Turquía", "pk": "Pakistán"
    }

    # 5. Formateo limpio de viñetas
    partes_finales = []
    for parte in texto.split(";"):
        p = parte.strip()
        if not p: continue
        
        p = p.replace("Fecha de nacimiento: ", "Fecha de nacimiento: ").replace("Dob ", "Fecha de nacimiento: ")
        p = p.replace("Lugar de nacimiento: ", "Lugar de nacimiento: ").replace("Pob ", "Lugar de nacimiento: ")

        # Traducción de códigos ISO de países
        if p.lower().startswith("nacionalidad:") or p.lower().startswith("ciudadanía:") or p.lower().startswith("ciudadano "):
            partes_split = p.split(":", 1)
            if len(partes_split) == 2:
                valores = partes_split[1]
                codigos = [c.strip() for c in valores.split(",")]
                nombres_paises = [paises_iso.get(c.lower(), c) for c in codigos]
                p = f"{partes_split[0]}: " + ", ".join(nombres_paises)
        
        p = p[0].upper() + p[1:]
        partes_finales.append(f"- {p}")
                
    return "\n".join(partes_finales)

@app.post("/api/consultar")
def consultar_antecedentes(consulta: ConsultaRequest):
    nombre = consulta.nombre.strip().upper()
    apellido = consulta.apellido.strip().upper()
    
    coincidencias = []
    
    # =========================================================
    # 1. BÚSQUEDA HÍBRIDA (Motor de Expresiones Regulares MongoDB)
    # Busca el nombre y el apellido en cualquier parte del registro
    # =========================================================
    query_directa = {
        "$and": [
            {"nombre_completo": {"$regex": nombre, "$options": "i"}},
            {"nombre_completo": {"$regex": apellido, "$options": "i"}}
        ]
    }
    
    # Esto busca directo en la nube sin descargar toda la base de datos
    resultados_exactos = list(coleccion.find(query_directa, {"_id": 0}).limit(3))
    
    if resultados_exactos:
        for d in resultados_exactos:
            textos_obs = str(d.get("observaciones", ""))
            if textos_obs == "No registrado": textos_obs = "No hay detalles públicos adicionales."
            programas_crudos = d.get("programas", "No especificado")
            fuentes_crudas = d.get("fuente", "")
            
            coincidencias.append({
                "nombre_sancionado": d.get("nombre_completo"),
                "similitud_porcentaje": 100, 
                "detalles": {
                    "fuente": traducir_fuentes(fuentes_crudas), 
                    "motivo_delito": traducir_motivos(programas_crudos), 
                    "programas_originales": programas_crudos,
                    "antecedentes_original": textos_obs,
                    "resumen_espanol": generar_resumen_espanol(textos_obs)
                }
            })
    else:
        # =========================================================
        # 2. PLAN B: BÚSQUEDA DIFUSA IA (Si hay errores ortográficos)
        # =========================================================
        nombre_completo_input = f"{nombre} {apellido}"
        registros_db = list(coleccion.find({}, {"_id": 0, "nombre_completo": 1, "programas": 1, "fuente": 1, "observaciones": 1}))
        lista_nombres = [reg["nombre_completo"] for reg in registros_db if "nombre_completo" in reg]
        
        resultados_fuzzy = process.extract(nombre_completo_input, lista_nombres, limit=3, scorer=fuzz.token_set_ratio)
        
        for nombre_encontrado, score in resultados_fuzzy:
            if score >= 85:
                detalles = [item for item in registros_db if item["nombre_completo"] == nombre_encontrado]
                if detalles:
                    d = detalles[0]
                    textos_obs = str(d.get("observaciones", ""))
                    if textos_obs == "No registrado": textos_obs = "No hay detalles públicos adicionales."
                    
                    coincidencias.append({
                        "nombre_sancionado": nombre_encontrado,
                        "similitud_porcentaje": score,
                        "detalles": {
                            "fuente": traducir_fuentes(d.get("fuente", "")), 
                            "motivo_delito": traducir_motivos(d.get("programas", "No especificado")), 
                            "programas_originales": d.get("programas", "No especificado"),
                            "antecedentes_original": textos_obs,
                            "resumen_espanol": generar_resumen_espanol(textos_obs)
                        }
                    })

    if coincidencias:
        return {"estado": "ALERTA", "mensaje": "Se encontraron posibles coincidencias.", "coincidencias": coincidencias}
    return {"estado": "LIMPIO", "mensaje": "No se encontraron antecedentes.", "coincidencias": []}