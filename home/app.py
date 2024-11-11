import re
from datetime import datetime, timedelta
from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_mysqldb import MySQL
from functools import wraps
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.secret_key = "sanamed"

# Configuración MySQL
app.config["MYSQL_HOST"] = "db"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "sanamed2"
mysql = MySQL(app)

def obtener_id_usuario_actual():
    if 'id_usuario' in session:
        return session['id_usuario']
    else:
        return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Por favor inicie sesión para acceder a esta página', 'error')
            return redirect(url_for('index'))
        
        # Verificar si la sesión ha expirado
        if 'last_activity' in session:
            last_activity = datetime.fromisoformat(session['last_activity'])
            if datetime.now() - last_activity > timedelta(minutes=30):  # 30 minutos de timeout
                session.clear()
                flash('Su sesión ha expirado. Por favor inicie sesión nuevamente', 'error')
                return redirect(url_for('index'))
        
        # Actualizar timestamp de última actividad
        session['last_activity'] = datetime.now().isoformat()
        return f(*args, **kwargs)
    return decorated_function

def validate_password(password):
    if len(password) < 8:
        return False
    if not re.search("[A-Z]", password):
        return False
    if not re.search("[!@#$%^&*()_+=\[{\]};:<>|./?,-]", password):
        return False
    return True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=["GET", 'POST'])
def login():
    if request.method == "POST" and "correo" in request.form and "contrasena" in request.form:
        username = request.form['correo']
        password = request.form['contrasena']
        rol = request.form['rol']
       
        cur = mysql.connection.cursor()
        
        # Buscar en la tabla de usuarios
        cur.execute("SELECT id_usuario FROM Usuarios WHERE correo = %s AND contrasena = %s AND tipo_perfil = %s", (username, password, rol))
        user_data = cur.fetchone()
       
        # Si no se encuentra en la tabla de usuarios, buscar en la tabla de profesionales
        if not user_data and rol == "profesional":
            cur.execute("SELECT id_profesional FROM Profesionales WHERE correo = %s AND contrasena = %s", (username, password))
            user_data = cur.fetchone()
       
        # Si aún no se encuentra, buscar en la tabla de administradores
        if not user_data and rol == "admin":
            cur.execute("SELECT id_administrador FROM Administradores WHERE correo = %s AND contrasena = %s", (username, password))
            user_data = cur.fetchone()


        cur.close()

        if user_data:
            session['logged_in'] = True
            session['id_usuario'] = user_data[0]
            session['last_activity'] = datetime.now().isoformat()  # Agregar timestamp
            
            if rol == 'usuario':
                return redirect("http://localhost:5002/user_home")  # Cambiar URL a la del microservicio usuario
            elif rol == 'profesional':
                return redirect("http://localhost:5003/profesional_home")  # Cambiar URL a la del microservicio profesional
            elif rol == 'admin':
                return redirect("http://localhost:5001/admin_home")  # Cambiar URL a la del microservicio administrador
        else:
            flash("Credenciales incorrectas", "error")
            return render_template('index.html')

    return render_template('index.html')

@app.route('/signup', methods=["GET", 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        tipo_documento = request.form['tipo_documento']
        numero_documento = request.form['numero_documento']
        celular = request.form['celular']
        correo = request.form['correo']
        contrasena = request.form['contrasena']

        if not validate_password(contrasena):
            flash("La contraseña debe tener al menos 8 caracteres, una mayúscula y un carácter especial.", "error")
            return render_template('register.html')

        cur = mysql.connection.cursor()
        cur.execute("SELECT id_usuario FROM Usuarios WHERE correo = %s", (correo,))
        existing_user = cur.fetchone()
        cur.close()

        if existing_user:
            flash("El correo electrónico ya está registrado. Por favor, utiliza otro correo electrónico", "error")
            return render_template('register.html')

        cur = mysql.connection.cursor()
        try:
            cur.execute(
                "INSERT INTO Usuarios (nombre, tipo_documento, numero_documento, celular, correo, contrasena) VALUES (%s, %s, %s, %s, %s, %s)",
                (nombre, tipo_documento, numero_documento, celular, correo, contrasena))
            mysql.connection.commit()
            flash("Registro exitoso. Inicia sesión con tus credenciales.", "success")
            return redirect(url_for('index'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Error: {e}", "error")
            return render_template('register.html')
        finally:
            cur.close()

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    response = redirect(url_for('index'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
