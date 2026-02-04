# Resumen del proceso y guía de desarrollo para Spot

## Estado actual del proceso
- **Comando ejecutado:** `uv run src/run.py spot`
- El proceso está activo y genera un flujo continuo de entradas del tipo **“Spot sensed the following: Universal Laws …”**.
- Cada entrada desencadena la carga de reglas desde la blockchain de Ethereum y la emisión de un comando `AvatarProvider` (normalmente `happy`).
- Spot recibe la información, intenta generar un resumen (summary) del estado, pero con frecuencia la petición al LLM falla por **tiempos de espera (timeout)**.  
- Cuando la generación falla, el sistema vuelve a intentar el mismo ciclo: cargar reglas, preguntar al LLM y volver a intentar el resumen.  
- Mientras tanto, Spot permanece en **estado `idle`**, sin ejecutar ninguna acción concreta, esperando una respuesta válida del modelo de lenguaje.

## Problemas observados
1. **Timeout recurrentes** al solicitar al LLM que genere el resumen, lo que bloquea la cadena de procesamiento.
2. **Mensajes repetitivos** de entrada (las mismas leyes universales se envían una y otra vez), lo que genera bucles innecesarios.
3. La **respuesta de Spot** se queda en “Given that information, Spot took these actions:” sin contenido adicional, indicando que no se ha definido ninguna acción concreta.
4. **Sobrecarga del historial**: el registro de mensajes crece rápidamente, provocando truncamientos automáticos.

## Guía de desarrollo (en español)
### 1. Manejo de fallos de LLM
- Implementar un **retry con back‑off** limitado (por ejemplo, máximo 3 intentos) antes de abortar la tarea.
- Si persiste el timeout, registrar el error y **pasar a un fallback** (por ejemplo, usar un modelo local más rápido o generar un mensaje de error para el usuario).

### 2. Optimización del flujo de entrada
- Detectar entradas duplicadas (las leyes universales) y **filtrarlas** antes de volver a enviarlas al LLM.
- Consolidar varias lecturas idénticas en una única solicitud de resumen.

### 3. Estado de Spot
- Mientras Spot está `idle`, puede ejecutar **rutinas de vigilancia** (escaneo de seguridad, diagnóstico de batería) para aprovechar el tiempo.
- Añadir un **watchdog** que cambie el estado a `busy` cuando se recibe una orden válida y vuelva a `idle` al completarla.

### 4. Registro y limpieza del historial
- Mantener un **límite de historial** (p. ej., 1000 mensajes) y archivar o descartar los más antiguos de forma estructurada.
- Guardar los logs relevantes en un archivo separado (`spot_logs.txt`) para depuración futura.

### 5. Generación del resumen para Spot
- El resumen debe incluir:
  1. **Leyes universales** (primer, segundo y tercer ley, amabilidad y distancia mínima de 50 cm).
  2. **Prioridades operativas**: seguridad humana → obediencia → autoprotección.
  3. **Checklist de interacción** (detectar, evaluar, mantener distancia, escuchar, validar, confirmar, ejecutar, monitorear).
  4. **Recomendaciones prácticas**: escaneo continuo, gestión de distancia, comunicación cortés, asistencia proactiva, manejo de errores, rutina de auto‑chequeo, protocolo de emergencia.
- Proveer versiones cortas de referencia rápida (una frase por regla) para que Spot pueda consultarlas rápidamente.

### 6. Guardar la guía
- El contenido anterior se guarda en `guia_desarrollo.md` para que el equipo tenga una referencia clara y en español del estado actual y de los pasos a seguir.

---

**Nota:** Esta guía está pensada para mejorar la robustez del ciclo de interacción de Spot y evitar los bucles de timeout que están saturando el sistema. Implementar los puntos anteriores debería reducir la latencia y permitir que Spot responda de manera más efectiva a los humanos y a su entorno.
