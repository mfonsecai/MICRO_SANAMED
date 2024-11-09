import re
from datetime import datetime,date, timedelta
from flask import Flask, render_template, request, session, redirect, url_for, jsonify,flash
from flask_mysqldb import MySQL
from functools import wraps

import random

app = Flask(__name__)

# Configuración MySQL
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "sanamed2"
mysql = MySQL(app)

def professional_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or session.get('rol') != 'profesional':
            return redirect('http://localhost:5001/login')
        return f(*args, **kwargs)
    return decorated_function
def obtener_id_usuario_actual():
    if 'id_usuario' in session:
        return session['id_usuario']
    else:
        return None

@app.route('/profesional_home')
@professional_required
def profesional_home():
    if 'logged_in' in session and session['logged_in']:
        # Aquí renderizas el home del usuario
        return render_template('profesional_home.html')
    else:
        return redirect(url_for('index'))




@app.route('/pacientes')
@professional_required
def pacientes():
    if 'logged_in' in session and session['logged_in']:
        id_profesional = obtener_id_usuario_actual()
       
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT  u.nombre,  u.numero_documento, u.celular, u.correo
            FROM Usuarios u
            JOIN profesionales_usuarios pu ON u.id_usuario = pu.id_usuario
            WHERE pu.id_profesional = %s
        """, (id_profesional,))
       
        pacientes = cur.fetchall()
        cur.close()
       
        return render_template('lista_pacientes.html', pacientes=pacientes)
    else:
        return redirect(url_for('index'))


@app.route('/citas_asignadas')
def citas_asignadas():
    if 'logged_in' in session and session['logged_in']:
        id_profesional = obtener_id_usuario_actual()
       
        cur = mysql.connection.cursor()
        
        # Actualiza el estado de las citas en tiempo real
        cur.execute("""
            UPDATE Consultas 
            SET estado = 'tomada' 
            WHERE fecha_consulta < CURDATE() AND estado = 'pendiente';
        """)
        
        # Ahora selecciona las citas
        cur.execute("""
            SELECT c.id_consulta, u.nombre AS nombre_paciente, u.numero_documento, u.correo AS correo_paciente, 
                   c.fecha_consulta, c.hora_consulta, c.motivo, 
                   c.estado
            FROM Consultas c
            JOIN Usuarios u ON c.id_usuario = u.id_usuario
            WHERE c.id_profesional = %s
        """, (id_profesional,))
       
        citas = cur.fetchall()
        cur.close()
        
        return render_template('citas_asignadas.html', citas=citas)
    else:
        return redirect(url_for('index'))


class Consulta:
    def __init__(self, id_consulta, numero_documento, fecha_consulta, hora_consulta, motivo, diagnostico, tratamiento):
        self.id_consulta = id_consulta
        self.numero_documento = numero_documento
        self.fecha_consulta = fecha_consulta
        self.hora_consulta = hora_consulta
        self.motivo = motivo
        self.diagnostico = diagnostico
        self.tratamiento = tratamiento


@app.route('/diagnosticos_tratamientos', methods=['GET', 'POST'])
@professional_required
def diagnosticos_tratamientos():
    if 'logged_in' in session and session['logged_in']:
        id_profesional = obtener_id_usuario_actual()  # Obtener el ID del profesional logueado


        cur = mysql.connection.cursor()
        cur.execute("""
    SELECT DISTINCT c.id_consulta, u.numero_documento, c.fecha_consulta, c.hora_consulta, c.motivo, c.diagnostico, c.tratamiento
    FROM Consultas c
    JOIN Usuarios u ON c.id_usuario = u.id_usuario
    JOIN Profesionales_Usuarios pu ON c.id_profesional = pu.id_profesional
    WHERE c.fecha_consulta < %s AND pu.id_profesional = %s
""", (datetime.now(), id_profesional))


        consultas = cur.fetchall()
        cur.close()


        consultas_obj = [Consulta(*consulta) for consulta in consultas]


        if request.method == 'POST':
            flash('Actualizado correctamente', 'success')


        return render_template('diagnosticos_tratamientos.html', consultas=consultas_obj)
    else:
        return redirect(url_for('index'))
@app.route('/editar_diagnostico_tratamiento/<int:id_consulta>', methods=['POST'])
@professional_required
def editar_diagnostico_tratamiento(id_consulta):
    diagnostico = request.form['diagnostico']
    tratamiento = request.form['tratamiento']
   
    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE Consultas
        SET diagnostico = %s, tratamiento = %s
        WHERE id_consulta = %s
    """, (diagnostico, tratamiento, id_consulta))
    mysql.connection.commit()
    cur.close()
   
    flash('El diagnóstico y tratamiento se han actualizado correctamente.')
    return redirect(url_for('diagnosticos_tratamientos'))


@app.route('/configuracion')
@professional_required

def configuracion():
    return render_template('configuracion.html')
@app.route('/editar_perfil', methods=['GET', 'POST'])
@professional_required
def editar_perfil():
    if 'logged_in' in session and session['logged_in']:
        id_usuario = obtener_id_usuario_actual()
        cur = mysql.connection.cursor()


        if request.method == 'POST':
            nombre = request.form['nombre']
            numero_documento = request.form['numero_documento']
            celular = request.form['celular']
            correo = request.form['correo']


            cur.execute("""
                UPDATE Usuarios
                SET nombre = %s, numero_documento = %s, celular = %s, correo = %s
                WHERE id_usuario = %s
            """, (nombre, numero_documento, celular, correo, id_usuario))
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('configuracion'))


        cur.execute("SELECT nombre, numero_documento, celular, correo FROM Usuarios WHERE id_usuario = %s", (id_usuario,))
        usuario = cur.fetchone()
        cur.close()
        return render_template('editar_perfil.html', usuario=usuario)
    else:
        return redirect(url_for('index'))


@app.route('/sobre_nosotros')
@professional_required
def sobre_nosotros():
    return render_template('sobre_nosotros.html')


@app.route('/preguntas_frecuentes')
@professional_required
def preguntas_frecuentes():
    return render_template('preguntas_frecuentes.html')

@app.after_request
def add_header(response):
    # Prevenir cache en todas las respuestas
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

if __name__ == '__main__':
    app.secret_key = "sanamed"
    app.run(debug=True, host="0.0.0.0", port=5004)