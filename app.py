import streamlit as st

# Configuración de la página para móvil
st.set_page_config(page_title="Arbitraje VZLA", page_icon="💸")

st.title("💸 Calculadora BDV-Binance")
st.markdown("---")

# Entradas tipo formulario
with st.container():
    monto_usd = st.number_input("Dólares a comprar ($)", min_value=0.0, value=20.0, step=1.0)
    tasa_bdv = st.number_input("Tasa BDV (Bs)", min_value=0.0, value=571.0)
    tasa_p2p = st.number_input("Tasa Compra Binance P2P (Bs)", min_value=0.0, value=625.0)

# Comisiones (Tus parámetros fijos)
com_compra_divisa = 0.005
com_uso_tarjeta = 0.025
com_bpay = 0.033

if st.button("CALCULAR GANANCIA", use_container_width=True):
    # Lógica Matemática
    costo_usd_en_cuenta = tasa_bdv * (1 + com_compra_divisa)
    total_bs_pagados = (monto_usd * costo_usd_en_cuenta) * (1 + com_uso_tarjeta)
    usdt_recibidos = monto_usd * (1 - com_bpay)
    costo_efectivo_tarjeta = total_bs_pagados / usdt_recibidos
    
    # Comparativa
    diferencia_bs = tasa_p2p - costo_efectivo_tarjeta
    ganancia_total_bs = diferencia_bs * usdt_recibidos
    porcentaje = ((tasa_p2p / costo_efectivo_tarjeta) - 1) * 100

    # Resultados visuales
    st.subheader("Resultados:")
    col1, col2 = st.columns(2)
    col1.metric("Recibes", f"{usdt_recibidos:.2f} USDT")
    col2.metric("Tu Costo", f"{costo_efectivo_tarjeta:.2f} Bs")

    if costo_efectivo_tarjeta < tasa_p2p:
        st.success(f"✅ ¡CONVIENE! Ganas {porcentaje:.2f}%")
        st.info(f"💰 Ahorro/Ganancia: **{ganancia_total_bs:.2f} Bs**")
    else:
        st.error(f"❌ NO CONVIENE. P2P es más barato.")

st.markdown("---")
st.caption("Configurado con comisiones: BDV (0.5% + 2.5%) y Bpay (3.3%)")
