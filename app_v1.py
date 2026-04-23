import streamlit as st
import math

# Configuración de la página para móvil
st.set_page_config(page_title="Arbitraje VZLA", page_icon="💸")

# Estilos personalizados para que se vea genial en móvil (oscuro como tu imagen)
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
        margin-bottom: 10px;
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

# --- SECCIÓN DE ENTRADAS ---
st.subheader("Datos de Entrada:")
with st.container():
    # CAMBIO 1: El input ahora es el total disponible en la cuenta BDV
    total_disponible_bdv = st.number_input(
        "Dólares Totales Comprados en BDV ($)", 
        min_value=0.0, 
        value=21.00, # Valor por defecto de tu ejemplo
        step=0.10,
        help="El monto neto que el banco te acreditó en tu cuenta de divisas."
    )
    tasa_bdv = st.number_input("Tasa BDV (Bs)", min_value=0.0, value=571.00, step=1.00)
    tasa_p2p = st.number_input("Tasa Compra Binance P2P (Bs)", min_value=0.0, value=625.00, step=1.00)

# --- CONFIGURACIÓN DE COMISIONES (FIJAS SEGÚN ACUERDO) ---
# Se asume que el usuario ya pagó el 0.5% por comprar la divisa, 
# así que aquí solo calculamos las de uso.
com_uso_tarjeta = 0.025    # 2.5% (Uso de tarjeta electrónica BDV)
com_bpay = 0.033           # 3.3% (Tajada de la plataforma Bpay)

st.markdown("---")

if st.button("CALCULAR OPERACIÓN", use_container_width=True):
    # --- LÓGICA MATEMÁTICA (INGENIERÍA INVERSA) ---

    # 1. Calcular el monto máximo a ingresar en Bpay.
    # Fórmula: Monto_Bpay = Total_Disponible / (1 + Com_Tarjeta)
    monto_bruto_bpay = total_disponible_bdv / (1 + com_uso_tarjeta)
    
    # Redondeamos hacia ABAJO a 2 decimales para evitar que la tarjeta rebote por 1 centavo
    monto_bruto_bpay_seguro = math.floor(monto_bruto_bpay * 100) / 100

    # 2. Calcular los USDT netos que recibirás (Tajada de Bpay)
    # Usamos el monto seguro calculado arriba
    usdt_recibidos = monto_bruto_bpay_seguro * (1 - com_bpay)

    # 3. Calcular el costo total en Bolívares que gastaste
    # Reintegramos el 0.5% de comisión por compra de divisa en el BDV
    com_compra_divisa = 0.005
    costo_usd_en_cuenta = tasa_bdv * (1 + com_compra_divisa)
    
    total_bs_debitados = (monto_bruto_bpay_seguro * costo_usd_en_cuenta) * (1 + com_uso_tarjeta)
    
    # Costo real de cada USDT obtenido
    costo_efectivo_usdt = total_bs_debitados / usdt_recibidos

    # 4. Comparativa y Ganancia
    # Calculamos cuánto te costarían esos mismos USDT si los compraras directo en P2P
    costo_p2p_directo = usdt_recibidos * tasa_p2p
    ganancia_bs = costo_p2p_directo - total_bs_debitados
    porcentaje_ganancia = ((tasa_p2p / costo_efectivo_usdt) - 1) * 100

    # --- SECCIÓN DE RESULTADOS ---
    st.subheader("Resultados:")

    # CAMBIO 2: Apartado crucial solicitado
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
        st.metric("Tu Costo USDT", f"{costo_efectivo_usdt:.2f} Bs")

    if costo_efectivo_usdt < tasa_p2p:
        st.success(f"✅ ¡CONVIENE COMPRAR POR BDV/BPAY!")
        st.info(f"📈 Brecha a favor: **{porcentaje_ganancia:.2f}%**")
        st.info(f"💰 Te ahorras/ganas: **{ganancia_bs:.2f} Bs**")
    else:
        st.error(f"❌ NO CONVIENE. Mejor usa el P2P directo.")
        st.error(f"📉 Estás pagando **{abs(porcentaje_ganancia):.2f}%** de más.")

st.markdown("---")
st.caption("Configurado con comisiones: BDV (0.5% + 2.5%) y Bpay (3.3%)")
