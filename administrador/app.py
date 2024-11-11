import re
from datetime import datetime,date, timedelta
from flask import Flask, render_template, request, session, redirect, url_for, jsonify,flash
from flask_mysqldb import MySQL
from functools import wraps
from flask_cors import CORS
import random

app = Flask(__name__)

# Configuración MySQL
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "sanamed2"
mysql = MySQL(app)

CORS(app, origins=["http://localhost:5000", "http://localhost:5001", "http://localhost:5002", "http://localhost:5003"])

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or session.get('rol') != 'admin':
            return redirect('http://localhost:5000/login')
        return f(*args, **kwargs)
    return decorated_function

def obtener_id_usuario_actual():
    if 'id_usuario' in session:
        return session['id_usuario']
    else:
        return None
    
def validate_password(password):
    if len(password) < 8:
        return False
    if not re.search("[A-Z]", password):
        return False
    if not re.search("[!@#$%^&*()_+=\[{\]};:<>|./?,-]", password):
        return False
    return True


@app.route('/admin_home')
@admin_required
def admin_home():
    if 'logged_in' in session and session['logged_in']:
        # Aquí renderizas el home del usuario
        return render_template('admin_home.html')
    else:
        return redirect(url_for('index'))


@app.route('/profesionales')
@admin_required
def listar_profesionales():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_profesional, nombre, especialidad FROM Profesionales")
    profesionales = cur.fetchall()
    cur.close()
    return render_template('lista_profesionales.html', profesionales=profesionales)


@app.route('/agregar_profesional', methods=["GET", "POST"])
@admin_required
def agregar_profesional():
    if request.method == "POST":
        nombre = request.form['nombre']
        especialidad = request.form['especialidad']
        correo = request.form['correo']
        contrasena = request.form['contrasena']


        # Validación de la contraseña
        if not validate_password(contrasena):
            error = "La contraseña debe tener al menos 8 caracteres, incluyendo letras, números y caracteres especiales."
            return render_template('agregar_profesional.html', error=error)


        cur = mysql.connection.cursor()
        try:
            cur.execute("INSERT INTO Profesionales (nombre, especialidad, correo, contrasena) VALUES (%s, %s, %s, %s)",
                        (nombre, especialidad, correo, contrasena))
            mysql.connection.commit()
        except Exception as e:
            mysql.connection.rollback()
            error = "Error al agregar profesional: " + str(e)
            return render_template('agregar_profesional.html', error=error)
        finally:
            cur.close()
        return redirect(url_for('listar_profesionales'))
    return render_template('agregar_profesional.html')


@app.route('/eliminar_profesional/<int:id>', methods=["POST"])
@admin_required
def eliminar_profesional(id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM Profesionales WHERE id_profesional=%s", (id,))
        mysql.connection.commit()
        flash("Profesional eliminado correctamente", "success")
    except Exception as e:
        mysql.connection.rollback()
        error = "Error al eliminar profesional "
        flash(error, "error")
    finally:
        cur.close()


    return redirect(url_for('listar_profesionales'))


@app.route('/usuarios')
@admin_required
def listar_usuarios():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_usuario, numero_documento, correo FROM Usuarios")
    usuarios = cur.fetchall()  # Cambio de nombre de la variable para reflejar que son usuarios, no profesionales
    cur.close()
    return render_template('lista_usuarios.html', usuarios=usuarios)  # Cambio de la plantilla a lista_usuarios.html
@app.route('/eliminar_usuario/<int:id>', methods=["POST"])
@admin_required
def eliminar_usuario(id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM Usuarios WHERE id_usuario=%s", (id,))
        mysql.connection.commit()
        flash('Usuario eliminado correctamente', 'success')  # Mensaje de éxito
    except Exception as e:
        mysql.connection.rollback()
        error = "Error al eliminar usuario "
        flash(error, 'error')  # Mensaje de error
    finally:
        cur.close()
    return redirect(url_for('listar_usuarios'))

@app.route('/citas_agendadas')
@admin_required
def listar_citas():
    cur = mysql.connection.cursor()
   
    query = """
    SELECT
        u.numero_documento,
        p.nombre AS nombre_profesional,
        c.fecha_consulta,
        c.hora_consulta,
        c.motivo,
        c.id_consulta
    FROM
        Consultas c
    JOIN
        Usuarios u ON c.id_usuario = u.id_usuario
    LEFT JOIN
        Profesionales p ON c.id_profesional = p.id_profesional;
    """
   
    cur.execute(query)
    citas = cur.fetchall()
    cur.close()
   
    return render_template('lista_consultas.html', citas=citas)
@app.route('/eliminar_cita/<int:id>', methods=['POST'])
@admin_required
def eliminar_cita(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM Consultas WHERE id_consulta = %s", (id,))
    mysql.connection.commit()
    cur.close()
   
    # Emitir un mensaje flash después de eliminar la cita con éxito
    flash('La cita ha sido eliminada correctamente.', 'success')
   
    return redirect(url_for('listar_citas'))


if __name__ == '__main__':
    app.secret_key = "sanamed"
    app.run(debug=True, host="0.0.0.0", port=5001)