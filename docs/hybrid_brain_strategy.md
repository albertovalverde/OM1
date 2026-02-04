# Arquitectura Profesional: Cerebro Híbrido Pepper (PersonaPlex + OpenAI)

Este diseño permite que Pepper tenga la **agilidad humana** de PersonaPlex (Moshi) y la **capacidad cognitiva** de un LLM complejo (OpenAI/GPT-4).

---

## 1. El Concepto: "Sistema 1 vs Sistema 2"

Siguiendo la teoría de Daniel Kahneman:
*   **Sistema 1 (PersonaPlex/Moshi)**: Rápido, intuitivo y reactivo. Gestiona el audio E2E, las muletillas ("Hmm...", "Entiendo...") y las respuestas sociales inmediatas.
*   **Sistema 2 (OpenAI)**: Lento, analítico y profundo. Gestiona tareas lógicas, consultas de datos y razonamiento complejo.

---

## 2. Flujo de Datos Híbrido y Desacoplado

### A. La Capa de Interacción (Foreground)
*   PersonaPlex recibe el audio de Pepper y responde **inmediatamente**.
*   Si la pregunta es compleja, PersonaPlex está instruido (vía System Prompt) para decir algo como: *"Excelente pregunta, déjame pensar un segundo..."* mientras mantiene el canal de audio abierto.

### B. El Puente de Razonamiento (Background)
*   OM1 tiene un plugin `HybridPersonaPlexLLM` que escucha la transcripción en tiempo real que genera PersonaPlex.
*   En cuanto detecta una intención compleja, lanza una petición asíncrona a **OpenAI**.
*   **Inyección de Pensamiento**: Cuando OpenAI responde, el resultado se envía de vuelta a PersonaPlex como un "Contexto de Pensamiento" para que PersonaPlex lo verbalice con su propia voz y estilo.

---

## 3. Implicaciones de usar el Server de Moshi + UI

Usar el servidor de Moshi tiene las siguientes ventajas y retos:
*   **Latencia**: Al ser E2E (Audio-to-Audio), la latencia es mínima. 
*   **UI de Moshi**: La interfaz original de Moshi es excelente para ver los niveles de audio, pero para Pepper necesitaremos que esa UI esté "oculta" o integrada en el sistema de visualización de OM1 para que el operador vea qué modelo está activado.
*   **Desacoplamiento**: El server de Moshi correrá en su propio contenedor/proceso. OM1 se conectará a él mediante un socket o Zenoh.

---

## 4. Estructura de Plugins en OM1

### `llm/plugins/hybrid_personaplex.py`
Este será el "Director de Orquesta":
1.  **Stream de Audio**: Lo mantiene activo con PersonaPlex.
2.  **Monitor de Transcripción**: Analiza lo que el usuario está diciendo.
3.  **Decision Maker**: 
    - ¿Es una charla trivial? -> Deja que PersonaPlex responda solo.
    - ¿Es una duda compleja? -> Llama a OpenAI + pide a PersonaPlex que genere un "filler" de pensamiento.

### `actions/speak/connector/hybrid_speaker.py`
Este conector será inteligente:
*   Puede mezclar el audio que viene de PersonaPlex con señales de control de OM1.

---

## 5. Esquema de Sincronización Profesional

Como quieres mantener forks separados:
1.  **Repo 1 (OM1)**: Contiene los plugins de "Hardware" y la orquesta básica.
2.  **Repo 2 (PersonaPlex/Moshi)**: Contiene el modelo 7B y el servidor de audio.
3.  **Zenoh Bridge**: Es el único punto donde ambos mundos se tocan. Si actualizas OM1, los tópicos de Zenoh siguen siendo los mismos, por lo que nada se rompe.

---

### Ejemplo de Interacción Híbrida:
*   **Usuario**: "Pepper, ¿cuál es la raíz cuadrada de la distancia entre la Tierra y Marte hoy?"
*   **PersonaPlex (Sistema 1)**: "Vaya, esa es una consulta técnica... déjame calcularlo un momento [genera sonido de pensamiento]."
*   **OpenAI (Sistema 2)**: Calcula el dato preciso -> Envía texto a PersonaPlex.
*   **PersonaPlex (Sistema 1)**: "Ya lo tengo. La distancia hoy es de... y su raíz cuadrada es..."

> [!TIP]
> Esto evita que Pepper se quede "mudo" durante los 2-3 segundos que tarda OpenAI en responder, eliminando el silencio incómodo en las demos.
