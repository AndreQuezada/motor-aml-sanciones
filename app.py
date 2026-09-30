import streamlit as st
import requests

# 1. Configuración de página (SIEMPRE debe ser el primer comando de Streamlit)
st.set_page_config(page_title="Plataforma AML", page_icon="🛡️", layout="wide")

# --- BARRA LATERAL: VERIFICACIÓN OFICIAL DIRECTA ---
with st.sidebar:
    st.title("Enlaces Oficiales")
    st.markdown("Portales gubernamentales e internacionales para validación manual de debida diligencia.")
    
    st.divider()

    # Sección Internacionales
    st.subheader("Internacionales")
    st.markdown("""
    * 🔗 [OFAC (Sanciones EE.UU.)](https://sanctionssearch.ofac.treas.gov/)
    * 🔗 [ONU (Lista Consolidada)](https://www.un.org/securitycouncil/es/content/un-sc-consolidated-list)
    * 🔗 [Interpol (Notificaciones Rojas)](https://www.interpol.int/es/Como-trabajamos/Notificaciones/Notificaciones-rojas/Ver-las-notificaciones-rojas)
    * 🔗 [Unión Europea (Sanciones)](https://eur-lex.europa.eu/legal-content/ES/TXT/?uri=OJ:L:2022:025:TOC)
    * 🔗 [State Dept (FTO Terrorismo)](https://www.state.gov/foreign-terrorist-organizations/)
    """)

    st.divider()
    
    # Sección Colombia
    st.subheader("🇨🇴 Colombia")
    st.markdown("""
    * 🔗 [Policía Nacional (Penales)](https://antecedentes.policia.gov.co:7005/WebJudicial/)
    * 🔗 [Contraloría (Resp. Fiscal)](https://www.contraloria.gov.co/control-fiscal/responsabilidad-fiscal/certificado-de-antecedentes-fiscales)
    * 🔗 [Procuraduría (Disciplinarios)](https://www.procuraduria.gov.co/Pages/Consulta-de-Antecedentes.aspx)
    * 🔗 [SIMIT (Multas de Tránsito)](https://www.fcm.org.co/simit/#/home-public)
    """)
    
    st.divider()
    
    # Sección Ecuador
    st.subheader("🇪🇨 Ecuador")
    st.markdown("""
    * 🔗 [Min. del Interior (Penales)](https://certificados.ministeriodelinterior.gob.ec/gestorcertificados/antecedentes/)
    * 🔗 [Función Judicial (Causas / SATJE)](http://consultas.funcionjudicial.gob.ec/informacionjudicial/public/informacion.jsf)
    * 🔗 [ANT (Multas de Tránsito)](https://consultaweb.ant.gob.ec/PortalWEB/paginas/clientes/clp_criterio_consulta.jsp)
    """)

# 2. Ajuste CSS Corporativo (Botones más formales y sobrios)
st.markdown("""
<style>
    div.stButton > button:first-child {
        background-color: #0F172A; /* Azul noche casi negro */
        color: white;
        border-radius: 4px; /* Bordes menos redondeados, más serios */
        padding: 10px 24px;
        font-weight: 600;
        border: none;
    }
    div.stButton > button:first-child:hover {
        background-color: #1D4ED8; /* Azul rey al pasar el mouse */
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# 3. Encabezado Corporativo 
st.title("Plataforma de Debida Diligencia y AML")
st.markdown("""
Sistema automatizado de cruce de datos contra listas restrictivas y vinculantes a nivel global: 
**Oficina de Control de Activos Extranjeros (OFAC SDN & Non-SDN), Consejo de Seguridad de las Naciones Unidas (ONU), Organización Internacional de Policía Criminal (Interpol - Notificaciones Rojas), Sanciones Financieras de la Unión Europea (UE), Departamento de Estado de EE.UU. (Organizaciones Terroristas Extranjeras - FTO) y más de 15 agencias gubernamentales internacionales consolidadas.**
""")
st.divider()

# 4. Formulario centrado y estructurado en columnas
col_izq, col_centro, col_der = st.columns([1, 2, 1])

with col_centro:
    with st.form("formulario_busqueda", clear_on_submit=False):
        st.subheader("🔍 Datos de Búsqueda")
        
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
    if not nombre and not apellido:
        st.warning("⚠️ Por favor, ingresa el nombre o el apellido para realizar la búsqueda.")
    else:
        with st.spinner("Buscando en bases de datos internacionales..."):
            try:
                # AQUÍ ESTÁ EL ESCUDO: timeout=20 segundos
                res = requests.post(
                    "https://api-antecedentes-wotq.onrender.com/api/consultar", 
                    json={"cedula": cedula, "nombre": nombre, "apellido": apellido}, 
                    timeout=20
                )
                
                if res.status_code == 200:
                    datos = res.json()
                    st.divider() 
                    
                    if datos["estado"] == "LIMPIO":
                        st.success(f"✅ ESTADO: APROBADO - No se encontraron registros en las listas restrictivas vinculantes para: {nombre} {apellido}.")
                    else:
                        st.error("🚨 ESTADO: ALERTA - Se encontraron posibles coincidencias en las bases de datos.")
                        st.markdown("<br>", unsafe_allow_html=True)
                        
                        # 1. AGRUPAR LOS REGISTROS POR NOMBRE
                        registros_agrupados = {}
                        for c in datos["coincidencias"]:
                            nombre_sancionado = c["nombre_sancionado"]
                            if nombre_sancionado not in registros_agrupados:
                                registros_agrupados[nombre_sancionado] = {
                                    "similitud": c["similitud_porcentaje"],
                                    "registros": []
                                }
                            registros_agrupados[nombre_sancionado]["registros"].append(c["detalles"])
                        
                        # 2. DESPLEGAR INTERFAZ CON PESTAÑAS (TABS)
                        for nombre_match, info in registros_agrupados.items():
                            with st.container():
                                st.markdown(f"### ⚠️ Objetivo: {nombre_match}")
                                
                                # Barra de progreso visual
                                st.caption(f"Nivel de Similitud: {info['similitud']}%")
                                st.progress(int(info['similitud']))
                                
                                # Nombres de las fuentes para crear las pestañas
                                nombres_fuentes = [detalle["fuente"] for detalle in info["registros"]]
                                
                                # Crear pestañas
                                pestañas = st.tabs(nombres_fuentes)
                                
                                # Llenar cada pestaña
                                for i, pestaña in enumerate(pestañas):
                                    with pestaña:
                                        detalle = info["registros"][i]
                                        
                                        col_info1, col_info2 = st.columns(2)
                                        with col_info1:
                                            st.error(f"**⚖️ Motivos / Delitos:**\n\n{detalle.get('motivo_delito', 'No especificado')}")
                                        with col_info2:
                                            st.info(f"**🌐 Fuente Original:**\n\n{detalle.get('fuente', 'Desconocida')}")
                                        
                                        st.success(f"**📝 Resumen de Perfil:**\n\n{detalle.get('resumen_espanol', 'No hay resumen disponible.')}")
                                        
                                        with st.expander("Ver registro técnico original (Inglés)"):
                                            st.write(f"**Programa Legal:** {detalle.get('programas_originales', '')}")
                                            st.write(detalle.get('antecedentes_original', ''))
                                        
                            st.divider() # Línea entre diferentes criminales
                else:
                    st.error(f"🚨 Error del Cerebro (Código {res.status_code}): {res.text}")
            
            except requests.exceptions.Timeout:
                st.warning("⏳ El servidor central se está despertando tras un periodo de inactividad. Por favor, espera 5 segundos y vuelve a darle clic a Buscar.")
            except Exception as e:
                st.error(f"❌ Error de conexión general: Verifica tu internet o los servidores.")