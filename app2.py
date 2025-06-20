import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# Cargar datos
@st.cache_data
def cargar_datos():
    xls = pd.ExcelFile("C:\\Users\\RONAL\\Documents\\unal\\Proyecto_investigacion.xlsx")
    hojas = {sheet: xls.parse(sheet) for sheet in xls.sheet_names}
    return hojas

datos = cargar_datos()
paises = list(datos.keys())
paises.remove("TOTAL")


# Selección de país socio
pais_seleccionado = st.selectbox("Selecciona un país socio de Colombia", paises)
df = datos[pais_seleccionado]
df.columns = df.columns.str.strip()
# Convertir columna 'Años' a datetime
df["Años"] = pd.to_datetime(df["Años"], format="%Y")

# Variables numéricas disponibles
columnas_numericas = df.select_dtypes(include="number").columns.tolist()

# Visualización de series de tiempo
st.header("📊 Series de tiempo")
variables = st.multiselect("Selecciona variables para visualizar", columnas_numericas, default=columnas_numericas[:1])
if variables:
    df_plot = df.set_index("Años")
    st.line_chart(df_plot[variables])

# ------------------- Análisis de correlación por país socio -------------------
st.markdown("---")
st.header("📈 Correlación entre variables bilaterales")

# Selección de variables numéricas para correlación
variables_corr = st.multiselect("Selecciona variables para analizar correlación", columnas_numericas, default=columnas_numericas[:5])

# Tipo de transformación
tipo_transformacion = st.radio(
    "¿Cómo deseas transformar las variables antes de calcular la correlación?",
    options=["Original", "Crecimiento porcentual (%)", "Primera diferencia (Δ)"]
)

# Opción de aplicar logaritmo
aplicar_log_corr = st.checkbox("Aplicar logaritmo natural (ln)", key="log_corr")

# Procesamiento
if variables_corr:
    df_corr = df[variables_corr].copy()
    df_corr = df_corr.replace(0, pd.NA)  # evitar log(0)

    # Aplicar transformación elegida
    if tipo_transformacion == "Crecimiento porcentual (%)":
        df_corr = df_corr.pct_change() * 100
        st.info("Transformación aplicada: crecimiento porcentual anual.")
    elif tipo_transformacion == "Primera diferencia (Δ)":
        df_corr = df_corr.diff()
        st.info("Transformación aplicada: primera diferencia entre años.")
    else:
        st.info("Usando valores originales (sin transformar).")

    # Aplicar logaritmo si se seleccionó
    if aplicar_log_corr:
        df_corr = np.log(df_corr)

    # Eliminar filas con datos faltantes
    df_corr = df_corr.dropna(how="any")

    # Matriz de correlación
    if not df_corr.empty:
        corr_matrix = df_corr.corr()
        st.subheader("🔍 Matriz de Correlación")
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", fmt=".2f", ax=ax)
        st.pyplot(fig)
    else:
        st.warning("No hay suficientes datos válidos tras la transformación.")
else:
    st.warning("Selecciona al menos una variable para la correlación.")

# ------------------- Estadística descriptiva -------------------
st.markdown("---")
st.header("📊 Estadística descriptiva de las variables seleccionadas")

variables_desc = st.multiselect("Selecciona variables para describir", columnas_numericas, default=["IGL total"])

if variables_desc:
    df_desc = df[variables_desc].describe().T
    df_desc["coef_variación"] = df_desc["std"] / df_desc["mean"]
    df_desc = df_desc.rename(columns={
        "mean": "Media",
        "std": "Desv. estándar",
        "min": "Mínimo",
        "25%": "Percentil 25",
        "50%": "Mediana",
        "75%": "Percentil 75",
        "max": "Máximo",
        "coef_variación": "Coef. variación"
    })
    st.dataframe(df_desc.style.format("{:.2f}"))
else:
    st.warning("Selecciona al menos una variable.")

# ------------------- Análisis de componentes del IGL -------------------
st.markdown("---")
st.header("📈 Análisis de los componentes del IGL")
st.write("Columnas disponibles:", df.columns.tolist())

df.columns = df.columns.str.strip()
# Selección de países
paises_igl = st.multiselect("Selecciona países para analizar el IGL", paises, default=paises[:1])

# Selección de año
año_igl = st.selectbox("Selecciona un año (o analiza todos)", options=["Todos los años"] + sorted(df["Años"].dt.year.unique().tolist()))

# Combinar hojas de países seleccionados
df_igl = pd.DataFrame()
for p in paises_igl:
    temp = datos[p].copy()
    temp["Años"] = pd.to_datetime(temp["Años"], format="%Y")
    temp["País"] = p
    df_igl = pd.concat([df_igl, temp], ignore_index=True)

# Filtrar por año si se eligió
if año_igl != "Todos los años":
    df_igl = df_igl[df_igl["Años"].dt.year == año_igl]

# Verificar columnas necesarias
cols_igl = [
    "IGL total",
    "IGL vertical alta calidad",
    "IGL vertical baja calidad",
    "IGL Horizontal", "IGL vertical"
]
if all(col in df_igl.columns for col in cols_igl):

    # Mostrar valor máximo del IGL total
    max_row = df_igl.loc[df_igl["IGL total"].idxmax()]
    st.markdown(f"""
    #### 🏆 Mayor IGL total
    - **País socio**: `{max_row["País"]}`
    - **Año**: `{max_row["Años"].year}`
    - **Valor IGL total(MAX)**: `{max_row["IGL total"]:.4f}`
    """)

    # Calcular correlaciones con IGL total
    componentes = cols_igl[1:]
    df_corr_igl = df_igl[cols_igl].dropna()
    correlaciones = df_corr_igl.corr()["IGL total"].loc[componentes].sort_values(ascending=False)

    st.subheader("📊 Correlación de componentes con IGL total")
    st.bar_chart(correlaciones)

else:
    st.warning("Faltan columnas necesarias para calcular los componentes del IGL.")