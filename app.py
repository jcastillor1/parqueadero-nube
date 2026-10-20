import streamlit as st
import database as db
import pandas as pd

# Iconos por tipo
ICONOS = {
    "Carro": "🚗",
    "Moto": "🏍️",
    "Bicicleta": "🚲",
    "Bicicleta Eléctrica": "🔋🚲",
    "Scooter Eléctrico": "🛴⚡"
}

st.set_page_config(
    page_title="Sistema Multimodal - Parqueadero en la Nube",
    page_icon="🅿️",
    layout="wide"
)

db.init_db()

# --- AUTENTICACIÓN ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.title("🔐 Acceso al Sistema - Parqueadero Multimodal")
    st.markdown("Ingrese sus credenciales de administración.")
    
    with st.form("login_form"):
        usuario = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submit_login = st.form_submit_button("Iniciar Sesión")
        
        if submit_login:
            if usuario == "admin" and password == "1234.":
                st.session_state['autenticado'] = True
                st.success("Acceso concedido.")
                st.rerun()
            else:
                st.error("Credenciales incorrectas (Use admin / 1234.).")
    st.stop()

# --- APLICACIÓN PRINCIPAL ---
st.title("🅿️ Gestión Inteligente Multimodal (95 Espacios)")
st.sidebar.success("Estado: Administrador Conectado")

if st.sidebar.button("Cerrar Sesión"):
    st.session_state['autenticado'] = False
    st.rerun()

st.markdown("---")

menu = st.sidebar.radio("Menú Principal", ["Estado General", "Registrar Entrada", "Registrar Salida y Cobro", "Historial y Métricas"])

espacios = db.obtener_espacios()

if menu == "Estado General":
    st.subheader("📊 Resumen de Ocupación por Categoría")
    
    # Métricas consolidadas
    categorias = ["Carro", "Moto", "Bicicleta", "Bicicleta Eléctrica", "Scooter Eléctrico"]
    
    cols_met = st.columns(5)
    for idx, cat in enumerate(categorias):
        esp_cat = [e for e in espacios if e[1] == cat]
        lib = sum(1 for e in esp_cat if e[2] == 'Disponible')
        cols_met[idx].metric(f"{ICONOS[cat]} {cat}", f"{lib}/{len(esp_cat)} Libres")
        
    st.markdown("---")
    
    # Filtro para ver las tarjetas
    tipo_filtro = st.selectbox("Filtrar vista detallada:", ["Todos"] + categorias)
    espacios_filtrados = espacios if tipo_filtro == "Todos" else [e for e in espacios if e[1] == tipo_filtro]
    
    st.caption(f"Mostrando {len(espacios_filtrados)} espacios.")
    
    # Mostrar tarjetas en rejilla de 4 columnas
    cols = st.columns(4)
    for index, (num, tipo_espacio, estado, placa, tipo_veh, hora) in enumerate(espacios_filtrados):
        icono = ICONOS.get(tipo_espacio, "🅿️")
        with cols[index % 4]:
            if estado == "Disponible":
                st.success(f"### {num} {icono}\n**{tipo_espacio}**\n\n🟢 **LIBRE**")
            else:
                st.error(f"### {num} {icono}\n**{tipo_espacio}**\n\n🔴 **OCUPADO**\n* ID: `{placa}`\n* Entrada: {hora.split()[1]}")

elif menu == "Registrar Entrada":
    st.subheader("📥 Registro de Ingreso")
    
    tipo_vehiculo = st.selectbox("Seleccione Tipo de Vehículo", ["Carro", "Moto", "Bicicleta", "Bicicleta Eléctrica", "Scooter Eléctrico"])
    
    espacios_libres = [e[0] for e in espacios if e[1] == tipo_vehiculo and e[2] == 'Disponible']
    
    if not espacios_libres:
        st.warning(f"⚠️ No hay espacios disponibles para **{tipo_vehiculo}**.")
    else:
        with st.form("form_entrada"):
            espacio_sel = st.selectbox("Espacio Disponible Asignado", espacios_libres)
            label_id = "Placa" if tipo_vehiculo in ["Carro", "Moto"] else "Número de Marco / Serie / ID"
            placa = st.text_input(f"{label_id}")
            
            submit = st.form_submit_button("Registrar Entrada")
            if submit:
                if not placa.strip():
                    st.error("Por favor ingrese una placa o identificador.")
                else:
                    if db.registrar_entrada(espacio_sel, placa, tipo_vehiculo):
                        st.success(f"¡{tipo_vehiculo} ({placa.upper()}) ingresado en **{espacio_sel}**!")
                        st.rerun()

elif menu == "Registrar Salida y Cobro":
    st.subheader("📤 Salida y Cobro Automático")
    
    espacios_ocupados = [e for e in espacios if e[2] == 'Ocupado']
    
    if not espacios_ocupados:
        st.info("No hay vehículos estacionados.")
    else:
        opciones = {f"{e[0]} - {e[4]} ({e[3]})": e for e in espacios_ocupados}
        seleccion = st.selectbox("Seleccione el vehículo a retirar:", list(opciones.keys()))
        
        datos = opciones[seleccion]
        num_espacio = datos[0]
        tipo_vehiculo = datos[4]
        
        tarifa_sugerida = db.TARIFAS_POR_DEFECTO.get(tipo_vehiculo, 50)
        
        with st.form("form_salida"):
            st.write(f"**Espacio:** `{num_espacio}` | **Tipo:** {tipo_vehiculo} {ICONOS.get(tipo_vehiculo, '')}")
            tarifa = st.number_input("Tarifa por minuto ($ COP)", value=tarifa_sugerida)
            
            submit_salida = st.form_submit_button("Calcular y Liberar Espacio")
            if submit_salida:
                placa, t_veh, minutos, total = db.registrar_salida(num_espacio, tarifa)
                if placa:
                    st.balloons()
                    st.success(f"¡Salida completada para **{placa}**!")
                    st.info(f"⏱️ **Tiempo:** {minutos} min | 💵 **Total:** ${total:,.0f} COP")
                else:
                    st.error("Error al procesar la salida.")

elif menu == "Historial y Métricas":
    st.subheader("📈 Historial y Recaudo")
    
    historial = db.obtener_historial()
    if not historial:
        st.info("No hay registros en el historial.")
    else:
        df = pd.DataFrame(historial, columns=["Espacio", "Tipo", "Placa/ID", "Entrada", "Salida", "Total ($)"])
        
        c1, c2 = st.columns(2)
        c1.metric("Servicios Realizados", len(df))
        c2.metric("Recaudo Total", f"${df['Total ($)'].sum():,.0f} COP")
        
        st.markdown("---")
        st.dataframe(df, use_container_width=True)
