# -*- coding: utf-8 -*-
# Importa los módulos necesarios de Flask y Python
import os
import sqlite3
import csv
import io
from datetime import datetime
from flask import Flask, request, g, redirect, url_for, Response, render_template

# --- Configuración de la aplicación y la base de datos ---
app = Flask(__name__)
# Define el nombre del archivo de la base de datos SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(basedir, 'respuestas_aec.db')

# Define la aplicación de Flask
app = Flask(__name__)

# --- Funciones para gestionar la base de datos ---

def get_db():
    # Conecta a la base de datos. Si no existe, la crea.
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    # Cierra la conexión a la base de datos al finalizar la solicitud.
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    # Inicializa la base de datos, creando la tabla de respuestas si no existe.
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS respuestas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                nombre TEXT,
                rol TEXT,
                comentario_introduccion TEXT,
                comentario_convivencia TEXT,
                comentario_derechos TEXT,
                comentario_obligaciones TEXT,
                comentario_sanciones TEXT,
                comentario_consejo TEXT,
                comentario_limites TEXT
            )
        ''')
        db.commit()

# --- Rutas de la aplicación ---

@app.route('/')
def home():
    # Renderiza la página principal con el formulario.
    # El HTML ahora se carga desde un archivo de plantilla.
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    # Recibe los datos del formulario POST
    nombre = request.form.get('nombre')
    rol = request.form.get('rol')
    comentarios = {key: request.form.get(key) for key in request.form if key not in ['nombre', 'rol']}

    # Guarda los datos en la base de datos
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO respuestas (fecha, nombre, rol, comentario_introduccion, comentario_convivencia, comentario_derechos, comentario_obligaciones, comentario_sanciones, comentario_consejo, comentario_limites)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        nombre,
        rol,
        comentarios.get('comentario_introduccion', ''),
        comentarios.get('comentario_convivencia', ''),
        comentarios.get('comentario_derechos', ''),
        comentarios.get('comentario_obligaciones', ''),
        comentarios.get('comentario_sanciones', ''),
        comentarios.get('comentario_consejo', ''),
        comentarios.get('comentario_limites', '')
    ))
    db.commit()
    return redirect(url_for('thank_you'))

@app.route('/thank-you')
def thank_you():
    # Página de agradecimiento simple.
    return """
    <div style='font-family: sans-serif; text-align: center; padding-top: 50px;'>
        <h1>¡Gracias por tu participación!</h1>
        <p>Tus respuestas han sido enviadas correctamente.</p>
        <a href='/'>Volver al formulario</a>
    </div>
    """

@app.route('/download')
def download_data():
    # Prepara los datos de la base de datos para la descarga en formato CSV
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM respuestas')
    data = cursor.fetchall()
    
    # Crea un archivo en memoria
    csv_output = io.StringIO()
    writer = csv.writer(csv_output)
    
    # Escribe los encabezados y los datos
    headers = [description[0] for description in cursor.description]
    writer.writerow(headers)
    writer.writerows(data)
    
    # Prepara la respuesta para la descarga del archivo
    response = Response(csv_output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment;filename=respuestas_aec.csv'
    return response

# Inicializa la base de datos antes de la primera solicitud.
if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(port=5001, debug=True)
