# hackatec

# AgroGest – Control Inteligente por Gestos

AgroGest es un prototipo de sistema de agricultura inteligente que permite controlar un dashboard mediante gestos de la mano en tiempo real, utilizando visión por computadora e inteligencia artificial.

El objetivo del proyecto es crear una forma sin contacto, accesible y eficiente de interactuar con sistemas agrícolas, como el control de riego o monitoreo de condiciones ambientales, ideal para invernaderos o entornos rurales.

## Cómo funciona

El sistema utiliza la cámara web para detectar la mano del usuario y reconocer gestos específicos.

1. La cámara captura el movimiento de la mano en tiempo real.
2. MediaPipe detecta la posición de la mano y los dedos.
3. El sistema interpreta los gestos definidos.
4. Cada gesto ejecuta una acción en el dashboard.

## Gestos disponibles

- 👍 Pulgar arriba → Activar sistema
- ✋ Mano abierta → Detener sistema
- ✌️ Dos dedos → Cambiar vista
- 👌 Gesto de pinza → Confirmar acción

## Tecnologías utilizadas

- Python
- MediaPipe (visión por computadora)
- OpenCV (procesamiento de video)
- Streamlit (dashboard web)
- Scikit-learn (opcional para predicciones)

## Objetivo

Desarrollar una solución basada en inteligencia artificial que permita mejorar la accesibilidad en sistemas agrícolas, reducir el contacto físico con dispositivos y demostrar el uso de IA aplicada a problemas reales.

## Nota

Este proyecto es un prototipo educativo desarrollado para hackatón. No es un sistema comercial.
git
