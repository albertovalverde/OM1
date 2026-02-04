# Guía: Cómo crear una Demo con un Nuevo Robot en OM1

Para llevar OM1 a un nuevo robot (ej: Pepper, Go2, o uno propio), debes entender que el sistema es agnóstico al hardware. Aquí están los pasos para migrar el "cerebro" de Spot a otro robot.

## 1. Crear el Archivo de Configuración (`config/mi_robot.json5`)
Copia `config/spot.json5` y cámbiale el nombre. Los puntos clave a editar son:
*   **`name`**: El nombre de tu nueva demo.
*   **`agent_actions`**: Aquí defines qué *puede* hacer tu robot.
    ```json
    {
      name: "caminar", // Nombre interno
      llm_label: "move", // Cómo lo llamará la IA
      implementation: "passthrough",
      connector: "mi_conector_personalizado", // El puente al hardware
    }
    ```

## 2. Definir los Conectores (`src/actions/connectors/`)
Esta es la parte más importante. Un conector es el código Python que traduce el deseo de la IA en movimiento real (o simulado).
*   Si el robot usa **ROS2**, puedes usar el `ros2_connector.py`.
*   Si el robot tiene una **API propietaria**, crea un nuevo archivo en `src/actions/connectors/mi_robot.py`.
*   **Interfaz**: Tu conector debe heredar de `AgentActionConnector` e implementar el método `connect(input_interface)`.

## 3. Adaptar el System Prompt
La IA necesita saber en qué cuerpo "vive". Cambia el `system_prompt_base` en tu `.json5`:
*   *Spot*: "Eres un perro robótico..."
*   *Pepper*: "Eres un robot humanoide asistencial..."
*   *Brazo Robótico*: "Eres una herramienta de precisión..."

## 4. Entradas Sensoriales (`agent_inputs`)
¿Qué ve o siente tu nuevo robot?
*   Si tiene cámaras, usa el plugin `VLM_COCO_Local` o uno basado en la nube.
*   Si detecta voz, añade un plugin de ASR (Reconocimiento de voz).
*   Si tiene batería o sensores de posición, crea un `provider` para que esa info llegue al `Fuser`.

## 5. El Proceso de Desarrollo Sugerido
Para una demo exitosa, sigue este orden:
1.  **Simulación primero**: Configura el robot para que use el simulador `WebSim`. Verifica que cuando la IA dice "hola", el campo `Last Speech` de la web se actualice.
2.  **Mocking de Acciones**: Usa conectores de tipo `mock` o `log` que solo impriman en consola para validar que la lógica del LLM es la correcta.
3.  **Integración de Hardware**: Una vez que la IA "razona" bien, conecta el hardware real en el conector.

## Checklist para tu nueva Demo:
- [ ] Nuevo archivo `.json5` en la carpeta `config/`.
- [ ] Acciones definidas con sus respectivos conectores.
- [ ] Servidor de LLM configurado (como hicimos con vLLM).
- [ ] Ejecutar con: `uv run src/run.py mi_robot`.

---
**Consejo para el LLM:** Si usas un modelo pequeño para la demo, asegúrate de que el `system_prompt_examples` en tu config sea muy claro, para que la IA aprenda rápido el formato de salida que esperas.
