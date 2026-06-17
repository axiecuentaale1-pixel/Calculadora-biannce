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
st.set_page_config(page_title="Arbitraje VZLA", page_icon=":material/calculate:")

# Estilos personalizados (Premium oscuro)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20,400,0,0');
    
    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
    }
    /* Proteger la fuente de los iconos para que no sea sobrescrita por Inter */
    .material-symbols-rounded {
        font-family: 'Material Symbols Rounded' !important;
    }
    .stNumberInput > div > div > input {
        background-color: #1a1a2e;
        color: #e0e0e0;
        border: 1px solid #333;
        border-radius: 8px;
    }
    /* Ocultar botones de +/- en los inputs numéricos */
    [data-testid="stNumberInputStepUp"],
    [data-testid="stNumberInputStepDown"] {
        display: none !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #1a1a2e;
        color: white;
    }
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 15px;
        border: 1px solid #2a2a4a;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .flow-step {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 15px 20px;
        border-radius: 12px;
        border-left: 4px solid #FFD700;
        margin-bottom: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }
    .flow-step .step-label {
        color: #888; font-size: 0.75em; text-transform: uppercase; letter-spacing: 1px; margin: 0;
        display: flex; align-items: center; gap: 6px;
    }
    .flow-step .step-label .material-symbols-rounded {
        font-size: 1.4em;
        text-transform: none;
    }
    .flow-step .step-value {
        color: #FFD700; font-size: 1.4em; font-weight: 700; margin: 4px 0 0 0;
    }
    .flow-connector {
        text-align: center;
        color: #888;
        font-size: 0.85em;
        font-style: italic;
        letter-spacing: 0.5px;
        padding: 8px 0;
        position: relative;
    }
    .flow-connector::before, .flow-connector::after {
        content: '';
        display: inline-block;
        width: 40px;
        height: 1px;
        background: #444;
        vertical-align: middle;
        margin: 0 10px;
    }
    .result-card-green {
        background: linear-gradient(135deg, #0a2e1a 0%, #0d3320 100%);
        padding: 20px;
        border-radius: 12px;
        margin: 15px 0;
        border: 1px solid #1a5c3a;
        box-shadow: 0 4px 20px rgba(0,255,100,0.08);
    }
    .result-card-red {
        background: linear-gradient(135deg, #2e0a0a 0%, #331515 100%);
        padding: 20px;
        border-radius: 12px;
        margin: 15px 0;
        border: 1px solid #5c1a1a;
        box-shadow: 0 4px 20px rgba(255,50,50,0.08);
    }
    .stButton>button {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: #FFD700;
        border: 1px solid #333;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #16213e 0%, #0f3460 100%);
        border-color: #FFD700;
        box-shadow: 0 0 15px rgba(255,215,0,0.15);
    }
    /* Pestañas grandes */
    button[data-baseweb="tab"] > div[data-testid="stMarkdownContainer"] > p {
        font-size: 18px !important;
        font-weight: 600 !important;
    }
    .tasas-header {
        background: linear-gradient(135deg, #0f3460 0%, #16213e 100%);
        padding: 15px 20px;
        border-radius: 12px;
        border: 1px solid #2a2a4a;
        margin-bottom: 15px;
    }
    .tasas-header p {
        color: #aaa; font-size: 0.85em; margin: 0 0 5px 0;
    }
    .tasas-header .title {
        color: #FFD700; font-size: 0.9em; font-weight: 600; margin: 0;
        display: flex; align-items: center; gap: 6px;
    }
    .tasas-header .title .material-symbols-rounded {
        font-size: 1.3em;
    }
</style>
""", unsafe_allow_html=True)

st.title(":material/currency_exchange: Calculadora BDV-Binance")
st.markdown("---")

# Comisiones configuradas
com_uso_tarjeta = 0.025    
com_bpay = 0.036
com_compra_divisa = 0.005

# --- TASAS GLOBALES (compartidas entre todas las pestañas) ---
st.markdown("""
<div class="tasas-header">
    <p class="title"><span class="material-symbols-rounded">satellite_alt</span> Tasas del Mercado</p>
    <p>Estas tasas se comparten en todas las pestañas. Configúralas una vez.</p>
</div>
""", unsafe_allow_html=True)

col_g1, col_g2 = st.columns(2)
with col_g1:
    tasa_bdv_global = st.number_input("Tasa BCV / BDV (Bs)", min_value=0.0, value=571.00, step=1.00, key="global_tasa_bdv")
with col_g2:
    tasa_p2p_global = st.number_input("Tasa Binance P2P (Bs)", min_value=0.0, value=625.00, step=1.00, key="global_tasa_p2p")

st.markdown("---")

# --- SETUP CLOUD CONNECTION ---
try:
    if HAS_GSHEETS:
        conn = st.connection("gsheets", type=GSheetsConnection)
    else:
        conn = None
except Exception:
    conn = None

def guardar_operacion(tipo, inversion, recibido, ganancia, porcentaje):
    if conn is None:
        st.warning("Conexión a Google Sheets no configurada. (Revisa tus st.secrets)", icon=":material/warning:")
        return
    try:
        df = conn.read()
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
        
        df_actualizado = pd.concat([df, nueva_fila], ignore_index=True)
        conn.update(data=df_actualizado)
        st.success("Operación guardada en la Nube correctamente.", icon=":material/check_circle:")
    except Exception as e:
        st.error(f"Error al guardar en Google Sheets: {e}", icon=":material/error:")

tab1, tab2, tab_arb, tab3 = st.tabs(["Tradicional", "Modo Meta", "Arbitraje", "Historial"])

# ========================
# TAB 1 - TRADICIONAL
# ========================
with tab1:
    st.subheader("Cálculo Tradicional")
    total_disponible_bdv = st.number_input(
        "Dólares Totales Comprados en BDV ($)", 
        min_value=0.0, 
        value=21.00,
        step=0.10,
        help="El monto neto que el banco te acreditó en tu cuenta de divisas.",
        key="trad_usd"
    )

    if st.button("CALCULAR DIFERENCIA", use_container_width=True, key="btn_trad"):
        tasa_bdv = tasa_bdv_global
        tasa_p2p = tasa_p2p_global
        
        monto_bruto_bpay = total_disponible_bdv / (1 + com_uso_tarjeta)
        monto_bruto_bpay_seguro = math.floor(monto_bruto_bpay * 100) / 100
        usdt_recibidos = monto_bruto_bpay_seguro * (1 - com_bpay)
        costo_usd_en_cuenta = tasa_bdv * (1 + com_compra_divisa)
        total_bs_debitados = (monto_bruto_bpay_seguro * costo_usd_en_cuenta) * (1 + com_uso_tarjeta)
        
        costo_efectivo_usdt = total_bs_debitados / usdt_recibidos if usdt_recibidos > 0 else 0
        costo_p2p_directo = usdt_recibidos * tasa_p2p
        ganancia_bs = costo_p2p_directo - total_bs_debitados
        porcentaje_ganancia = ((tasa_p2p / costo_efectivo_usdt) - 1) * 100 if costo_efectivo_usdt > 0 else 0

        # Cálculo de Bs necesarios para comprar los dólares iniciales
        bs_para_comprar_divisas = total_disponible_bdv * tasa_bdv * (1 + com_compra_divisa)

        st.subheader("Resultados:")
        
        st.markdown(f"""
        <div class="metric-card" style="margin-bottom: 10px; border-left: 4px solid #4ade80;">
            <p style="color:#aaa; font-size:0.9em; margin:0;">Para comprar esos ${total_disponible_bdv:.2f} en el banco, necesitas:</p>
            <p style="color:#4ade80; font-size:1.8em; font-weight:bold; margin:0;">Bs {bs_para_comprar_divisas:,.2f}</p>
            <p style="color:#aaa; font-size:0.8em; margin:0;">(Incluye la comisión cambiaria del 0.5%)</p>
        </div>
        """, unsafe_allow_html=True)

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
            st.success(f"¡CONVIENE COMPRAR POR BPAY! Ganas {porcentaje_ganancia:.2f}%", icon=":material/check_circle:")
            ganancia_usdt = ganancia_bs / tasa_p2p
            st.info(f"Te ahorras/ganas: **{ganancia_bs:.2f} Bs** (~{ganancia_usdt:.2f} USDT)", icon=":material/savings:")
        else:
            st.error("NO CONVIENE BPAY. Mejor usa el P2P directo.", icon=":material/cancel:")
            st.error(f"Estás pagando **{abs(porcentaje_ganancia):.2f}%** de más.", icon=":material/trending_down:")
            
        st.markdown("---")
        if st.button("Guardar Operación en la Nube", icon=":material/cloud_upload:", key="save_trad"):
            guardar_operacion("Tradicional", total_bs_debitados, usdt_recibidos, ganancia_bs, porcentaje_ganancia)

# ========================
# TAB 2 - MODO META
# ========================
with tab2:
    st.subheader("Cálculo Inverso (Meta)")
    st.markdown("¿Cuántos Bolívares necesitas para llegar a una meta exacta de USDT?")
    meta_usdt = st.number_input("Meta deseada en Binance (USDT)", min_value=0.0, value=50.00, step=1.00, key="inv_usdt")
        
    if st.button("CALCULAR INVERSO", use_container_width=True, key="btn_inv"):
        tasa_bdv_inv = tasa_bdv_global
        tasa_p2p_inv = tasa_p2p_global
        
        bpay_deposit_requerido = meta_usdt / (1 - com_bpay)
        bpay_deposit_seguro = math.ceil(bpay_deposit_requerido * 100) / 100
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
            st.success(f"¡CONVIENE COMPRAR POR BPAY! Ganas {porcentaje_ganancia:.2f}%", icon=":material/check_circle:")
            ganancia_usdt = ganancia_bs / tasa_p2p_inv
            st.info(f"Te ahorras: **{ganancia_bs:,.2f} Bs** (~{ganancia_usdt:.2f} USDT) respecto al P2P.", icon=":material/savings:")
        else:
            st.error(f"NO CONVIENE BPAY. Mejor compra los {meta_usdt} USDT directo en P2P.", icon=":material/cancel:")
            
        st.markdown("---")
        if st.button("Guardar Operación en la Nube", icon=":material/cloud_upload:", key="save_inv"):
            guardar_operacion("Inverso", bs_totales_requeridos, meta_usdt, ganancia_bs, porcentaje_ganancia)

# ========================
# TAB ARB - ARBITRAJE
# ========================
with tab_arb:
    st.subheader("Arbitraje Completo")
    st.markdown("Simula el ciclo completo y descubre si el arbitraje es rentable.")
    
    modo = st.radio("Selecciona cómo vas a iniciar:", ["Comenzar con USDT en Binance", "Comenzar con Bolívares en el BDV"], horizontal=True)
    
    if modo == "Comenzar con USDT en Binance":
        usdt_inicial = st.number_input("USDT a Vender en P2P", min_value=0.0, value=100.00, step=1.00, key="arb_usdt_in")
                
        if st.button("CALCULAR ARBITRAJE", use_container_width=True, key="btn_arb_1"):
            tasa_p2p_venta = tasa_p2p_global
            tasa_bdv_compra = tasa_bdv_global
            
            bs_obtenidos = usdt_inicial * tasa_p2p_venta
            usd_bdv_comprados = bs_obtenidos / (tasa_bdv_compra * (1 + com_compra_divisa))
            comision_bdv_bs = usd_bdv_comprados * tasa_bdv_compra * com_compra_divisa
            
            monto_bpay = usd_bdv_comprados / (1 + com_uso_tarjeta)
            usdt_final = monto_bpay * (1 - com_bpay)
            
            ganancia_usdt = usdt_final - usdt_inicial
            rentabilidad = (usdt_final / usdt_inicial - 1) * 100 if usdt_inicial > 0 else 0
            
            # Flujo visual paso a paso
            st.markdown("#### :material/list_alt: Desglose de la Operación")
            
            st.markdown(f"""
            <div class="flow-step">
                <p class="step-label"><span class="material-symbols-rounded">swap_horiz</span> Vendes en Binance P2P</p>
                <p class="step-value">Recibes Bs {bs_obtenidos:,.2f}</p>
                <p style="color:#888; font-size:0.8em; margin:4px 0 0 0;">Por la venta de tus {usdt_inicial:,.2f} USDT</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="flow-connector">con esos bolívares compras divisas</div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="flow-step">
                <p class="step-label"><span class="material-symbols-rounded">account_balance</span> Compras Dólares en el BDV</p>
                <p class="step-value">Compras $ {usd_bdv_comprados:,.2f}</p>
                <p style="color:#888; font-size:0.8em; margin:4px 0 0 0;">Acreditados en tu cuenta de divisas</p>
                <p style="color:#888; font-size:0.8em; margin:2px 0 0 0;">Incluye comisión cambiaria (0.5%): <b>{comision_bdv_bs:,.2f} Bs</b></p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="flow-connector">luego depositas en BPay</div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="flow-step" style="border-left-color: #60a5fa;">
                <p class="step-label"><span class="material-symbols-rounded">credit_card</span> Depósito vía BPay</p>
                <p class="step-value" style="color: #60a5fa;">Ingresas $ {monto_bpay:,.2f}</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="flow-connector">y finalmente recibes en Binance</div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="flow-step" style="border-left-color: #4ade80;">
                <p class="step-label"><span class="material-symbols-rounded">check_circle</span> Llega a tu cuenta Binance</p>
                <p class="step-value" style="color: #4ade80; font-size: 1.8em;">{usdt_final:,.2f} USDT</p>
                <p style="color:#888; font-size:0.8em; margin:4px 0 0 0;">Después de comisiones de tarjeta y BPay</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Resultado final
            card_class = "result-card-green" if ganancia_usdt > 0 else "result-card-red"
            emoji = "🟢" if ganancia_usdt > 0 else "🔴"
            st.markdown(f"""
            <div class="{card_class}">
                <p style="color:#aaa; font-size:0.85em; margin:0;">{emoji} Ganancia Neta del Ciclo</p>
                <p style="color:{'#4ade80' if ganancia_usdt > 0 else '#f87171'}; font-size:2.2em; font-weight:bold; margin:5px 0;">
                    {'+' if ganancia_usdt > 0 else ''}{ganancia_usdt:,.2f} USDT
                </p>
                <p style="color:#ccc; font-size:0.9em; margin:0;">Rentabilidad: <b>{rentabilidad:.2f}%</b></p>
                <p style="color:#888; font-size:0.8em; margin:4px 0 0 0;">Invertiste {usdt_inicial:,.2f} USDT · Recuperaste {usdt_final:,.2f} USDT</p>
            </div>
            """, unsafe_allow_html=True)
            
            if ganancia_usdt > 0:
                st.success("¡El arbitraje es rentable!", icon=":material/check_circle:")
            else:
                st.error("El arbitraje arroja pérdidas.", icon=":material/cancel:")
                
            st.markdown("---")
            if st.button("Guardar Operación en la Nube", icon=":material/cloud_upload:", key="save_arb_1"):
                guardar_operacion("Arbitraje (USDT)", bs_obtenidos, usdt_final, ganancia_usdt * tasa_p2p_venta, rentabilidad)

    else:
        bs_iniciales = st.number_input("Bolívares Disponibles (Bs)", min_value=0.0, value=50000.00, step=100.0, key="arb_bs_in")
                
        if st.button("CALCULAR ARBITRAJE", use_container_width=True, key="btn_arb_2"):
            tasa_bdv_compra = tasa_bdv_global
            tasa_p2p_venta = tasa_p2p_global
            
            usd_bdv_comprados = bs_iniciales / (tasa_bdv_compra * (1 + com_compra_divisa))
            comision_bdv_bs = usd_bdv_comprados * tasa_bdv_compra * com_compra_divisa
            
            monto_bpay = usd_bdv_comprados / (1 + com_uso_tarjeta)
            usdt_final = monto_bpay * (1 - com_bpay)
            
            bs_finales = usdt_final * tasa_p2p_venta
            ganancia_bs = bs_finales - bs_iniciales
            rentabilidad = (bs_finales / bs_iniciales - 1) * 100 if bs_iniciales > 0 else 0
            
            # Flujo visual paso a paso
            st.markdown("#### :material/list_alt: Desglose de la Operación")
            
            st.markdown(f"""
            <div class="flow-step">
                <p class="step-label"><span class="material-symbols-rounded">account_balance</span> Compras Dólares en el BDV</p>
                <p class="step-value">Compras $ {usd_bdv_comprados:,.2f}</p>
                <p style="color:#888; font-size:0.8em; margin:4px 0 0 0;">Con tus Bs {bs_iniciales:,.2f} disponibles</p>
                <p style="color:#888; font-size:0.8em; margin:2px 0 0 0;">Comisión cambiaria (0.5%): <b>{comision_bdv_bs:,.2f} Bs</b></p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="flow-connector">luego depositas en BPay</div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="flow-step" style="border-left-color: #60a5fa;">
                <p class="step-label"><span class="material-symbols-rounded">credit_card</span> Depósito vía BPay</p>
                <p class="step-value" style="color: #60a5fa;">Ingresas $ {monto_bpay:,.2f}</p>
                
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="flow-connector">y finalmente recibes en Binance</div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="flow-step" style="border-left-color: #4ade80;">
                <p class="step-label"><span class="material-symbols-rounded">check_circle</span> Llega a tu cuenta Binance</p>
                <p class="step-value" style="color: #4ade80; font-size: 1.8em;">{usdt_final:,.2f} USDT</p>
                <p style="color:#888; font-size:0.8em; margin:4px 0 0 0;">Después de comisiones de tarjeta y BPay</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="flow-connector">que si vendieras en P2P equivaldrían a</div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="flow-step" style="border-left-color: #fbbf24;">
                <p class="step-label"><span class="material-symbols-rounded">payments</span> Valor en Bolívares</p>
                <p class="step-value" style="color: #fbbf24; font-size: 1.8em;">Bs {bs_finales:,.2f}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Resultado final
            card_class = "result-card-green" if ganancia_bs > 0 else "result-card-red"
            emoji = "🟢" if ganancia_bs > 0 else "🔴"
            st.markdown(f"""
            <div class="{card_class}">
                <p style="color:#aaa; font-size:0.85em; margin:0;">{emoji} Ganancia Neta del Ciclo</p>
                <p style="color:{'#4ade80' if ganancia_bs > 0 else '#f87171'}; font-size:2.2em; font-weight:bold; margin:5px 0;">
                    {'+' if ganancia_bs > 0 else ''}{ganancia_bs:,.2f} Bs
                </p>
                <p style="color:#ccc; font-size:0.9em; margin:0;">Rentabilidad: <b>{rentabilidad:.2f}%</b></p>
                <p style="color:#888; font-size:0.8em; margin:4px 0 0 0;">Empezaste con Bs {bs_iniciales:,.2f} · Terminaste con Bs {bs_finales:,.2f}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if ganancia_bs > 0:
                st.success("¡El arbitraje es rentable!", icon=":material/check_circle:")
            else:
                st.error("El arbitraje arroja pérdidas.", icon=":material/cancel:")
                
            st.markdown("---")
            if st.button("Guardar Operación en la Nube", icon=":material/cloud_upload:", key="save_arb_2"):
                guardar_operacion("Arbitraje (Bs)", bs_iniciales, usdt_final, ganancia_bs, rentabilidad)

# ========================
# TAB 3 - HISTORIAL
# ========================
with tab3:
    st.subheader("Historial de Operaciones en Google Sheets")
    if conn is None:
        st.warning("Para ver el historial, debes configurar los Secrets de Google Sheets en Streamlit Cloud.", icon=":material/warning:")
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
                
                if st.button("Actualizar Datos", icon=":material/refresh:"):
                    st.rerun()
        except Exception as e:
            st.error("No se pudo leer la base de datos de la nube. Asegúrate de que la hoja exista y tenga permisos.", icon=":material/error:")
            st.write(e)

st.markdown("---")
# Footer limpio
st.caption("Configurado con comisiones: BDV (0.5% + 2.5%) y Bpay (3.6%)")
