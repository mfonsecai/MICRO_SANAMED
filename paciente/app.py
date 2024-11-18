import os
import re
from datetime import datetime, timedelta
from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.secret_key = "sanamed"

# Configuración SQLAlchemy (Usar MySQL con SQLAlchemy)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "mysql+pymysql://root:@db:3306/sanamed2")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Inicializar SQLAlchemy
db = SQLAlchemy(app)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect('http://localhost:5001/login')
        return f(*args, **kwargs)
    return decorated_function

def obtener_id_usuario_actual():
    if 'id_usuario' in session:
        return session['id_usuario']
    else:
        return None
    
def obtener_profesionales_disponibles():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_profesional, nombre, especialidad FROM Profesionales")
    profesionales = cur.fetchall()
    cur.close()
    return profesionales
def obtener_emociones_por_fecha(fecha):
    cur = mysql.connection.cursor()
    query = "SELECT emocion, HOUR(fecha_emocion), MINUTE(fecha_emocion) FROM Emociones WHERE DATE(fecha_emocion) = %s"
    cur.execute(query, (fecha,))
    emociones = []
    horas = []
    for row in cur.fetchall():
        emociones.append(row[0])
        hora = str(row[1]).zfill(2)
        minuto = str(row[2]).zfill(2)
        hora_formateada = f"{hora}:{minuto}"
        horas.append(hora_formateada)
    cur.close()
    return emociones, horas
def obtener_consultas_por_fecha(fecha):
    cur = mysql.connection.cursor()
    query = "SELECT id_usuario, id_profesional, fecha_consulta, hora_consulta, motivo FROM Consultas WHERE DATE(fecha_consulta) = %s"
    cur.execute(query, (fecha,))
    consultas = cur.fetchall()
    cur.close()
    return consultas

def obtener_especialidad_profesional(id_profesional):
    cur = mysql.connection.cursor()
    cur.execute("SELECT especialidad FROM Profesionales WHERE id_profesional = %s", (id_profesional,))
    especialidad_profesional = cur.fetchone()[0]
    cur.close()
    return especialidad_profesional


def obtener_nombre_profesional(id_profesional):
    cur = mysql.connection.cursor()
    cur.execute("SELECT nombre FROM Profesionales WHERE id_profesional = %s", (id_profesional,))
    nombre_profesional = cur.fetchone()[0]
    cur.close()
    return nombre_profesional
def obtener_conteo_emociones_por_fecha(fecha):
    cur = mysql.connection.cursor()
    query = "SELECT emocion FROM Emociones WHERE DATE(fecha_emocion) = %s"
    cur.execute(query, (fecha,))
    emociones = [row[0] for row in cur.fetchall()]
    cur.close()
    
    # Contar cada emoción y devolver en formato JSON serializable
    conteo_emociones = dict(Counter(emociones))
    return conteo_emociones


@app.route('/user_home')
@login_required
def user_home():
    if 'logged_in' in session and session['logged_in']:
        # Aquí renderizas el home del usuario
        return render_template('user_home.html')
    else:
        return redirect(url_for('index'))

@app.route('/registro_emocion', methods=['POST'])
@login_required
def registro_emocion():
    if 'logged_in' in session and session['logged_in']:
        if request.method == 'POST':
            # Obtener la emoción seleccionada por el usuario
            emocion = request.form['emocion']


            # Obtener el ID del usuario actualmente logueado
            print("Contenido de la sesión:", session)  # Agregar esta impresión
            id_usuario = obtener_id_usuario_actual()


            # Obtener la fecha y hora actual
            fecha_emocion = datetime.now()


            # Insertar la emoción en la base de datos
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO Emociones (id_usuario, fecha_emocion, emocion) VALUES (%s, %s, %s)",
                        (id_usuario, fecha_emocion, emocion))
            mysql.connection.commit()
            cur.close()


            # Redirigir al usuario de nuevo a la página de inicio
            return redirect(url_for('user_home'))
    else:
        return redirect(url_for('index'))
    


@app.route('/agendar_cita', methods=["GET", "POST"])
@login_required
def agendar_cita():
    if 'logged_in' in session and session['logged_in']:
        if request.method == "POST":
            fecha = request.form['fecha']
            hora = request.form['hora']
            motivo = request.form['motivo']
            id_usuario = session['id_usuario']


            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM Consultas WHERE fecha_consulta = %s AND hora_consulta = %s", (fecha, hora))
            cita_existente = cur.fetchone()
            cur.close()


            # Validar que la fecha no sea anterior a la fecha actual
            fecha_actual = date.today()
            fecha_seleccionada = datetime.strptime(fecha, '%Y-%m-%d').date()


            if fecha_seleccionada < fecha_actual:
                error = "No puedes programar una cita en una fecha anterior a la fecha actual."
                return render_template('agendar_cita.html', error=error, profesionales=obtener_profesionales_disponibles())


            if cita_existente:
                error = "Ya hay una cita programada para esa fecha y hora."
                return render_template('agendar_cita.html', error=error, profesionales=obtener_profesionales_disponibles())
            else:
                # Convertir la hora AM/PM a un formato de 24 horas
                hora_seleccionada = datetime.strptime(hora, '%I:%M %p').strftime('%H:%M')


                hora_inicio = datetime.strptime('08:00', '%H:%M').time()
                hora_fin = datetime.strptime('17:00', '%H:%M').time()
               
                if hora_seleccionada < hora_inicio.strftime('%H:%M') or hora_seleccionada > hora_fin.strftime('%H:%M'):
                    error = "La hora seleccionada está fuera del rango permitido (8:00 - 17:00)."
                    return render_template('agendar_cita.html', error=error, profesionales=obtener_profesionales_disponibles())


                id_profesional = request.form['profesional']


                cur = mysql.connection.cursor()
                try:
                    cur.execute("INSERT INTO Consultas (id_usuario, id_profesional, fecha_consulta, hora_consulta, motivo) VALUES (%s, %s, %s, %s, %s)",
                                (id_usuario, id_profesional, fecha, hora_seleccionada, motivo))
                    mysql.connection.commit()


                    cur.execute("INSERT INTO Profesionales_Usuarios (id_profesional, id_usuario) VALUES (%s, %s)",
                                (id_profesional, id_usuario))
                    mysql.connection.commit()
                except Exception as e:
                    mysql.connection.rollback()
                    error = "Error al programar la cita: " + str(e)
                    return render_template('agendar_cita.html', error=error, profesionales=obtener_profesionales_disponibles())
                finally:
                    cur.close()
                # Agregar el mensaje de éxito
                success_message = "Su cita se ha registrado con éxito."
                return render_template('agendar_cita.html', success=success_message, profesionales=obtener_profesionales_disponibles())
    else:
        return redirect(url_for('index'))


    return render_template('agendar_cita.html', profesionales=obtener_profesionales_disponibles())

@app.route('/calendario')
@login_required
def mostrar_calendario():
    # Aquí debes implementar la lógica para mostrar el calendario
    return render_template('calendario.html')

@app.route('/seleccionar_dia', methods=['POST'])
@login_required
def seleccionar_dia():
    if request.method == 'POST':
        fecha_seleccionada = request.form['fecha']
        emociones, horas = obtener_emociones_por_fecha(fecha_seleccionada)
        if not emociones:
            mensaje = "No hay emociones registradas para este día."
            return render_template('calendario.html', mensaje=mensaje)
        return render_template('emociones.html', fecha_seleccionada=fecha_seleccionada, emociones_horas=zip(emociones, horas))
    
@app.route('/ver_grafica/<fecha>')
@login_required
def ver_grafica(fecha):
    conteo_emociones = obtener_conteo_emociones_por_fecha(fecha)
    
    if not conteo_emociones:
        mensaje = "No hay emociones registradas para este día."
        return render_template('calendario.html', mensaje=mensaje)
    
    # Extraer etiquetas (emociones) y valores (conteo de cada emoción)
    emociones = list(conteo_emociones.keys())
    cantidades = list(conteo_emociones.values())
    
    return render_template(
        'grafica_emociones.html', 
        fecha_seleccionada=fecha, 
        emociones=emociones, 
        cantidades=cantidades
    )

@app.route('/consultas_dia', methods=["GET", 'POST'])
@login_required
def consultas_dia():
    if request.method == 'POST':
        fecha_seleccionada = request.form['fecha']
        consultas = obtener_consultas_por_fecha(fecha_seleccionada)
        if not consultas:
            mensaje = "No hay citas registradas para este día."
            return render_template('calendario.html', mensaje=mensaje)
        return render_template('consultas.html', fecha_seleccionada=fecha_seleccionada, consultas=consultas, obtener_nombre_profesional=obtener_nombre_profesional, obtener_especialidad_profesional=obtener_especialidad_profesional)


juegos = [
    {
        "id": 1,
        "nombre": "Juego de Meditación",
        "descripcion": "Un juego que te guía a través de una serie de ejercicios de meditación.",
        "dificultad": "Fácil",
        "duracion": "10 minutos"
    },
    {
        "id": 2,
        "nombre": "Cuestionario de Autoevaluación",
        "descripcion": "Evalúa tu estado emocional y mental con este cuestionario.",
        "dificultad": "Moderada",
        "duracion": "5 minutos"
    },
    {
        "id": 3,
        "nombre": "Desafío de Estrategia",
        "descripcion": "Desarrolla habilidades de pensamiento crítico y resolución de problemas.",
        "dificultad": "Difícil",
        "duracion": "15 minutos"
    },
    {
        "id": 4,
        "nombre": "Juego de Respiración Profunda",
        "descripcion": "Aprende técnicas de respiración para reducir la ansiedad.",
        "dificultad": "Fácil",
        "duracion": "5 minutos"
    },
    {
        "id": 5,
        "nombre": "Jardín de Gratitud",
        "descripcion": "Expresa y comparte cosas por las que estás agradecido.",
        "dificultad": "Fácil",
        "duracion": "Sin límite"
    }
]

@app.route('/games')
@login_required
def games():
    return render_template('games.html')

@app.route('/api/juegos', methods=['GET'])
def obtener_juegos():
    return jsonify({"juegos": juegos}), 200


@app.route('/configuracion')
@login_required

def configuracion():
    return render_template('configuracion.html')
@app.route('/editar_perfil', methods=['GET', 'POST'])
@login_required
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
@login_required
def sobre_nosotros():
    return render_template('sobre_nosotros.html')


@app.route('/preguntas_frecuentes')
@login_required
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
    app.run(debug=True, host="0.0.0.0", port=5000)