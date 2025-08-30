{\rtf1\ansi\ansicpg1252\cocoartf2822
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import io\
import numpy as np\
import pandas as pd\
import streamlit as st\
\
st.set_page_config(page_title="Modelo DuPont \'96 Rentabilidad de Negocios", layout="wide")\
\
st.title("Modelo DuPont \'96 Rentabilidad de Negocios")\
st.caption("Sube tu base de datos y genera el reporte con per\'edodos en columnas y conceptos en filas.")\
\
# ----------------------------\
# Utilidades\
# ----------------------------\
REQUIRED_LOGICAL_COLS = \{\
    "Periodo": "Periodo (ej. 2023, T1-2024, dic-2025)",\
    "Ventas Netas": "Ventas Netas",\
    "Utilidad Neta": "Utilidad Neta",\
    "Activos Totales": "Activos Totales",\
    "Capital Contable": "Capital Contable",\
\}\
\
def load_any(file):\
    if file.name.lower().endswith((".xlsx", ".xls")):\
        return pd.read_excel(file)\
    return pd.read_csv(file)\
\
def to_one_decimal(v):\
    try:\
        return np.round(v.astype(float), 1)\
    except Exception:\
        return v\
\
def excel_download(df, filename="reporte_dupont.xlsx"):\
    buf = io.BytesIO()\
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:\
        df.to_excel(writer, sheet_name="Reporte", index=True)\
        ws = writer.sheets["Reporte"]\
        ws.set_column(0, 0, 28)   # \'edndice\
        ws.set_column(1, 1 + len(df.columns), 14)\
    buf.seek(0)\
    st.download_button("\uc0\u11015 \u65039  Descargar reporte en Excel", buf, file_name=filename, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")\
\
def build_template():\
    data = \{\
        "Periodo": ["1992","1993","1994","1995","1996"],\
        "Ventas Netas": [1000, 1200, 900, 1500, 1800],\
        "Utilidad Neta": [67, 139, -39, 249, 377],\
        "Activos Totales": [500, 520, 480, 590, 620],\
        "Capital Contable": [250, 260, 240, 270, 300],\
    \}\
    return pd.DataFrame(data)\
\
# ----------------------------\
# Sidebar\
# ----------------------------\
st.sidebar.header("1) Carga de datos")\
uploaded = st.sidebar.file_uploader("Sube un archivo CSV o Excel", type=["csv", "xlsx", "xls"])\
st.sidebar.markdown("\'97 o \'97")\
if st.sidebar.button("Descargar plantilla CSV de ejemplo"):\
    tmpl = build_template()\
    st.sidebar.download_button(\
        "\uc0\u55357 \u56516  Plantilla.csv",\
        data=tmpl.to_csv(index=False).encode("utf-8"),\
        file_name="plantilla_dupont.csv",\
        mime="text/csv",\
    )\
\
# ----------------------------\
# Paso 2: Mapeo de columnas\
# ----------------------------\
df_raw = None\
if uploaded:\
    try:\
        df_raw = load_any(uploaded)\
        st.success("Archivo cargado correctamente.")\
        st.dataframe(df_raw.head(), use_container_width=True)\
    except Exception as e:\
        st.error(f"No pude leer el archivo: \{e\}")\
\
if df_raw is not None:\
    st.sidebar.header("2) Mapea tus columnas")\
    options = ["\'97 seleccionar \'97"] + list(df_raw.columns)\
    mapping = \{\}\
    for logical, label in REQUIRED_LOGICAL_COLS.items():\
        mapping[logical] = st.sidebar.selectbox(label, options, index=options.index(logical) if logical in options else 0, key=logical)\
\
    ready = all(mapping[k] != "\'97 seleccionar \'97" for k in REQUIRED_LOGICAL_COLS.keys())\
    if not ready:\
        st.info("Selecciona todas las columnas requeridas en la barra lateral.")\
        st.stop()\
\
    # Renombrar a nombres l\'f3gicos y tomar s\'f3lo columnas necesarias\
    df = df_raw.rename(columns=\{mapping[k]: k for k in REQUIRED_LOGICAL_COLS\})\
    df = df[list(REQUIRED_LOGICAL_COLS.keys())].copy()\
\
    # Normalizar Periodo a str para pivote\
    df["Periodo"] = df["Periodo"].astype(str)\
\
    # Agregaci\'f3n por per\'edodo (por si vienen m\'faltiples filas por per\'edodo)\
    grp = df.groupby("Periodo", dropna=False, as_index=False).sum(numeric_only=True)\
\
    # ----------------------------\
    # C\'e1lculos DuPont (seg\'fan f\'f3rmulas del usuario)\
    # ----------------------------\
    # Margen Neto (%) = Utilidad Neta / Ventas Netas\
    margen = grp["Utilidad Neta"] / grp["Ventas Netas"]\
\
    # Rotaci\'f3n (veces) = Ventas Netas / Activos Totales\
    rotacion = grp["Ventas Netas"] / grp["Activos Totales"]\
\
    # Apalancamiento (veces) = Activos Totales / Capital Contable\
    apalancamiento = grp["Activos Totales"] / grp["Capital Contable"]\
\
    # ROE (%) = Margen Neto \'d7 Rotaci\'f3n\
    roe = margen * rotacion\
\
    # ROA (%) = Rotaci\'f3n \'d7 Apalancamiento  (seg\'fan instrucci\'f3n proporcionada)\
    roa = rotacion * apalancamiento\
\
    # Pay Back Capital (veces) = 1 / ROE\
    payback_capital = pd.Series(np.where(roe != 0, 1 / roe, np.nan))\
\
    # Pay Back Activos (veces) = 1 / ROA\
    payback_activos = pd.Series(np.where(roa != 0, 1 / roa, np.nan))\
\
    # ----------------------------\
    # Armar reporte (filas=conceptos, columnas=per\'edodos)\
    # ----------------------------\
    periods = list(grp["Periodo"])\
    report = pd.DataFrame(index=[\
        "Margen Neto (%)",\
        "Rotaci\'f3n (veces)",\
        "Apalancamiento (veces)",\
        "ROE (%)",\
        "ROA (%)",\
        "Pay Back Capital (veces)",\
        "Pay Back Activos (veces)",\
    ], columns=periods, dtype=float)\
\
    # Cargar valores; relativos en % con un decimal, absolutos en veces con un decimal\
    def fmt_pct(series):\
        return to_one_decimal(series * 100.0)\
\
    def fmt_abs(series):\
        return to_one_decimal(series)\
\
    report.loc["Margen Neto (%)"] = fmt_pct(margen)\
    report.loc["Rotaci\'f3n (veces)"] = fmt_abs(rotacion)\
    report.loc["Apalancamiento (veces)"] = fmt_abs(apalancamiento)\
    report.loc["ROE (%)"] = fmt_pct(roe)\
    report.loc["ROA (%)"] = fmt_pct(roa)\
    report.loc["Pay Back Capital (veces)"] = fmt_abs(payback_capital)\
    report.loc["Pay Back Activos (veces)"] = fmt_abs(payback_activos)\
\
    # Mostrar como tabla con un decimal (y % donde aplique)\
    # Convertir a string con 1 decimal + a\'f1adir % a filas relativas\
    relative_rows = \{"Margen Neto (%)", "ROE (%)", "ROA (%)"\}\
    display = report.copy()\
    for r in display.index:\
        if r in relative_rows:\
            display.loc[r] = display.loc[r].map(lambda x: "" if pd.isna(x) else f"\{x:.1f\}%")\
        else:\
            display.loc[r] = display.loc[r].map(lambda x: "" if pd.isna(x) else f"\{x:.1f\}")\
\
    st.subheader("Reporte DuPont (columnas = per\'edodos, renglones = conceptos)")\
    st.dataframe(display, use_container_width=True)\
\
    # Descargar Excel\
    excel_download(report)\
\
else:\
    st.info("Carga un archivo o descarga la plantilla para comenzar.")}