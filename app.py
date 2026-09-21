import streamlit as st
# --- BARRA LATERAL: VERIFICACIÓN OFICIAL ---
# --- BARRA LATERAL: VERIFICACIÓN OFICIAL DIRECTA ---
with st.sidebar:
    st.title("🏛️ Verificación Nacional")
    st.markdown("Enlaces directos a los formularios oficiales de consulta.")
    
    st.divider()
    
    # Sección Colombia
    st.subheader("🇨🇴 Colombia")
    st.markdown("""
    * 🔗 [Policía Nacional (Penales)](https://antecedentes.policia.gov.co:7005/WebJudicial/)
    * 🔗 [Contraloría (Resp. Fiscal)](https://www.contraloria.gov.co/control-fiscal/responsabilidad-fiscal/certificado-de-antecedentes-fiscales)
    * 🔗 [Procuraduría (Disciplinarios)](https://www.procuraduria.gov.co/Pages/Consulta-de-Antecedentes.aspx)
    * 🔗 [Contaduría General (BDME)](https://eris.contaduria.gov.co/BDME/#PanelPrincipal)
    """)
    
    st.divider()
    
    # Sección Ecuador
    st.subheader("🇪🇨 Ecuador")
    st.markdown("""
    * 🔗 [Min. del Interior (Penales)](https://certificadoantecedentes.ministeriodelinterior.gob.ec/)
    * 🔗 [Función Judicial (Causas / SATJE)](http://consultas.funcionjudicial.gob.ec/informacionjudicial/public/informacion.jsf)
    * 🔗 [Contraloría General (Responsabilidades)](https://www.contraloria.gob.ec/Servicios/CertificadoResponsabilidades)
    * 🔗 [Min. del Trabajo (Impedimentos SUT)](https://sut.trabajo.gob.ec/impedimentos/generar_certificado.xhtml)
    """)
import requests

# 1. Configuración de página limpia y amplia
st.set_page_config(page_title="Plataforma AML", page_icon="🛡️", layout="wide")

# 2. Pequeño ajuste CSS para suavizar el botón
st.markdown("""
<style>
    div.stButton > button:first-child {
        background-color: #2563eb;
        color: white;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: bold;
    }
    div.stButton > button:first-child:hover {
        background-color: #1d4ed8;
    }
</style>
""", unsafe_allow_html=True)

# 3. Encabezado moderno
st.title("🛡️ Plataforma de Cumplimiento (AML & Sanciones)")
st.markdown("Consulta inteligente en listas restrictivas globales: **OFAC, ONU, Interpol y OpenSanctions**.")
st.divider()

# 4. Formulario centrado y estructurado en columnas
col_izq, col_centro, col_der = st.columns([1, 2, 1])

with col_centro:
    with st.form("formulario_busqueda", clear_on_submit=False):
        st.subheader("🔍 Datos de Búsqueda")
        
        # Ponemos nombre y apellido uno al lado del otro
        col_nom, col_ape = st.columns(2)
        with col_nom:
            nombre = st.text_input("Nombre(s) *", placeholder="Ej: Nicolas")
        with col_ape:
            apellido = st.text_input("Apellido(s) *", placeholder="Ej: Maduro")
            
        cedula = st.text_input("Identificación (Opcional)", placeholder="Cédula o Pasaporte")
        
        st.markdown("<br>", unsafe_allow_html=True)
        boton = st.form_submit_button("Consultar Antecedentes", use_container_width=True)

# 5. Procesamiento y Resultados Visuales
if boton:
    if not nombre or not apellido:
        st.warning("⚠️ Por favor, ingresa el nombre y el apellido para realizar la búsqueda.")
    else:
        with st.spinner("Buscando en bases de datos internacionales..."):
            try:
                res = requests.post("https://api-antecedentes-wotq.onrender.com/api/consultar", json={"cedula": cedula, "nombre": nombre, "apellido": apellido}, timeout=90)
                if res.status_code == 200:
                    datos = res.json()
                    
                    st.divider() # Línea separadora antes de los resultados
                    
                    if datos["estado"] == "LIMPIO":
                        # Mensaje de éxito gigante si no hay coincidencias
                        st.success(f"✅ **{datos['mensaje']}** - No se encontraron registros en las listas restrictivas para: {nombre} {apellido}.")
                        st.balloons()
                    else:
                        st.error(f"🚨 **ALERTA:** {datos['mensaje']}")
                        st.markdown(f"### Resultados encontrados para: *{nombre} {apellido}*")
                        st.markdown("<br>", unsafe_allow_html=True)
                        
                        # Mostramos cada coincidencia como una "tarjeta" limpia
                        for idx, coincidencia in enumerate(datos["coincidencias"]):
                            with st.container():
                                st.subheader(f"Objetivo #{idx + 1}: {coincidencia['nombre_sancionado']}")
                                
                                # ¡NUEVO! Barra de progreso visual para la similitud
                                st.caption(f"Nivel de Similitud: {coincidencia['similitud_porcentaje']}%")
                                st.progress(int(coincidencia['similitud_porcentaje']))
                                
                                # Dividimos la información legal en dos cajas de colores suaves
                                col_info1, col_info2 = st.columns(2)
                                with col_info1:
                                    st.error(f"**⚖️ Motivo de Inclusión:**\n\n{coincidencia['detalles'].get('motivo_delito', '')}")
                                with col_info2:
                                    st.info(f"**🌐 Fuentes Internacionales:**\n\n{coincidencia['detalles'].get('fuente', '')}")
                                
                                # El resumen en un cuadro verde de éxito (fácil de leer)
                                st.success(f"**📝 Resumen de Perfil:**\n\n{coincidencia['detalles'].get('resumen_espanol', '')}")
                                
                                # El dato feo/crudo escondido por defecto
                                with st.expander("Ver registro técnico original (Inglés)"):
                                    st.write(f"**Programa Legal:** {coincidencia['detalles'].get('programas_originales', '')}")
                                    st.write(coincidencia['detalles'].get('antecedentes_original', ''))
                                
                                st.divider() # Línea entre diferentes resultados
                                
            except Exception:
                st.error("❌ Error conectando con el motor de búsqueda (Verifica que FastAPI esté encendido).")