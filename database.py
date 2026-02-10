import sqlite3

def inicializar_db():
    conn = sqlite3.connect("asamblea.db")
    cursor = conn.cursor()
    # Tabla de votos (donde se guarda el resultado)
    cursor.execute('''CREATE TABLE IF NOT EXISTS votos 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, unidad TEXT, coeficiente REAL, decision TEXT)''')
    # Tabla de censo (donde están los dueños y poderes)
    cursor.execute('''CREATE TABLE IF NOT EXISTS censo 
                      (unidad TEXT PRIMARY KEY, coeficiente REAL, apoderado_id TEXT)''')
    conn.commit()
    conn.close()

def guardar_voto(unidad, coeficiente, decision):
    conn = sqlite3.connect("asamblea.db")
    cursor = conn.cursor()
    # Evitar que una misma unidad vote dos veces
    cursor.execute("SELECT id FROM votos WHERE unidad = ?", (unidad,))
    if cursor.fetchone():
        conn.close()
        return False
    
    cursor.execute("INSERT INTO votos (unidad, coeficiente, decision) VALUES (?, ? , ?)",
                   (unidad, coeficiente, decision))
    conn.commit()
    conn.close()
    return True

def obtener_totales():
    conn = sqlite3.connect("asamblea.db")
    cursor = conn.cursor()
    cursor.execute("SELECT decision, SUM(coeficiente) FROM votos GROUP BY decision")
    resultados = dict(cursor.fetchall())
    conn.close()
    return resultados

def borrar_todos_los_votos():
    conn = sqlite3.connect("asamblea.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM votos")
    conn.commit()
    conn.close()