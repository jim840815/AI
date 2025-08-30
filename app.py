import io
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Modelo DuPont – Rentabilidad de Negocios", layout="wide")

st.title("Modelo DuPont – Rentabilidad de Negocios")
st.caption("Sube tu base, mapea columnas y genera el reporte (columnas = períodos, renglones = conceptos).")

# ----------------------------
# Utilidades
# ----------------------------
REQUIRED_LOGICAL_COLS = {
    "Periodo": "Periodo (ej. 2023, T1-2024, dic-2025)",
    "Ventas Netas": "Ventas Netas",
    "Utilidad Neta": "Utilidad Neta",
    "Activos Totales": "Activos Totales",
    "Capital Contable": "Capital Contable",
}

def load_any(file):
    fname = file.name.lower()
    if fname.endswith((".xlsx", ".xls")):
        return pd.read_excel(file)
    return pd.read_csv(file)

def coerce_numeric(df, cols):
    for c in cols:
        # quitar separadores y convertir
        df[c] = (
            df[c]
            .astype(str)
            .str.replace(r"[,\s]", "", regex=True)
            .str.replace("%", "", regex=False)
        )
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def to_one_decimal(v):
    try:
        return np.round(v.astype(float), 1)
    except Exception:
        return v

def excel_download(df, filename="reporte_dupont.xlsx"):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Reporte", index=True)
        ws = writer.sheets["Reporte"]
        ws.set_column(0, 0, 28)
        ws.set_column(1, 1 + len(df.columns), 14)
    buf.seek(0)
    st.download_button(
        "⬇️ Descargar reporte en Excel",
        buf,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

def build_template():
    data = {
        "Periodo": ["1992","1993","1994","1995","1996"],
        "Ventas Netas": [1000, 1200, 900, 1500, 1800],
        "Utilidad Neta": [67, 139, -39, 249, 377],
        "Activos Totales": [500, 520, 480, 590, 620],
        "Capital Contable": [250, 260, 240, 270, 300],
    }
    return pd.DataFrame(data)

# ----------------------------
# Sidebar
# ----------------------------
st.sidebar.header("1) Carga de datos")
uploaded = st.sidebar.file_uploader("Sube un archivo CSV o Excel", type=["csv", "xlsx", "xls"])

if st.sidebar.button("Descargar plantilla CSV de ejemplo"):
    tmpl = build_template()
    st.sidebar.download_button(
        "📄 plantilla_dupont.csv",
        data=tmpl.to_csv(index=False).encode("utf-8"),
        file_name="plantilla_dupont.csv",
        mime="text/csv",
    )

df_raw = None
if uploaded:
    try:
        df_raw = load_any(uploaded)
        st.success("Archivo cargado correctamente.")
        st.dataframe(df_raw.head(), use_container_width=True)
    except Exception as e:
        st.error(f"No pude leer el archivo: {e}")

if df_raw is None:
    st.info("Carga un archivo o usa la plantilla para comenzar.")
    st.stop()

# ----------------------------
# Mapeo de columnas
# ----------------------------
st.sidebar.header("2) Mapea tus columnas")
options = ["— seleccionar —"] + list(df_raw.columns)
mapping = {}
for logical, label in REQUIRED_LOGICAL_COLS.items():
    mapping[logical] = st.sidebar.selectbox(
        label,
        options,
        index=options.index(logical) if logical in options else 0,
        key=logical,
    )

ready = all(mapping[k] != "— seleccionar —" for k in REQUIRED_LOGICAL_COLS.keys())
if not ready:
    st.warning("Selecciona todas las columnas requeridas en la barra lateral.")
    st.stop()

# Renombrar y tomar solo columnas requeridas
df = df_raw.rename(columns={mapping[k]: k for k in REQUIRED_LOGICAL_COLS})
df = df[list(REQUIRED_LOGICAL_COLS.keys())].copy()
df["Periodo"] = df["Periodo"].astype(str)

# Convertir a numérico por si vienen con comas o porcentajes
numeric_cols = ["Ventas Netas", "Utilidad Neta", "Activos Totales", "Capital Contable"]
df = coerce_numeric(df, numeric_cols)

# Agregar por período (si hay múltiples filas)
grp = df.groupby("Periodo", dropna=False, as_index=False).sum(numeric_only=True)

# ----------------------------
# Cálculos DuPont
# ----------------------------
# Evitar divisiones por cero
eps = 1e-12

margen = grp["Utilidad Neta"] / (grp["Ventas Netas"].replace(0, np.nan))
rotacion = grp["Ventas Netas"] / (grp["Activos Totales"].replace(0, np.nan))
apalancamiento = grp["Activos Totales"] / (grp["Capital Contable"].replace(0, np.nan))

roe = margen * rotacion
roa = rotacion * apalancamiento  # según tu indicación

payback_capital = 1 / roe.replace(0, np.nan)
payback_activos = 1 / roa.replace(0, np.nan)

# ----------------------------
# Reporte (filas = conceptos, columnas = períodos)
# ----------------------------
periods = list(grp["Periodo"])
report = pd.DataFrame(
    index=[
        "Margen Neto (%)",
        "Rotación (veces)",
        "Apalancamiento (veces)",
        "ROE (%)",
        "ROA (%)",
        "Pay Back Capital (veces)",
        "Pay Back Activos (veces)",
    ],
    columns=periods,
    dtype=float,
)

def fmt_pct(series):  # relativo con 1 decimal
    return to_one_decimal(series * 100.0)

def fmt_abs(series):  # absoluto con 1 decimal
    return to_one_decimal(series)

report.loc["Margen Neto (%)"] = fmt_pct(margen)
report.loc["Rotación (veces)"] = fmt_abs(rotacion)
report.loc["Apalancamiento (veces)"] = fmt_abs(apalancamiento)
report.loc["ROE (%)"] = fmt_pct(roe)
report.loc["ROA (%)"] = fmt_pct(roa)
report.loc["Pay Back Capital (veces)"] = fmt_abs(payback_capital)
report.loc["Pay Back Activos (veces)"] = fmt_abs(payback_activos)

# Vista formateada para pantalla (añadiendo % en filas relativas)
relative_rows = {"Margen Neto (%)", "ROE (%)", "ROA (%)"}
display = report.copy()
for r in display.index:
    if r in relative_rows:
        display.loc[r] = display.loc[r].map(lambda x: "" if pd.isna(x) else f"{x:.1f}%")
    else:
        display.loc[r] = display.loc[r].map(lambda x: "" if pd.isna(x) else f"{x:.1f}")

st.subheader("Reporte DuPont (columnas = períodos, renglones = conceptos)")
st.dataframe(display, use_container_width=True)

excel_download(report)
