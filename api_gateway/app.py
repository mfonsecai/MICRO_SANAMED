from flask import Flask, request, Response, render_template
import requests
from flask_mysqldb import MySQL

app = Flask(__name__, template_folder="templates")
app.secret_key = "sanamed"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "sanamed2"
mysql = MySQL(app)

ROUTES = {
    # Rutas de autenticación
    'index': 'http://localhost:5000/index',
    'login': 'http://localhost:5001/login',
    'signup': 'http://localhost:5001/signup',
    'logout': 'http://localhost:5001/logout',
    
    # Rutas de pacientes
    'user_home': 'http://localhost:5002/user_home',
    'agendar_cita': 'http://localhost:5002/agendar_cita',
    'registro_emocion': 'http://localhost:5002/registro_emocion',
    'calendario': 'http://localhost:5002/calendario',
    'seleccionar_dia': 'http://localhost:5002/seleccionar_dia',
    'consultas_dia': 'http://localhost:5002/consultas_dia',
    'games': 'http://localhost:5002/games',
    'api/juegos': 'http://localhost:5002/api/juegos',
    'configuracion': 'http://localhost:5002/configuracion',
    'editar_perfil': 'http://localhost:5002/editar_perfil',
    'sobre_nosotros': 'http://localhost:5002/sobre_nosotros',
    'preguntas_frecuentes': 'http://localhost:5002/preguntas_frecuentes',

    
    # Rutas de administrador
    'admin_home': 'http://localhost:5003/admin_home',
    'profesionales': 'http://localhost:5003/profesionales',
    'agregar_profesional': 'http://localhost:5003/agregar_profesional',
    'eliminar_profesional': 'http://localhost:5003/eliminar_profesional',
    'usuarios': 'http://localhost:5003/usuarios',
    'eliminar_usuario': 'http://localhost:5003/eliminar_usuario',
    'citas_agendadas': 'http://localhost:5003/citas_agendadas',
    'eliminar_cita': 'http://localhost:5003/eliminar_cita',
    
    
    # Rutas de profesionales
    'professional_home': 'http://localhost:5004/professional_home',
    'diagnosticos_tratamientos': 'http://localhost:5004/diagnosticos_tratamientos',
    'pacientes': 'http://localhost:5004/pacientes' ,
    'citas_asignadas': 'http://localhost:5004/citas_asignadas',
    'editar_diagnosticos_tratamientos': 'http://localhost:5004/editar_diagnosticos_tratamientos',
    'configuracion': 'http://localhost:5004/configuracion',
    'editar_perfil': 'http://localhost:5004/editar_perfil',
    'sobre_nosotros': 'http://localhost:5004/sobre_nosotros',
    'preguntas_frecuentes': 'http://localhost:5004/preguntas_frecuentes',




}


@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(path):
    print(f"Solicitado path: {path}")
    url = ROUTES.get(path)
    if not url:
        print(f"Ruta no encontrada: {path}")
        return 'Not Found', 404
    
    print(f"Redirigiendo a: {url}")
    resp = requests.request(
        method=request.method,
        url=url,
        headers={key: value for key, value in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False
    )
    
    # Excluir headers que puedan causar problemas
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]
    
    # Crear la respuesta final con los headers del servicio
    response = Response(resp.content, resp.status_code, headers)
    return response

if __name__ == '__main__':
    app.run(port=5000, debug=True)