from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Ruta base para archivos estáticos (CSS, imágenes)
app.static_folder = 'static'

data_file = 'data.json'

# Configuración SMTP
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = 'yquvivaelfutbol@gmail.com'
SMTP_PASSWORD = 'Yqueviva#001'

# Cargar datos iniciales o crear archivo
if not os.path.exists(data_file):
    with open(data_file, 'w') as f:
        json.dump({"jugadores": [], "partidos": []}, f)


# Leer datos
def cargar_datos():
    with open(data_file, 'r') as f:
        return json.load(f)


# Guardar datos
def guardar_datos(data):
    with open(data_file, 'w') as f:
        json.dump(data, f, indent=4)


# Enviar correo
def enviar_correo(destinatario, asunto, mensaje):
    try:
        msg = MIMEText(mensaje)
        msg['Subject'] = asunto
        msg['From'] = SMTP_USER
        msg['To'] = destinatario

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, destinatario, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Error al enviar correo: {e}")


@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        puesto = request.form['puesto']
        pierna = request.form['pierna']
        password = request.form['password']

        data = cargar_datos()

        if any(j['nombre'] == nombre for j in data['jugadores']):
            return "El nombre de usuario ya está registrado."

        data['jugadores'].append({"nombre": nombre, "email": email, "puesto": puesto, "pierna": pierna, "password": password, "historico_puntajes": []})
        guardar_datos(data)

        return redirect(url_for('login'))
    return render_template('registrar.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nombre = request.form['nombre']
        password = request.form['password']

        data = cargar_datos()
        jugador = next((j for j in data['jugadores'] if j['nombre'] == nombre and j['password'] == password), None)

        if jugador:
            session['usuario'] = nombre
            return redirect(url_for('index'))
        else:
            return "Usuario o contraseña incorrectos."

    return render_template('login.html')

@app.route('/login_admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        nombre = request.form['nombre']
        password = request.form['password']

        if nombre == 'admin' and password == 'admin123':
            session['usuario'] = 'admin'
            return redirect(url_for('index'))
        else:
            return "Credenciales de administrador incorrectas."

    return render_template('login_admin.html')


@app.route('/recuperar', methods=['GET', 'POST'])
def recuperar():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']

        data = cargar_datos()
        jugador = next((j for j in data['jugadores'] if j['nombre'] == nombre and j['email'] == email), None)

        if jugador:
            asunto = "Recuperación de contraseña"
            mensaje = f"Hola {nombre}, tu contraseña es: {jugador['password']}"
            enviar_correo(email, asunto, mensaje)
            return "Te hemos enviado tu contraseña al correo registrado."
        else:
            return "No se encontró coincidencia para el usuario y correo."

    return render_template('recuperar.html')


@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('index'))


@app.route('/crear_partido', methods=['GET', 'POST'])
def crear_partido():
    if request.method == 'POST':
        fecha = request.form['fecha']
        hora = request.form['hora']
        sede = request.form['sede']
        jugadores_por_equipo = int(request.form['jugadores_por_equipo'])

        if jugadores_por_equipo == 10:
            puestos = {"arquero": 2, "defensor": 8, "mediocampista": 6, "delantero": 4}
        else:
            puestos = {"arquero": 2, "defensor": 6, "mediocampista": 4, "delantero": 4}

        data = cargar_datos()

        jugadores_ordenados = sorted(
            data['jugadores'],
            key=lambda j: sum(j['historico_puntajes']) / len(j['historico_puntajes']) if j['historico_puntajes'] else 0,
            reverse=True
        )
        jugadores_disponibles = jugadores_ordenados[:jugadores_por_equipo * 2]

        equipo_a = []
        equipo_b = []

        for i, jugador in enumerate(jugadores_disponibles):
            if i % 2 == 0:
                equipo_a.append(jugador['nombre'])
            else:
                equipo_b.append(jugador['nombre'])

        partido = {
            "fecha": fecha,
            "hora": hora,
            "sede": sede,
            "jugadores_por_equipo": jugadores_por_equipo,
            "puestos": puestos,
            "inscriptos": [],
            "finalizado": False,
            "votaciones": [],
            "equipo_a": equipo_a,
            "equipo_b": equipo_b
        }
        data['partidos'].append(partido)
        guardar_datos(data)

        return redirect(url_for('partidos'))

    return render_template('crear_partido.html')

@app.route('/darse_baja/<int:partido_id>', methods=['POST'])
def darse_baja(partido_id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    data = cargar_datos()
    partido = data['partidos'][partido_id]
    nombre = session['usuario']

    inscripto = next((i for i in partido['inscriptos'] if i['nombre'] == nombre), None)
    if inscripto:
        puesto = inscripto['puesto']
        partido['inscriptos'].remove(inscripto)
        partido['puestos'][puesto] += 1
        guardar_datos(data)

    return redirect(url_for('partidos'))

@app.route('/partidos')
def partidos():
    data = cargar_datos()
    return render_template('partidos.html', partidos=data['partidos'])


@app.route('/equipos/<int:partido_id>')
def equipos(partido_id):
    data = cargar_datos()
    partido = data['partidos'][partido_id]
    jugadores_dict = {j['nombre']: j for j in data['jugadores']}
    return render_template('equipos.html', partido=partido, jugadores=jugadores_dict)


@app.route('/anotarse/<int:partido_id>', methods=['GET', 'POST'])
def anotarse(partido_id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    data = cargar_datos()
    partido = data['partidos'][partido_id]
    jugadores = data['jugadores']
    nombre = session['usuario']

    if request.method == 'POST':
        if any(inscripto['nombre'] == nombre for inscripto in partido['inscriptos']):
            return "Ya estás inscripto en este partido."

        jugador = next((j for j in jugadores if j['nombre'] == nombre), None)
        if jugador:
            puesto = jugador['puesto']
            email = jugador['email']
            if partido['puestos'].get(puesto, 0) > 0:
                partido['inscriptos'].append({"nombre": nombre, "puesto": puesto})
                partido['puestos'][puesto] -= 1
            else:
                for p in partido['puestos']:
                    if partido['puestos'][p] > 0:
                        partido['inscriptos'].append({"nombre": nombre, "puesto": p})
                        partido['puestos'][p] -= 1
                        break

            guardar_datos(data)

            mensaje = f"Hola {nombre}, te has inscrito correctamente al partido el {partido['fecha']} a las {partido['hora']} en {partido['sede']} como {puesto}."
            enviar_correo(email, "Confirmación de Inscripción", mensaje)

        return redirect(url_for('partidos'))

    return render_template('anotarse.html', partido=partido, jugadores=jugadores)


@app.route('/finalizar_partido/<int:partido_id>')
def finalizar_partido(partido_id):
    data = cargar_datos()
    partido = data['partidos'][partido_id]
    partido['finalizado'] = True

    for inscripto in partido['inscriptos']:
        jugador = next((j for j in data['jugadores'] if j['nombre'] == inscripto['nombre']), None)
        if jugador:
            encuesta_link = f"/encuesta/{partido_id}/{jugador['nombre']}"
            mensaje = f"Hola {jugador['nombre']}, por favor califica a tus compañeros en el siguiente enlace: {request.host_url.strip('/')}{encuesta_link}"
            enviar_correo(jugador['email'], "Encuesta de Evaluación", mensaje)

    guardar_datos(data)
    return redirect(url_for('partidos'))


@app.route('/encuesta/<int:partido_id>/<nombre>', methods=['GET', 'POST'])
def encuesta(partido_id, nombre):
    data = cargar_datos()
    partido = data['partidos'][partido_id]
    jugadores = [j['nombre'] for j in partido['inscriptos'] if j['nombre'] != nombre]

    if request.method == 'POST':
        votaciones = {}
        for jugador in jugadores:
            puntuacion = int(request.form[jugador])
            votaciones[jugador] = puntuacion

        partido['votaciones'].append({"votante": nombre, "votos": votaciones})
        guardar_datos(data)

        return "Gracias por completar la encuesta."

    return render_template('encuesta.html', jugadores=jugadores, partido_id=partido_id, nombre=nombre)


@app.route('/destacado/<int:partido_id>')
def destacado(partido_id):
    data = cargar_datos()
    partido = data['partidos'][partido_id]

    if not partido['votaciones']:
        return "Aún no hay votaciones registradas."

    puntajes = {}
    for votacion in partido['votaciones']:
        for jugador, puntaje in votacion['votos'].items():
            if jugador not in puntajes:
                puntajes[jugador] = 0
            puntajes[jugador] += puntaje

    destacado = max(puntajes, key=puntajes.get)

    for jugador in data['jugadores']:
        if jugador['nombre'] in puntajes:
            jugador['historico_puntajes'].append(puntajes[jugador['nombre']])

    guardar_datos(data)

    return f"El jugador destacado del partido del {partido['fecha']} es {destacado} con {puntajes[destacado]} puntos."


@app.route('/eliminar_partido/<int:partido_id>', methods=['POST'])
def eliminar_partido(partido_id):
    data = cargar_datos()
    if 0 <= partido_id < len(data['partidos']):
        data['partidos'].pop(partido_id)
        guardar_datos(data)
        return redirect(url_for('partidos'))
    return "Partido no encontrado."

if __name__ == '__main__':
    app.run(debug=True)
