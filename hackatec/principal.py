import cv2
import numpy as np
import urllib.request
import json
from flask import Flask, render_template, Response, jsonify

app = Flask(__name__)
camara = cv2.VideoCapture(0)

estado_riego = "DESACTIVADO"
gesto_actual = "Ninguno"

# --- NUEVA FUNCIÓN: OBTENER CLIMA REAL DE TEHUACÁN ---
def obtener_clima_tehuacan():
    try:
        # Coordenadas de Tehuacán, Puebla. Pedimos temperatura actual y probabilidad de lluvia por hora
        url = "https://api.open-meteo.com/v1/forecast?latitude=18.4631&longitude=-97.3927&current=temperature_2m&hourly=precipitation_probability&forecast_days=1"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'AgroGestApp'})
        with urllib.request.urlopen(req) as response:
            datos = json.loads(response.read().decode())
            
            temp_actual = datos["current"]["temperature_2m"]
            # Tomamos la probabilidad de lluvia de la hora actual
            prob_lluvia_actual = datos["hourly"]["precipitation_probability"][0] 
            
            return temp_actual, prob_lluvia_actual
    except Exception as e:
        print(f"Error al consultar el clima: {e}")
        # Valores de respaldo por si falla el internet o la API
        return 24.5, 10 

def procesar_y_transmitir_video():
    global estado_riego, gesto_actual
    while True:
        ret, frame = camara.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (640, 480))
        
        cv2.rectangle(frame, (380, 50), (580, 300), (255, 0, 0), 2)
        roi = frame[50:300, 380:580]
        
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        bajo_piel = np.array([0, 20, 70], dtype=np.uint8)
        alto_piel = np.array([20, 255, 255], dtype=np.uint8)
        mascara = cv2.inRange(hsv, bajo_piel, alto_piel)
        
        kernel = np.ones((5, 5), np.uint8)
        mascara = cv2.dilate(mascara, kernel, iterations=2)
        mascara = cv2.GaussianBlur(mascara, (5, 5), 100)
        
        contornos, _ = cv2.findContours(mascara, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        texto_gesto = "Mano no detectada"
        gesto_actual = "Ninguno"
        color_texto = (241, 196, 15)
        
        if len(contornos) > 0:
            mano_contorno = max(contornos, key=cv2.contourArea)
            if cv2.contourArea(mano_contorno) > 2000:
                cv2.drawContours(roi, [mano_contorno], -1, (0, 255, 0), 2)
                envoltura = cv2.convexHull(mano_contorno, returnPoints=False)
                
                if len(envoltura) > 3:
                    defectos = cv2.convexityDefects(mano_contorno, envoltura)
                    valles_validos = 0
                    
                    if defectos is not None:
                        for i in range(defectos.shape[0]):
                            s, e, f, d = defectos[i, 0]
                            inicio = tuple(mano_contorno[s][0])
                            fin = tuple(mano_contorno[e][0])
                            faro = tuple(mano_contorno[f][0])
                            
                            a = np.sqrt((fin[0] - inicio[0])**2 + (fin[1] - inicio[1])**2)
                            b = np.sqrt((faro[0] - inicio[0])**2 + (faro[1] - inicio[1])**2)
                            c = np.sqrt((fin[0] - faro[0])**2 + (fin[1] - faro[1])**2)
                            angulo = np.arccos((b**2 + c**2 - a**2) / (2 * b * c)) * 57
                            
                            if angulo <= 90:
                                valles_validos += 1
                                cv2.circle(roi, faro, 5, [0, 0, 255], -1)

                        if valles_validos == 0:
                            texto_gesto = "PUNO CERRADO"
                            gesto_actual = "PUNO"
                            estado_riego = "DESACTIVADO"
                            color_texto = (60, 76, 231)
                        elif valles_validos == 1:
                            texto_gesto = "DOS DEDOS"
                            gesto_actual = "DOS_DEDOS"
                            color_texto = (182, 89, 155)
                        elif valles_validos == 2:
                            texto_gesto = "TRES DEDOS"
                            gesto_actual = "TRES_DEDOS"
                            color_texto = (34, 126, 230)
                        elif valles_validos >= 3:
                            texto_gesto = "MANO ABIERTA"
                            gesto_actual = "MANO_ABIERTA"
                            estado_riego = "ACTIVO"
                            color_texto = (113, 204, 46)

        cv2.putText(frame, f"Gesto: {texto_gesto}", (30, 410), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_texto, 2, cv2.LINE_AA)
        cv2.putText(frame, f"Riego: {estado_riego}", (30, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(procesar_y_transmitir_video(), mimetype='multipart/x-mixed-replace; boundary=frame')

# --- RUTA MODIFICADA: AHORA INCLUYE LOS DATOS DEL CLIMA ---
@app.route('/estado')
def obtener_estado():
    global estado_riego, gesto_actual
    t_real, p_lluvia = obtener_clima_tehuacan()
    return jsonify({
        "riego": estado_riego,
        "gesto": gesto_actual,
        "temperatura": t_real,
        "lluvia": p_lluvia
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)