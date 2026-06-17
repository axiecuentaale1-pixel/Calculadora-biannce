import streamlit as st
import math
import pandas as pd
from datetime import datetime
try:
    from streamlit_gsheets import GSheetsConnection
    HAS_GSHEETS = True
except ImportError:
    HAS_GSHEETS = False

# Configuración de la página para móvil
st.set_page_config(page_title="Arbitraje VZLA", page_icon="💸")

# Estilos personalizados (Oscuro y limpio)
st.markdown("""
<style>
    .stNumberInput > div > div > input {
        background-color: #1E1E1E;
        color: white;
    }
    div[data-baseweb="select"] > div {
        background-color: #1E1E1E;
        color: white;
    }
    .metric-card {
        background-color: #262730;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
        border: 1px solid #444;
    }
    .stButton>button {
        background-color: #1E1E1E;
        color: white;
        border: 1px solid #444;
    }
    .stButton>button:hover {
        background-color: #333;
        border-color: #666;
    }
    /* Hacer más grandes las pestañas (Tabs) */
    button[data-baseweb="tab"] > div[data-testid="stMarkdownContainer"] > p {
        font-size: 20px !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("💸 Calculadora BDV-Binance")
st.markdown("---")

# Comisiones configuradas
com_uso_tarjeta = 0.025    
com_bpay = 0.036
com_compra_divisa = 0.005

# --- SETUP CLOUD CONNECTION ---
# st.connection will only work if st.secrets are configured in Streamlit Cloud.
# We wrap it in a try-except so the app doesn't crash locally while configuring.
try:
    if HAS_GSHEETS:
        conn = st.connection("gsheets", type=GSheetsConnection)
    else:
        conn = None
except Exception:
    conn = None

def guardar_operacion(tipo, inversion, recibido, ganancia, porcentaje):
    if conn is None:
        st.warning("⚠️ Conexión a Google Sheets no configurada. (Revisa tus st.secrets)")
        return
    try:
        # Read existing data
        df = conn.read()
        
        # Check if df is empty or needs initialization
        if df is None or df.empty or len(df.columns) == 0:
            df = pd.DataFrame(columns=["Fecha", "Tipo", "Inversion_Bs", "Recibido_USDT", "Ganancia_Bs", "Porcentaje"])
            
        nueva_fila = pd.DataFrame([{
            "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Tipo": tipo,
            "Inversion_Bs": inversion,
            "Recibido_USDT": recibido,
            "Ganancia_Bs": ganancia,
            "Porcentaje": porcentaje
        }])
        
        # Append and update
        df_actualizado = pd.concat([df, nueva_fila], ignore_index=True)
        conn.update(data=df_actualizado)
        st.success("✅ Operación guardada en la Nube correctamente.")
    except Exception as e:
        st.error(f"Error al guardar en Google Sheets: {e}")

tab1, tab2, tab3 = st.tabs(["📊 Tradicional", "🎯 Modo Meta (Inverso)", "📂 Historial"])

with tab1:
    st.subheader("Cálculo Tradicional")
    with st.container():
        total_disponible_bdv = st.number_input(
            "Dólares Totales Comprados en BDV ($)", 
            min_value=0.0, 
            value=21.00,
            step=0.10,
            help="El monto neto que el banco te acreditó en tu cuenta de divisas.",
            key="trad_usd"
        )
        tasa_bdv = st.number_input("Tasa BDV (Bs)", min_value=0.0, value=571.00, step=1.00, key="trad_tasa_bdv")
        tasa_p2p = st.number_input("Tasa Compra Binance P2P (Bs)", min_value=0.0, value=625.00, step=1.00, key="trad_tasa_p2p")

    if st.button("CALCULAR DIFERENCIA", use_container_width=True, key="btn_trad"):
        monto_bruto_bpay = total_disponible_bdv / (1 + com_uso_tarjeta)
        monto_bruto_bpay_seguro = math.floor(monto_bruto_bpay * 100) / 100
        usdt_recibidos = monto_bruto_bpay_seguro * (1 - com_bpay)
        costo_usd_en_cuenta = tasa_bdv * (1 + com_compra_divisa)
        total_bs_debitados = (monto_bruto_bpay_seguro * costo_usd_en_cuenta) * (1 + com_uso_tarjeta)
        
        costo_efectivo_usdt = total_bs_debitados / usdt_recibidos if usdt_recibidos > 0 else 0
        costo_p2p_directo = usdt_recibidos * tasa_p2p
        ganancia_bs = costo_p2p_directo - total_bs_debitados
        porcentaje_ganancia = ((tasa_p2p / costo_efectivo_usdt) - 1) * 100 if costo_efectivo_usdt > 0 else 0

        st.subheader("Resultados:")
        st.markdown(f"""
        <div class="metric-card">
            <p style="color:#aaa; font-size:0.9em; margin:0;">Monto a ingresar en Bpay ($)</p>
            <p style="color:#FFD700; font-size:2em; font-weight:bold; margin:0;">$ {monto_bruto_bpay_seguro:.2f}</p>
            <p style="color:#aaa; font-size:0.8em; margin:0;">Esto dejará un pequeño saldo de seguridad en tu cuenta BDV.</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Recibes", f"{usdt_recibidos:.2f} USDT")
        with col2:
            st.metric("Tu Costo", f"{costo_efectivo_usdt:.2f} Bs")

        if costo_efectivo_usdt < tasa_p2p and usdt_recibidos > 0:
            st.success(f"✅ ¡CONVIENE COMPRAR POR BPAY! Ganas {porcentaje_ganancia:.2f}%")
            ganancia_usdt = ganancia_bs / tasa_p2p
            st.info(f"💰 Te ahorras/ganas: **{ganancia_bs:.2f} Bs** (~{ganancia_usdt:.2f} USDT)")
        else:
            st.error(f"❌ NO CONVIENE BPAY. Mejor usa el P2P directo.")
            st.error(f"📉 Estás pagando **{abs(porcentaje_ganancia):.2f}%** de más.")
            
        st.markdown("---")
        if st.button("💾 Guardar Operación en la Nube", key="save_trad"):
            guardar_operacion("Tradicional", total_bs_debitados, usdt_recibidos, ganancia_bs, porcentaje_ganancia)

with tab2:
    st.subheader("Cálculo Inverso (Meta)")
    st.markdown("¿Cuántos Bolívares necesitas para llegar a una meta exacta de USDT?")
    with st.container():
        meta_usdt = st.number_input("Meta deseada en Binance (USDT)", min_value=0.0, value=50.00, step=1.00, key="inv_usdt")
        tasa_bdv_inv = st.number_input("Tasa BDV (Bs)", min_value=0.0, value=571.00, step=1.00, key="inv_tasa_bdv")
        tasa_p2p_inv = st.number_input("Tasa Compra Binance P2P (Bs)", min_value=0.0, value=625.00, step=1.00, key="inv_tasa_p2p")
        
    if st.button("CALCULAR INVERSO", use_container_width=True, key="btn_inv"):
        # Para llegar a meta_usdt despues de la comision de bpay (3.6%)
        bpay_deposit_requerido = meta_usdt / (1 - com_bpay)
        
        # Redondeo seguro hacia arriba para garantizar que llegue la meta
        bpay_deposit_seguro = math.ceil(bpay_deposit_requerido * 100) / 100
        
        # Cuantos dolares BDV necesito tener considerando 2.5% por uso de tarjeta
        usd_bdv_necesarios = bpay_deposit_seguro * (1 + com_uso_tarjeta)
        
        costo_usd_en_cuenta = tasa_bdv_inv * (1 + com_compra_divisa)
        bs_totales_requeridos = usd_bdv_necesarios * costo_usd_en_cuenta
        
        costo_efectivo_usdt = bs_totales_requeridos / meta_usdt if meta_usdt > 0 else 0
        costo_p2p_directo = meta_usdt * tasa_p2p_inv
        ganancia_bs = costo_p2p_directo - bs_totales_requeridos
        porcentaje_ganancia = ((tasa_p2p_inv / costo_efectivo_usdt) - 1) * 100 if costo_efectivo_usdt > 0 else 0
        
        st.subheader("Resultados:")
        st.markdown(f"""
        <div class="metric-card">
            <p style="color:#aaa; font-size:0.9em; margin:0;">Total de Bolívares Requeridos</p>
            <p style="color:#FFD700; font-size:2em; font-weight:bold; margin:0;">Bs {bs_totales_requeridos:,.2f}</p>
            <p style="color:#aaa; font-size:0.8em; margin:0;">Equivalente a comprar ${usd_bdv_necesarios:.2f} en BDV.</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Ingresar en Bpay", f"${bpay_deposit_seguro:.2f}")
        with col2:
            st.metric("Tu Costo Real", f"{costo_efectivo_usdt:.2f} Bs/USDT")
            
        if costo_efectivo_usdt < tasa_p2p_inv and meta_usdt > 0:
            st.success(f"✅ ¡CONVIENE COMPRAR POR BPAY! Ganas {porcentaje_ganancia:.2f}%")
            ganancia_usdt = ganancia_bs / tasa_p2p_inv
            st.info(f"💰 Te ahorras: **{ganancia_bs:,.2f} Bs** (~{ganancia_usdt:.2f} USDT) respecto al P2P.")
        else:
            st.error(f"❌ NO CONVIENE BPAY. Mejor compra los {meta_usdt} USDT directo en P2P.")
            
        st.markdown("---")
        if st.button("💾 Guardar Operación en la Nube", key="save_inv"):
            guardar_operacion("Inverso", bs_totales_requeridos, meta_usdt, ganancia_bs, porcentaje_ganancia)

with tab3:
    st.subheader("📂 Historial de Operaciones en Google Sheets")
    if conn is None:
        st.warning("Para ver el historial, debes configurar los Secrets de Google Sheets en Streamlit Cloud.")
    else:
        try:
            df = conn.read()
            if df is None or df.empty:
                st.info("No hay operaciones guardadas aún.")
            else:
                ganancia_total = pd.to_numeric(df["Ganancia_Bs"], errors='coerce').sum()
                ops_totales = len(df)
                
                col1, col2 = st.columns(2)
                col1.metric("Operaciones Totales", ops_totales)
                col2.metric("Ganancia Histórica Total", f"{ganancia_total:,.2f} Bs")
                
                st.dataframe(df, use_container_width=True)
                
                if st.button("🔄 Actualizar Datos"):
                    st.rerun()
        except Exception as e:
            st.error("No se pudo leer la base de datos de la nube. Asegúrate de que la hoja exista y tenga permisos.")
            st.write(e)

st.markdown("---")
# Footer limpio
st.caption("Configurado con comisiones: BDV (0.5% + 2.5%) y Bpay (3.6%)")
