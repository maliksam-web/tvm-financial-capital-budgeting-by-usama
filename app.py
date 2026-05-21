import streamlit as st
import numpy_financial as npf
import pandas as pd
import numpy as np

# --- ENTERPRISE FINANCIAL MATH FUNCTIONS ---

def calculate_advanced_metrics(initial_investment, cash_flows, discount_rate):
    """Calculates standard PBP, Discounted PBP, NPV, IRR, and PI."""
    # Build a clean ledger dataframe
    years = [f"Year {i+1}" for i in range(len(cash_flows))]
    df = pd.DataFrame(index=years)
    df["Cash Flow"] = cash_flows
    
    # Calculate Present Values (PV)
    df["Discount Factor"] = [1 / ((1 + discount_rate) ** (i + 1)) for i in range(len(cash_flows))]
    df["Present Value"] = df["Cash Flow"] * df["Discount Factor"]
    
    # Calculate Cumulative Tracks
    df["Cum. Cash Flow"] = df["Cash Flow"].cumsum() - initial_investment
    df["Cum. Present Value"] = df["Present Value"].cumsum() - initial_investment

    # 1. Standard Payback Period
    pbp = None
    cum_cf = -initial_investment
    for i, cf in enumerate(cash_flows):
        prev_cum = cum_cf
        cum_cf += cf
        if cum_cf >= 0:
            pbp = i + (abs(prev_cum) / cf)
            break

    # 2. Discounted Payback Period (DPP)
    dpp = None
    cum_pv = -initial_investment
    for i, pv in enumerate(df["Present Value"]):
        prev_cum_pv = cum_pv
        cum_pv += pv
        if cum_pv >= 0:
            dpp = i + (abs(prev_cum_pv) / pv)
            break

    # 3. NPV & IRR & PI
    full_cfs = [-initial_investment] + cash_flows
    npv = npf.npv(discount_rate, full_cfs)
    
    try:
        irr = npf.irr(full_cfs) * 100
    except Exception:
        irr = None
        
    pi = (npv + initial_investment) / initial_investment if initial_investment > 0 else 0
    
    return npv, irr, pbp, dpp, pi, df

# --- UI SETUP ---
st.set_page_config(page_title="Strategic Capital Budgeting Suite", layout="wide")

# 🛑 HARDENED MOBILE SCROLL-LOCK FILTER (Injected directly into browser window tree)
st.markdown("""
    <style>
    /* Force lock structural view containers on Android System WebView */
    html, body, [data-testid="stAppViewContainer"], .main, .block-container {
        overscroll-behavior-y: contain !important;
        overscroll-behavior-x: none !important;
        overflow-y: auto !important;
    }
    .main .block-container {padding-top: 2rem;}
    div[data-testid="stMetricValue"] {font-size: 24px; font-weight: bold;}
    </style>
    
    <script>
    // Intercept downward drag vectors right at the page ceiling boundary
    let touchStartOffsetY = 0;
    
    window.addEventListener('touchstart', function(e) {
        touchStartOffsetY = e.touches[0].clientY;
    }, { passive: false });

    window.addEventListener('touchmove', function(e) {
        let touchCurrentOffsetY = e.touches[0].clientY;
        let diffY = touchCurrentOffsetY - touchStartOffsetY;
        
        // If device context viewport is pinned at 0 and pulls down, cancel event action
        if (window.scrollY === 0 && diffY > 0) {
            e.preventDefault();
        }
    }, { passive: false });
    </script>
""", unsafe_allow_html=True)

st.title("🦅 Strategic Capital Budgeting Suite")
st.caption("Enterprise Risk Analytics & Scenario Valuation Modeler")
st.divider()

# --- SIDEBAR INTERACTIVE INPUTS ---
st.sidebar.header("📊 Investment Variables")

initial_investment = st.sidebar.number_input(
    "Capital Allocation Outlay ($)", 
    min_value=1000.0, value=100000.0, step=5000.0, format="%.2f"
)

wacc_input = st.sidebar.slider(
    "Base Cost of Capital (WACC %)", 
    min_value=1.0, max_value=25.0, value=10.0, step=0.25
)
base_rate = wacc_input / 100

# Advanced Feature: Scenario Adjustments
st.sidebar.subheader("🎭 Market Risk Scenario")
scenario = st.sidebar.radio(
    "Select Forecasting Lens:",
    ["Base Case (As Projected)", "Optimistic Case (+15% Inflows)", "Pessimistic Case (-20% Inflows)"]
)

st.sidebar.divider()
st.sidebar.write("⚡ *Calculations refresh instantaneously upon field modification.*")

# --- MAIN SCREEN: EXCEL-STYLE DATA INPUT ---
st.subheader("📅 Cash Flow Schedule Configuration")
st.write("Modify values inside the table grid below to match your asset lifecycle forecasts:")

# Initialize default rows
init_df = pd.DataFrame(
    {"Estimated Annual Inflow ($)": [30000.0, 35000.0, 45000.0, 40000.0, 30000.0]},
    index=["Year 1", "Year 2", "Year 3", "Year 4", "Year 5"]
)

# Render editable spreadsheet container
edited_df = st.data_editor(init_df, use_container_width=True, num_rows="dynamic")

# Process grid outputs
raw_cash_flows = edited_df["Estimated Annual Inflow ($)"].dropna().tolist()

if len(raw_cash_flows) > 0:
    # Apply scenario multipliers
    if scenario == "Optimistic Case (+15% Inflows)":
        processed_cash_flows = [cf * 1.15 for cf in raw_cash_flows]
    elif scenario == "Pessimistic Case (-20% Inflows)":
        processed_cash_flows = [cf * 0.80 for cf in raw_cash_flows]
    else:
        processed_cash_flows = raw_cash_flows

    # Execute engine math
    npv, irr, pbp, dpp, pi, metrics_df = calculate_advanced_metrics(initial_investment, processed_cash_flows, base_rate)

    # --- TOP LEVEL SAAS METRICS DISPLAY ---
    st.divider()
    st.subheader("📊 Capital Budgeting KPIs")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="Net Present Value (NPV)", 
            value=f"${npv:,.2f}", 
            delta="🟢 Feasible" if npv >= 0 else "🔴 Unfeasible",
            delta_color="normal" if npv >= 0 else "inverse"
        )
    with col2:
        irr_txt = f"{irr:.2f}%" if irr is not None else "Error"
        st.metric(
            label="Internal Rate (IRR)", 
            value=irr_txt,
            delta="🟢 IRR > WACC" if (irr and irr > wacc_input) else "🔴 IRR < WACC",
            delta_color="normal" if (irr and irr > wacc_input) else "inverse"
        )
    with col3:
        pbp_txt = f"{pbp:.2f} Yrs" if pbp is not None else "N/A"
        st.metric(label="Simple Payback", value=pbp_txt)
    with col4:
        dpp_txt = f"{dpp:.2f} Yrs" if dpp is not None else "N/A"
        st.metric(label="Discounted Payback", value=dpp_txt)
    with col5:
        st.metric(
            label="Profitability Index", 
            value=f"{pi:.2f}x",
            delta="Value Adding" if pi >= 1.0 else "Value Destroying",
            delta_color="normal" if pi >= 1.0 else "inverse"
        )

    # --- ADVANCED GRAPHICAL INTERFACES ---
    st.divider()
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.subheader("📈 Cumulative Recovery Trajectory")
        plot_df = metrics_df[["Cum. Cash Flow", "Cum. Present Value"]].copy()
        origin = pd.DataFrame([[-initial_investment, -initial_investment]], 
                             columns=["Cum. Cash Flow", "Cum. Present Value"], index=["Year 0"])
        plot_df = pd.concat([origin, plot_df])
        st.line_chart(plot_df, use_container_width=True)
        
    with chart_col2:
        st.subheader("📉 WACC Cost Sensitivity Scale")
        rates = np.linspace(0.01, 0.25, 20)
        npvs = [npf.npv(r, [-initial_investment] + processed_cash_flows) for r in rates]
        sensitivity_df = pd.DataFrame({"WACC %": rates * 100, "Project NPV ($)": npvs}).set_index("WACC %")
        st.line_chart(sensitivity_df, use_container_width=True)

    # --- DETAILED LEDGER DATAFRAME ---
    st.divider()
    st.subheader("📑 Financial Amortization Ledger")
    format_dict = {
        "Cash Flow": "${:,.2f}", "Discount Factor": "{:.4f}", 
        "Present Value": "${:,.2f}", "Cum. Cash Flow": "${:,.2f}", "Cum. Present Value": "${:,.2f}"
    }
    st.dataframe(metrics_df.style.format(format_dict), use_container_width=True)

else:
    st.info("💡 Please type at least one valid future cash flow item inside the data schedule grid above.")
