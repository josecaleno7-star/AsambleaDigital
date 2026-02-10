import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from database import inicializar_db, guardar_voto, obtener_totales

st.set_page_config(page_title="Sistema de Poderes PH", layout="centered")

# --- CARGA DE DATOS ---
@st.cache_data
def cargar_censo():
    df = pd.read_excel("censo.xlsx")
    df.columns = df.columns.str.strip()
    df['id_unidad'] = df['Torre'].astype(str) + " " + df['Unidad'].astype(str)
    return df

try:
    censo_df = cargar_censo()
except:
    st.error("Por favor sube el archivo 'censo.xlsx' con la columna 'Apoderado_ID'")
    st.stop()

st.title("🗳️ Votación por Representación")
st.markdown("---")

# --- PROCESO DE VOTACIÓN ---
id_usuario = st.text_input("Ingrese su Cédula o ID de Apoderado:", placeholder="Ej: 12345678")

if id_usuario:
    # Buscamos todas las unidades que este ID representa
    unidades_representadas = censo_df[censo_df['Apoderado_ID'].astype(str) == id_usuario]
    
    if not unidades_representadas.empty:
        total_unidades = len(unidades_representadas)
        coef_total_grupo = unidades_representadas['Coeficiente'].sum()
        
        st.info(f"👤 **Apoderado reconocido.** Representa a **{total_unidades}** unidades.")
        st.write(f"🏢 **Unidades:** {', '.join(unidades_representadas['id_unidad'].tolist())}")
        st.write(f"📊 **Coeficiente Total:** {coef_total_grupo:.4f}%")

        # Verificar si alguna de estas unidades ya votó
        conn = sqlite3.connect("asamblea.db")
        votos_existentes = pd.read_sql_query("SELECT unidad FROM votos", conn)['unidad'].tolist()
        conn.close()
        
        ya_voto = any(u in votos_existentes for u in unidades_representadas['id_unidad'])

        if not ya_voto:
            with st.form("voto_grupal"):
                st.subheader("¿Cuál es su decisión para todas sus unidades?")
                decision = st.radio("Seleccione una opción:", ["Favor", "Contra"], horizontal=True)
                
                if st.form_submit_button("REGISTRAR VOTOS MASIVOS"):
                    for _, fila in unidades_representadas.iterrows():
                        guardar_voto(fila['id_unidad'], fila['Coeficiente'], decision)
                    st.success(f"¡Éxito! Se han registrado {total_unidades} votos bajo su representación.")
                    st.balloons()
        else:
            st.warning("⚠️ El sistema detectó que estas unidades ya ejercieron su derecho al voto.")
    else:
        st.error("El ID ingresado no coincide con ningún apoderado en el censo.")

# --- RESULTADOS ---
st.markdown("---")
if st.button("Ver Resultados de la Asamblea"):
    totales = obtener_totales()
    if totales:
        fig, ax = plt.subplots()
        ax.pie(totales.values(), labels=totales.keys(), autopct='%1.1f%%', colors=['#2ecc71', '#e74c3c'])
        st.pyplot(fig)
    else:
        st.write("Aún no hay votos registrados.")
@st.cache_data
def cargar_censo():
    # Forzamos que la columna Apoderado_ID sea leída como TEXTO (str)
    df = pd.read_excel("censo.xlsx", dtype={'Apoderado_ID': str})
    df.columns = df.columns.str.strip()
    
    # Limpieza extrema: eliminamos decimales .0 que a veces pone Excel y espacios
    df['Apoderado_ID'] = df['Apoderado_ID'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    
    df['id_unidad'] = df['Torre'].astype(str) + " " + df['Unidad'].astype(str)
    return df