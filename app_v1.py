import streamlit as st
import math

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
</style>
""", unsafe_allow_html=True)

st.title("💸 Calculadora BDV-Binance")
st.markdown("---")

# --- ENTRADAS (Sin subheader "Datos de Entrada") ---
with st.container():
    total_disponible_bdv = st.number_input(
        "Dólares Totales Comprados en BDV ($)", 
        min_value=0.0, 
        value=21.00,
        step=0.10,
        help="El monto neto que el banco te acreditó en tu cuenta de divisas."
    )
    tasa_bdv = st.number_input("Tasa BDV (Bs)", min_value=0.0, value=571.00, step=1.00)
    tasa_p2p = st.number_input("Tasa Compra Binance P2P (Bs)", min_value=0.0, value=625.00, step=1.00)

# Comisiones configuradas
com_uso_tarjeta = 0.025    
com_bpay = 0.033           

# Botón con el texto original "CALCULAR DIFERENCIA"
if st.button("CALCULAR DIFERENCIA", use_container_width=True):
    # --- LÓGICA MATEMÁTICA ---
    monto_bruto_bpay = total_disponible_bdv / (1 + com_uso_tarjeta)
    monto_bruto_bpay_seguro = math.floor(monto_bruto_bpay * 100) / 100

    usdt_recibidos = monto_bruto_bpay_seguro * (1 - com_bpay)

    com_compra_divisa = 0.005
    costo_usd_en_cuenta = tasa_bdv * (1 + com_compra_divisa)
    total_bs_debitados = (monto_bruto_bpay_seguro * costo_usd_en_cuenta) * (1 + com_uso_tarjeta)
    
    costo_efectivo_usdt = total_bs_debitados / usdt_recibidos

    costo_p2p_directo = usdt_recibidos * tasa_p2p
    ganancia_bs = costo_p2p_directo - total_bs_debitados
    porcentaje_ganancia = ((tasa_p2p / costo_efectivo_usdt) - 1) * 100

    # --- RESULTADOS ---
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

    if costo_efectivo_usdt < tasa_p2p:
        st.success(f"✅ ¡CONVIENE COMPRAR POR BPAY! Ganas {porcentaje_ganancia:.2f}%")
        ganancia_usdt = ganancia_bs / tasa_p2p
        st.info(f"💰 Te ahorras/ganas: **{ganancia_bs:.2f} Bs** (~{ganancia_usdt:.2f} USDT)")
    else:
        st.error(f"❌ NO CONVIENE BPAY. Mejor usa el P2P directo.")
        st.error(f"📉 Estás pagando **{abs(porcentaje_ganancia):.2f}%** de más.")

# Footer limpio sin líneas extras
st.caption("Configurado con comisiones: BDV (0.5% + 2.5%) y Bpay (3.3%)")
