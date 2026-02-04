# Manual del Sistema OM1

Este documento explica cómo funciona el sistema OM1, su arquitectura y cómo interactúan sus componentes para dar vida al agente (en este caso, Spot).

## 1. Arquitectura General

OM1 es un "Cortex" (Corteza) para robots. Funciona mediante un ciclo continuo de **Percepción -> Razonamiento -> Acción**.

### Componentes Clave:
*   **Configuración (`config/`)**: Archivos `.json5` que definen la identidad, entradas, modelo de lenguaje (LLM), y acciones del robot.
*   **Runtime (`src/run.py`)**: El motor que ejecuta al agente.
*   **Fuser**: Combina todas las entradas (sensores, cámara, mensajes) en un solo "contexto" o prompt para el LLM.
*   **LLM (Cerebro)**: Procesa el contexto y decide qué acciones tomar.
*   **Action Orchestrator**: Ejecuta las órdenes del LLM (hablar, moverse, cambiar expresión).
*   **Simulator (WebSim)**: Una interfaz web para ver lo que el robot está haciendo en tiempo real.

---

## 2. El Ciclo de Vida (Tick)

El sistema funciona en "ticks" (ciclos). En cada tick sucede lo siguiente:

1.  **Fusión (Fuse)**: El sistema recoge datos de todas las `agent_inputs` (ej: cámara, sensores de batería, mensajes de Ethereum).
2.  **Consulta al LLM (Think)**: Se envía un prompt al servidor de lenguaje (vLLM en `fcas1bcalc:8008`). El sistema usa un "Historial de Memoria" para que el robot recuerde lo que pasó anteriormente.
3.  **Acción (Act)**: El LLM responde con acciones. Por ejemplo: `{"move": "sit", "speak": "¡Hola!", "emotion": "happy"}`.
4.  **Distribución**: Estas acciones se envían simultáneamente al robot real (si está conectado) y al simulador web.

---

## 3. Configuración del Agente (`spot.json5`)

Este archivo es el "ADN" del robot. Aquí puedes cambiar:

*   **`system_prompt`**: La personalidad del robot (ej: "Eres un perro curioso").
*   **`agent_inputs`**: Qué sensores puede usar (VLM para ver imágenes, Governance para recibir órdenes).
*   **`cortex_llm`**: Qué modelo usa. Hemos configurado el plugin `OpenAILLM` para conectar con un servidor local compatible con OpenAI.
*   **`simulators`**: Configuración del puerto y host para ver al robot en la web.

---

## 4. Plugins de LLM

El sistema es modular. Hemos modificado el plugin `OpenAILLM` para que sea más inteligente:
*   **Fallback Parser**: Si el modelo de IA no soporta "tool calls" nativas (como muchos modelos Open Source), nuestro sistema ahora puede extraer las acciones directamente del texto o de bloques JSON.
*   **Mapping**: Mapea automáticamente nombres de acciones comunes (ej: "Action", "Command") a las etiquetas que el robot entiende.

---

## 5. Visualización (WebSim)

Puedes ver el estado de Spot accediendo a:
`http://fcas1bcalc:8004`

En el simulador verás:
*   **Input History**: Todo lo que el robot ha "sentido" o escuchado.
*   **Current State**: La acción actual y la última vez que habló.
*   **System Latency**: Cuánto tarda el "cerebro" en procesar la información.

---

## 6. Comandos Útiles

*   **Iniciar el agente**: `uv run src/run.py spot`
*   **Ver logs detallados**: `uv run src/run.py spot --log-level INFO`
*   **Cambiar configuración**: Edita `config/spot.json5` y el sistema se recargará automáticamente (Hot-reload).

---

> [!TIP]
> Si el robot no se mueve, revisa los logs para ver si el LLM está recibiendo entradas. El sistema necesita "sentir" algo para reaccionar.
