# Guía de Desarrollo Pepper (Híbrido) - OM1

Esta guía consolida toda la arquitectura, configuración y estrategias para el desarrollo del robot Pepper utilizando el sistema híbrido PersonaPlex (Moshi) y OpenAI.

---

## 1. Arquitectura General de OM1

OM1 es un "sistema operativo" para agentes robóticos que separa el cerebro (LLM) de la percepción y la acción mediante plugins.

### Componentes Clave:
*   **Fuser (Percepción)**: Une todas las entradas (micrófono, cámara, sensores) en un prompt para el cerebro.
*   **Cortex (Cerebro)**: El LLM (OpenAI, Gemini, Local) que decide qué debe hacer el robot.
*   **Action Orchestrator**: Ejecuta las órdenes del cerebro a través de conectores (ROS2, Log, HTTP).
*   **Simulators (WebSim)**: Una interfaz web para visualizar el estado interno del robot en tiempo real.

---

## 2. Configuración de Pepper (`config/pepper.json5`)

La configuración define la "identidad" de Pepper. Algunos puntos clave:
*   **Simulación**: Pepper corre por defecto en el puerto `8005`.
*   **Prompt**: Define su personalidad como un robot humanoide amable.
*   **Governance**: Incluye reglas críticas de comportamiento (Leyes de Asimov).
*   **Hybrid Brain**: Configurado para usar el plugin `HybridPersonaPlexLLM` que orquestra la comunicación.

---

## 3. Estrategia Híbrida: PersonaPlex + OpenAI

Para eliminar el "silencio incómodo" en las demos y lograr una respuesta instantánea:

### Sistema 1 (Moshi / PersonaPlex) - Respuesta Rápida
*   Se encarga de la charla trivial (*chit-chat*), saludos y respuestas emocionales.
*   **Latencia**: < 200ms.
*   **Función**: "Hablar por hablar" mientras el Sistema 2 piensa.

### Sistema 2 (OpenAI / Deep Reasoning) - Razonamiento Profundo
*   Se activa cuando el usuario hace preguntas complejas, cálculos o requiere lógica.
*   **Inyección**: Sus resultados se envían a PersonaPlex para que los verbalice.

---

## 4. Guía de Integración Independiente (Desacoplada)

Para mantener los repositorios de OM1 y PersonaPlex/Moshi separados y sincronizables:

### En el Repositorio de PersonaPlex (Moshi):
Necesitas instalar `zenoh-python` y correr un puente:
```python
import zenoh
# Configuración de tópicos
MIC_TOPIC = "pepper/audio/mic"
SPEAKER_TOPIC = "pepper/audio/speaker"

# Aquí conectas tu modelo Moshi para que lea de MIC_TOPIC
# y publique audio en SPEAKER_TOPIC
```

### En el Repositorio de OM1 (Este):
Usa los plugins de proxy creados:
*   **Micro**: `src/inputs/plugins/personaplex_mic.py`
*   **Speaker**: `src/actions/speak/connector/personaplex_zenoh.py`
*   **Brain**: `src/llm/plugins/hybrid_personaplex.py`

---

## 5. Resumen de Implementación y Flujo de Trabajo

### Cambios realizados:
1.  **Fix de LLM**: Se añadió un parser de fallback en `OpenAILLM` para modelos que no soportan `tool_calls` nativos.
2.  **Plugins de Pepper**: Tres plugins nuevos para manejar el audio y la orquestación híbrida vía Zenoh.
3.  **Visualización**: WebSim configurado en el puerto `8005` para evitar conflictos.
4.  **Repositorio**: Todo el código ha sido profesionalizado y subido a la rama `dev` del fork `albertovalverde/OM1`.

### Cómo probar la demo:
1.  Arranca el servidor de Moshi/PersonaPlex con el puente Zenoh.
2.  Arranca Pepper en OM1: `uv run src/run.py pepper`.
3.  Interactúa mediante el simulador o `interactuar_pepper.py`.

---

> [!NOTE]
> Esta arquitectura permite actualizar OM1 desde el repositorio oficial de Deepmind sin romper la lógica específica de hardware y audio de Pepper, que vive en sus propios plugins y ramas.
