# Guía de Pruebas: Servicio Independiente PersonaPlex

Para que tu arquitectura profesional funcione, el repositorio de **PersonaPlex** debe actuar como un servidor de audio que "escucha" y "responde" a través de Zenoh.

## 1. Preparación en el Repo de PersonaPlex (Moshi)

En tu repositorio de PersonaPlex, necesitas un script que haga de puente entre el modelo Moshi y Zenoh. Aquí tienes un ejemplo de cómo sería ese `zenoh_bridge.py`:

```python
import zenoh
import logging

# Configuración de tópicos (deben coincidir con OM1)
MIC_TOPIC = "pepper/audio/mic"
SPEAKER_TOPIC = "pepper/audio/speaker"

def main():
    session = zenoh.open()
    
    # 1. Escuchar el micrófono que viene de OM1
    def mic_callback(sample):
        audio_data = sample.payload.to_bytes()
        # --> AQUÍ: Envía audio_data a tu modelo Moshi
        # moshi_model.process(audio_data)
        print("Recibiendo audio de Pepper...")

    session.declare_subscriber(MIC_TOPIC, mic_callback)

    # 2. Enviar la respuesta de Moshi a OM1
    publisher = session.declare_publisher(SPEAKER_TOPIC)
    
    # Ejemplo de envío (esto lo llamaría tu modelo Moshi al generar audio)
    # def on_moshi_audio(output_chunk):
    #     publisher.put(output_chunk)

    print("PersonaPlex Bridge listo. Esperando a OM1...")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        session.close()

if __name__ == "__main__":
    main()
```

---

## 2. Cómo realizar la prueba (Demo)

Para probarlo todo junto sin necesidad de tener el robot físico:

### Terminal A: PersonaPlex (Tu otro repo)
Ejecutas el servidor de Moshi con el puente de Zenoh.
```bash
python zenoh_bridge.py
```

### Terminal B: OM1 (Este repo)
Ejecutas el agente de Pepper.
```bash
uv run src/run.py pepper
```

### Terminal C: Interacción (Simulador)
Usas el simulador o el script de interacción que creamos para enviar comandos.
```bash
uv run interactuar_pepper.py
```

---

## 3. Verificación de Comunicación Full Duplex

Para verificar que el sistema es "desacoplado" e independiente:

1.  **Observa el tráfico de Zenoh**: Puedes usar la herramienta `zenoh-get` o `zenoh-subscribe` para ver si hay paquetes fluyendo entre los tópicos `pepper/audio/mic` y `pepper/audio/speaker`.
2.  **Prueba de Interrupción**: Mientras PersonaPlex está enviando audio al tópico `speaker`, envía un mensaje de texto por `interactuar_pepper.py`. Deberías ver cómo el plugin de OM1 detecta el nuevo input y corta el audio actual.
3.  **Logs**: Verás en OM1 logs tipo: `PersonaPlex Mic Proxy initialized` y `PersonaPlex Speaker Proxy listening`.

> [!IMPORTANT]
> Al ser repositorios independientes, puedes actualizar las librerías de NVIDIA en PersonaPlex (que a veces son incompatibles con otras) sin afectar a las dependencias de OM1. Solo se "hablan" por el canal binario de Zenoh.
