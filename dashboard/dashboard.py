# dashboard.py
import os
import io
from datetime import datetime
import pandas as pd
import numpy as np
import psycopg2
from psycopg2.extras import RealDictCursor
import plotly.express as px
from PIL import Image
import base64
import streamlit as st
from config import POSTGRES_CONFIG

st.set_page_config(page_title="Painel EBITDA", layout="wide", initial_sidebar_state="expanded")


# ----------------------------
# DB connection helper
# ----------------------------
def get_connection():
    return psycopg2.connect(
        host=POSTGRES_CONFIG['host'],
        port=POSTGRES_CONFIG['port'],
        user=POSTGRES_CONFIG['user'],
        password=POSTGRES_CONFIG['password'],
        dbname=POSTGRES_CONFIG['database'],
        sslmode="require"
    )

# ----------------------------
# Load data (cached)
# ----------------------------
@st.cache_data(ttl=300)
def load_data():
    conn = get_connection()
    try:
        # Select essential columns
        query = """
        SELECT id, banco, trimestre, valores, data_publicada, data_atualizacao
        FROM valores_novo
        ORDER BY data_publicada NULLS LAST;
        """
        df = pd.read_sql(query, conn, parse_dates=["data_publicada", "data_atualizacao"])
    finally:
        conn.close()

    # Normalize/clean dataframe
    # Ensure 'valores' numeric
    if "valores" in df.columns:
        df["valores"] = pd.to_numeric(df["valores"], errors="coerce").fillna(0.0)

    # Derive year & quarter from data_publicada if possible, otherwise parse 'trimestre'
    def derive_year_quarter(row):
        if pd.notna(row["data_publicada"]):
            d = row["data_publicada"]
            year = d.year
            # pandas quarter (1-4) from month
            quarter = (d.month - 1) // 3 + 1
            return year, int(quarter)
        # fallback parse from 'trimestre' like '1T25' or '1T2025'
        t = row.get("trimestre")
        if isinstance(t, str):
            m = None
            # common patterns: '1T25', 'Q1 2025', '1T2025'
            # try regex
            import re
            mm = re.match(r"^\s*([1-4])\s*[TtQq]?\s*[-/]?\s*(\d{2,4})\s*$", t)
            if mm:
                q = int(mm.group(1))
                ystr = mm.group(2)
                if len(ystr) == 2:
                    # heuristic: 00-25 -> 2000-2025
                    y2 = int(ystr)
                    base = 2000
                    year = base + y2
                else:
                    year = int(ystr)
                return year, q
        # ultimate fallback: NaNs
        return np.nan, np.nan

    yrs = df.apply(derive_year_quarter, axis=1)
    df["year"] = yrs.apply(lambda x: x[0])
    df["q"] = yrs.apply(lambda x: x[1])

    # create a period column like 'YYYY-Qn' and a datetime representative for plotting
    def period_to_date(row):
        try:
            y = int(row["year"])
            q = int(row["q"])
            month = (q - 1) * 3 + 1
            return datetime(y, month, 1)
        except Exception:
            # fallback to data_publicada
            return row["data_publicada"]

    df["period_start"] = df.apply(period_to_date, axis=1)
    df = df.sort_values(by=["period_start"]).reset_index(drop=True)

    # For convenience, create human readable quarter label
    df["quarter_label"] = df.apply(lambda r: f"{int(r['q'])}T{int(r['year'])}" if pd.notna(r["q"]) and pd.notna(r["year"]) else (
        r["trimestre"] if pd.notna(r.get("trimestre")) else ""), axis=1)

    return df


# ----------------------------
# Utility functions
# ----------------------------
def compute_kpis(df_filtered):
    # Latest row by period_start
    if df_filtered.empty:
        return {"last_value": 0.0, "last_period": None, "qoq": None, "yoy": None, "year_avg": None}

    df_ts = df_filtered.dropna(subset=["period_start"]).sort_values("period_start")
    # aggregate by period_start (in case multiple records per period) - sum by default
    df_period = df_ts.groupby("period_start", as_index=False)["valores"].sum().sort_values("period_start")
    last = df_period.iloc[-1]
    last_value = float(last["valores"])
    last_period = last["period_start"]

    # QoQ: compare to previous period
    if len(df_period) >= 2:
        prev = df_period.iloc[-2]["valores"]
        qoq = (last_value - float(prev)) / float(prev) if float(prev) != 0 else None
    else:
        qoq = None

    # YoY: find same quarter previous year (approx by date - 365 days)
    same_period_prev_year = last_period.replace(year=last_period.year - 1)
    yoy = None
    # find closest matching period_start same quarter previous year
    prev_year_row = df_period[df_period["period_start"] == same_period_prev_year]
    if not prev_year_row.empty:
        prev_val = float(prev_year_row.iloc[0]["valores"])
        yoy = (last_value - prev_val) / prev_val if prev_val != 0 else None

    # Year average (current year)
    cur_year = last_period.year
    year_vals = df_period[df_period["period_start"].dt.year == cur_year]["valores"]
    year_avg = float(year_vals.mean()) if not year_vals.empty else None

    return {"last_value": last_value, "last_period": last_period, "qoq": qoq, "yoy": yoy, "year_avg": year_avg}


def format_currency(x):
    if x is None:
        return "—"
    # display with separators and two decimals; values likely large so show in billions if appropriate
    try:
        if abs(x) >= 1e9:
            return f"{x/1e9:,.2f} B"
        if abs(x) >= 1e6:
            return f"{x/1e6:,.2f} M"
        return f"{x:,.2f}"
    except Exception:
        return str(x)


# ----------------------------
# Streamlit layout
# ----------------------------
st.title("Painel EBITDA — 2008–2025")
st.markdown("Painel interativo para análise do EBITDA por trimestre/ano. Dados carregados da tabela `valores_novo`.")




# === LOGO no SIDEBAR acima dos filtros ===
logo_path = os.path.join(os.path.dirname(__file__), "b3.jpg")

if os.path.exists(logo_path):
    # Carregar a logo local em base64 para embutir no HTML
    with open(logo_path, "rb") as f:
        img_bytes = f.read()
    img_base64 = base64.b64encode(img_bytes).decode()

    st.sidebar.markdown(
        f"""
        <div style="text-align: center;">
            <img src="data:image/png;base64,{img_base64}" width="140">
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    # fallback online
    st.sidebar.markdown(
        """
        <div style="text-align: center;">
            <img src="https://logodownload.org/wp-content/uploads/2019/06/b3-logo.png" width="140">
        </div>
        """,
        unsafe_allow_html=True
    )

st.sidebar.markdown("---")

st.sidebar.header("Filtros")  # agora os filtros virão abaixo do logo

df = load_data()

if df.empty:
    st.warning("Nenhum dado disponível na tabela `valores_novo`.")
    st.stop()

bancos = sorted(df["banco"].fillna("N/A").unique())
banco_sel = st.sidebar.selectbox("Banco", bancos, index=0)

year_min = int(df["year"].dropna().min())
year_max = int(df["year"].dropna().max())
yr_range = st.sidebar.slider("Intervalo de anos", year_min, year_max, (year_min, year_max))

agg_option = st.sidebar.radio("Agregação anual", ("sum", "mean"))
display_mode = st.sidebar.radio("Exibir", ("Valores absolutos", "Variação % (YoY)"))

# Filter dataframe
df = df[df["banco"] == banco_sel].copy()
df = df[(df["year"] >= yr_range[0]) & (df["year"] <= yr_range[1])]

# Main KPIs
kpis = compute_kpis(df)
col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
col1.metric("Último EBITDA", format_currency(kpis["last_value"]), delta=None)
col2.metric("Período", kpis["last_period"].strftime("%Y-%m") if kpis["last_period"] is not None else "—")
col3.metric("Variação QoQ", f"{kpis['qoq']*100:.2f}%" if kpis["qoq"] is not None else "—")
col4.metric("Variação YoY", f"{kpis['yoy']*100:.2f}%" if kpis["yoy"] is not None else "—")

st.markdown("---")

# Time series: aggregate by period_start
ts = df.dropna(subset=["period_start"]).groupby("period_start", as_index=False)["valores"].sum().sort_values("period_start")
if display_mode == "Variação % (YoY)":
    ts["val_pct_yoy"] = ts["valores"].pct_change(periods=4) * 100
    y_col = "val_pct_yoy"
    y_title = "Variação YoY (%)"
else:
    y_col = "valores"
    y_title = "EBITDA"

# Line chart
st.subheader("Evolução temporal")
fig_line = px.line(ts, x="period_start", y=y_col, markers=True, title=f"{y_title} — {banco_sel}")
fig_line.update_layout(xaxis_title="Período", yaxis_title=y_title)
st.plotly_chart(fig_line, use_container_width=True)

# Annual aggregation
st.subheader("Consolidação anual")
if agg_option == "sum":
    annual = df.groupby("year", as_index=False)["valores"].sum().sort_values("year")
else:
    annual = df.groupby("year", as_index=False)["valores"].mean().sort_values("year")

fig_bar = px.bar(annual, x="year", y="valores", title=f"EBITDA anual ({'soma' if agg_option=='sum' else 'média'})")
fig_bar.update_layout(xaxis_title="Ano", yaxis_title="EBITDA")
st.plotly_chart(fig_bar, use_container_width=True)

# Heatmap: year x quarter
st.subheader("Heatmap: Ano × Trimestre")
# pivot table: rows year, cols quarter number 1-4
heat_df = df.dropna(subset=["year", "q"]).pivot_table(index="year", columns="q", values="valores", aggfunc="sum", fill_value=0)
# order columns 1..4
heat_df = heat_df.reindex(columns=[1, 2, 3, 4], fill_value=0)
fig_heat = px.imshow(heat_df, aspect="auto", labels=dict(x="Trimestre", y="Ano", color="EBITDA"), x=[1,2,3,4])
fig_heat.update_xaxes(side="top")
st.plotly_chart(fig_heat, use_container_width=True)

# Ranking top/bottom periods
st.subheader("Ranking — Top 5 / Bottom 5 trimestres")
by_period = df.dropna(subset=["period_start"]).groupby("period_start", as_index=False)["valores"].sum()
top5 = by_period.nlargest(5, "valores")
bottom5 = by_period.nsmallest(5, "valores")

c1, c2 = st.columns(2)
with c1:
    st.markdown("**Top 5 trimestres**")
    fig_top = px.bar(top5.sort_values("valores"), x="valores", y=top5["period_start"].dt.strftime("%Y-%m"), orientation="h")
    st.plotly_chart(fig_top, use_container_width=True)
with c2:
    st.markdown("**Bottom 5 trimestres**")
    fig_bottom = px.bar(bottom5.sort_values("valores", ascending=True), x="valores", y=bottom5["period_start"].dt.strftime("%Y-%m"), orientation="h")
    st.plotly_chart(fig_bottom, use_container_width=True)

st.markdown("---")

# Data table and download
st.subheader("Dados detalhados")
table_df = df[["id", "banco", "quarter_label", "year", "q", "valores", "data_publicada", "data_atualizacao"]].copy()
table_df = table_df.rename(columns={"quarter_label": "trimestre_label", "valores": "EBITDA"})
st.dataframe(table_df.sort_values(["year", "q"], ascending=[False, False]))

# CSV download
csv = table_df.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Baixar CSV", data=csv, file_name=f"valores_{banco_sel}_{yr_range[0]}_{yr_range[1]}.csv", mime="text/csv")

st.markdown("---")

# Insights automáticos simples
st.subheader("Insights automáticos")
insights = []
if kpis["last_value"] and kpis["qoq"] is not None:
    insights.append(f"O EBITDA mais recente ({kpis['last_period'].strftime('%Y-%m')}) é {format_currency(kpis['last_value'])}.")
    if kpis["qoq"] is not None:
        insights.append(f"Variação QoQ: {kpis['qoq']*100:.2f}%")
    if kpis["yoy"] is not None:
        insights.append(f"Variação YoY: {kpis['yoy']*100:.2f}%")
if not insights:
    st.info("Não há insights suficientes (poucos dados).")
else:
    for ins in insights:
        st.write("- " + ins)

st.markdown("### Observações")
st.write("""
- Valores agrupados por período (trimestre) e consolidados.  
- Heatmap mostra intensidade por trimestre ao longo dos anos.  
- Caso os períodos não venham corretamente da coluna `data_publicada`, o painel tenta inferir a partir do campo `trimestre`.  
""")
