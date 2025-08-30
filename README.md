# 📊 Modelo DuPont – Rentabilidad de Negocios

Aplicación interactiva en **Streamlit** que permite medir la **rentabilidad de negocios** utilizando el **modelo DuPont**.  
La app genera un **reporte en formato tabular** (columnas = períodos, renglones = conceptos) a partir de una base de datos cargada por el usuario.

---

## ⚙️ Funcionalidades

- Carga de archivos **CSV o Excel** con la información financiera.
- Posibilidad de **mapear las columnas** de tu base de datos a los campos requeridos.
- Cálculo automático de los indicadores del **modelo DuPont**:
  - Margen Neto (%)
  - Rotación (veces)
  - Apalancamiento (veces)
  - ROE (%)
  - ROA (%)
  - Pay Back Capital (veces)
  - Pay Back Activos (veces)
- Resultados en **un decimal**:
  - **Valores relativos (%)**: Margen, ROE, ROA
  - **Valores absolutos (veces)**: Rotación, Apalancamiento, Pay Back
- Generación de un **reporte en tabla** y opción para **descargar en Excel**.

---

## 📥 Requisitos de la base de datos

Tu archivo debe contener al menos estas columnas (los nombres pueden variar, ya que en la app podrás mapearlos):

- **Periodo** (ejemplo: 2022, T1-2023, dic-2024)  
- **Ventas Netas**  
- **Utilidad Neta**  
- **Activos Totales**  
- **Capital Contable**  

👉 Si tienes múltiples filas por período, la app las **sumará automáticamente**.

---

## 🖥️ Uso local

1. Clona este repositorio:

   ```bash
   git clone https://github.com/tu_usuario/tu_repo.git
   cd tu_repo
