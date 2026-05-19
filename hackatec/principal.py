import cv2
import numpy as np
from flask import Flask, render_template, Response, jsonify

app = Flask(__name__)
camara = cv2.VideoCapture(0)

# Variable global para almacenar el estado del riego
estado_riego = "DESACTIVADO"

def procesar_y_transmitir_video():
    global estado_riego
    while True:
        ret, frame = camara.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (640, 480))
        
        # Cuadro azul de interacción
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
        color_texto = (241, 196, 15) # Amarillo por defecto
        
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

                        # --- CLASIFICACIÓN MODIFICADA ---
                        if valles_validos == 0:
                            texto_gesto = "PUNO CERRADO"
                            estado_riego = "DESACTIVADO" # Cambia estado a apagado
                            color_texto = (60, 76, 231)   # Rojo
                        elif valles_validos == 1:
                            texto_gesto = "DOS DEDOS"
                            color_texto = (182, 89, 155)  # Morado
                        elif valles_validos == 2:
                            texto_gesto = "TRES DEDOS"     # Cambio solicitado por el usuario
                            color_texto = (34, 126, 230)  # Naranja
                        elif valles_validos >= 3:
                            texto_gesto = "MANO ABIERTA"
                            estado_riego = "ACTIVO"      # Cambia estado a encendido
                            color_texto = (113, 204, 46)  # Verde

        # Dibujar estado actual en el video
        cv2.putText(frame, f"Gesto: {texto_gesto}", (30, 410), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_texto, 2, cv2.LINE_AA)
        cv2.putText(frame, f"Riego: {estado_riego}", (30, 450), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

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
    return Response(procesar_y_transmitir_video(), 
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# NUEVA RUTA: Envía el estado actual del riego en formato JSON a la página web
@app.route('/estado')
def obtener_estado():
    global estado_riego
    return jsonify({"riego": estado_riego})

if __name__ == '__main__':
    app.run(debug=True, port=5000)