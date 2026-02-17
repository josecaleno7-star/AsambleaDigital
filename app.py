import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt

# --- CONFIGURACIÓN DE LA APP ---
st.set_page_config(page_title="Asamblea Digital PH", page_icon="🗳️", layout="centered")

# Estilo CSS para que parezca una App nativa de celular
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 20px; height: 3em; background-color: #2e7d32; color: white; font-weight: bold; }
    .stTextInput>div>div>input { border-radius: 15px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS INTERNA ---
def conectar():
    return sqlite3.connect("asamblea.db", check_same_thread=False)

def inicializar_tablas():
    conn = conectar()
    conn.execute('''CREATE TABLE IF NOT EXISTS votos 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, unidad TEXT, coeficiente REAL, decision TEXT)''')
    conn.commit()
    conn.close()

inicializar_tablas()

# --- CARGA DE DATOS ---
@st.cache_data
def cargar_datos():
    try:
        # Forzamos la lectura de IDs como texto para que no falle el reconocimiento
        df = pd.read_excel("censo.xlsx", dtype={'Apoderado_ID': str, 'Torre': str, 'Unidad': str})
        df.columns = df.columns.str.strip()
        # Limpieza de cédulas: quitamos decimales y espacios
        df['Apoderado_ID'] = df['Apoderado_ID'].astype(str).str.split('.').str[0].str.strip()
        df['id_unidad'] = df['Torre'].astype(str) + " " + df['Unidad'].astype(str)
        return df
    except Exception as e:
        st.error(f"Error al cargar censo.xlsx: {e}")
        return None

censo_df = cargar_datos()

# --- INTERFAZ DE USUARIO ---
st.title("🗳️ Asamblea Digital")
st.write("Bienvenido. Ingrese su identificación para votar.")

if censo_df is not None:
    id_input = st.text_input("Cédula del Propietario o Apoderado", placeholder="Escriba su número aquí")

    if id_input:
        # Buscar coincidencias
        id_buscado = id_input.strip()
        mis_unidades = censo_df[censo_df['Apoderado_ID'] == id_buscado]
        
        if not mis_unidades.empty:
            total_coef = mis_unidades['Coeficiente'].sum()
            unidades_nombres = mis_unidades['id_unidad'].tolist()
            
            st.success(f"✅ Identificado correctamente")
            st.info(f"🏢 **Unidades:** {', '.join(unidades_nombres)}\n\n📊 **Coeficiente Total:** {total_coef:.4f}%")

            # Verificar si ya votaron
            conn = conectar()
            ya_votaron = pd.read_sql_query("SELECT unidad FROM votos", conn)['unidad'].tolist()
            conn.close()
            
            pueden_votar = [u for u in unidades_nombres if u not in ya_votaron]

            if pueden_votar:
                st.subheader("¿Cuál es su decisión?")
                decision = st.radio("Elija una opción:", ["Favor", "Contra"], horizontal=True)
                
                if st.button("REGISTRAR VOTO"):
                    conn = conectar()
                    for _, fila in mis_unidades.iterrows():
                        if fila['id_unidad'] in pueden_votar:
                            conn.execute("INSERT INTO votos (unidad, coeficiente, decision) VALUES (?, ?, ?)",
                                         (fila['id_unidad'], fila['Coeficiente'], decision))
                    conn.commit()
                    conn.close()
                    st.balloons()
                    st.success("¡Voto registrado con éxito!")
                    st.rerun()
            else:
                st.warning("⚠️ Usted ya ha ejercido su derecho al voto.")
        else:
            st.error("❌ El número de identificación no aparece en el censo.")

# --- RESULTADOS (MODO ADMINISTRADOR) ---
st.markdown("---")
with st.expander("📊 Ver Resultados (Solo Admin)"):
    clave = st.text_input("Clave de acceso", type="password")
    if clave == "1234": # Puedes cambiar esta clave
        conn = conectar()
        df_res = pd.read_sql_query("SELECT decision, SUM(coeficiente) as total FROM votos GROUP BY decision", conn)
        conn.close()
        
        if not df_res.empty:
            fig, ax = plt.subplots()
            ax.pie(df_res['total'], labels=df_res['decision'], autopct='%1.1f%%', colors=['#4CAF50', '#F44336'])
            st.pyplot(fig)
            st.write(df_res)
        else:
            st.write("Esperando los primeros votos...")