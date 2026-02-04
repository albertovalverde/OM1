# Arquitectura Profesional: Desacoplamiento de PersonaPlex en OM1

Para cumplir con el requerimiento de mantener **OM1** y **PersonaPlex** como forks independientes con sincronización diaria, seguiremos una estrategia basada en **Plugins de Interface** y **Middleware de Mensajería (Zenoh)**.

---

## 1. El Puente de Comunicación: Zenoh
No integraremos el código de PersonaPlex dentro del núcleo de OM1. En su lugar, PersonaPlex funcionará como un servicio externo que se comunica mediante el bus de datos **Zenoh**.

### Tópicos Zenoh Propuestos:
*   `pepper/audio/mic`: Flujo de audio crudo desde Pepper hacia PersonaPlex.
*   `pepper/audio/speaker`: Flujo de audio de respuesta desde PersonaPlex hacia Pepper.
*   `pepper/personaplex/metadata`: JSON con transcripciones en tiempo real y detección de interrupciones.
*   `pepper/personaplex/control`: Comandos de control (cambio de voz, actualización de sistema, interrupción forzada).

---

## 2. Implementación en OM1 (Lado Robot)
Todo el código residirá en las carpetas de `plugins/`, las cuales son ignoradas por la mayoría de cambios del núcleo o son fácilmente mantenibles.

### A. Input Plugin: `PersonaPlexMicInput`
*   **Ruta**: `src/inputs/plugins/personaplex_mic.py`
*   **Función**: Captura el audio del hardware y lo publica en Zenoh. No hace ASR localmente.
*   **Beneficio**: El núcleo de OM1 no sabe que PersonaPlex existe, solo sabe que hay un flujo de audio saliendo.

### B. Action Plugin: `PersonaPlexSpeakerAction`
*   **Ruta**: `src/actions/speak/connector/personaplex_zenoh.py`
*   **Función**: Se suscribe al tópico de audio de salida de PersonaPlex y lo envía a los altavoces de Pepper.
*   **Beneficio**: Mantiene el control del hardware separado del cerebro.

### C. Proxy LLM Plugin: `PersonaPlexProxyLLM`
*   **Ruta**: `src/llm/plugins/personaplex_proxy.py`
*   **Función**: En lugar de hacer una llamada HTTP, este plugin envía el "contexto" o "system prompt" a PersonaPlex vía Zenoh y recibe actualizaciones de estado.
*   **Beneficio**: Sigue la interfaz `LLM` de OM1, por lo que es totalmente compatible con el `Cortex`.

---

## 3. Estrategia de Sincronización (Forks)

### Aislamiento de Código:
Para que tus sincronizaciones diarias de OM1 no rompan nada:
1.  **Cero cambios en `src/runtime/`**: Toda la lógica de PersonaPlex debe vivir fuera.
2.  **Configuración Única**: Solo el archivo `config/pepper.json5` referencia a los nuevos plugins.
3.  **Inyección de Dependencias**: OM1 carga los plugins dinámicamente. Si el archivo del plugin existe en la carpeta, OM1 lo usará.

### Estructura de Archivos recomendada para tu Fork:
```text
OM1/ (Tu Fork)
├── config/
│   └── pepper.json5 (Solo aquí activas PersonaPlex)
├── src/
│   ├── inputs/plugins/
│   │   └── personaplex_mic.py [NUEVO]
│   ├── actions/speak/connector/
│   │   └── personaplex_zenoh.py [NUEVO]
│   └── llm/plugins/
│       └── personaplex_proxy.py [NUEVO]
└── ... (Archivos de OM1 Upstream - Sincronizados diariamente)
```

---

## 4. Gestión de Interrupciones (Full Duplex)
Para lograr el "Full Duplex" profesional:
1.  `PersonaPlexMicInput` detecta voz.
2.  Envía una señal de `USER_STARTED_SPEAKING` vía Zenoh.
3.  `PersonaPlexSpeakerAction` recibe esta señal y **vacía instantáneamente** su buffer de audio.
4.  PersonaPlex (el otro fork) deja de generar audio y empieza a escuchar.

---

> [!IMPORTANT]
> Esta arquitectura permite que si mañana hay una actualización crítica en el `CortexRuntime` de OM1, puedas hacer `git pull upstream main` sin conflictos, ya que tu implementación de PersonaPlex es totalmente "plug-and-play".
