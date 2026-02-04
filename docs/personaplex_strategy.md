# Plan: Implementación de NVIDIA PersonaPlex en OM1

NVIDIA PersonaPlex es un sistema **End-to-End (E2E)** que procesa audio directamente y devuelve audio, permitiendo conversaciones "full-duplex" (bidireccionales simultáneas) con latencia ultra baja (~170ms).

## Arquitectura Propuesta en OM1

A diferencia del flujo tradicional (ASR -> LLM -> TTS), PersonaPlex requiere un flujo de **Streaming de Audio** constante.

### 1. Cambio de Paradigma: Flujo Unificado
En lugar de procesar texto, OM1 actuaría como un puente de audio:
*   **Entrada**: `src/inputs/plugins/personaplex_input.py` envía el flujo del micrófono de Pepper a NVIDIA via gRPC/WebSocket.
*   **Procesamiento**: Un nuevo plugin de LLM `src/llm/plugins/personaplex_llm.py` gestiona la sesión E2E.
*   **Salida**: `src/actions/speak/connector/personaplex_speaker.py` recibe el flujo de audio de retorno y lo reproduce en Pepper.

### 2. Implementación Técnica (Pasos)

#### A. Input Plugin (Micrófono)
Captura audio PCM de Pepper y lo publica en un tópico de Zenoh: `om/audio/mic`.
```python
# Pseudocódigo para personaplex_input.py
class PersonaPlexInput(FuserInput):
    async def _poll(self):
        audio_chunk = self.mic.read()
        self.zenoh.put("om/audio/mic", audio_chunk)
```

#### B. Unified LLM Plugin
Este plugin no devuelve texto, sino que coordina el flujo de audio de NVIDIA.
```python
# Pseudocódigo para personaplex_llm.py
class PersonaPlexLLM(LLM):
    async def ask(self, audio_stream):
        # Conecta con el modelo de 7B de NVIDIA
        # Gestiona interrupciones (Barge-in) internamente
        return nvidia_audio_output_stream
```

#### C. Full Duplex (Interrupciones)
Para que Pepper pueda ser interrumpido:
1.  El modelo de NVIDIA detecta voz mientras está hablando.
2.  Envía una señal de `interrupt`.
3.  El `ActionOrchestrator` de OM1 limpia el buffer de audio de salida inmediatamente para que Pepper "se calle" y escuche.

## 3. Configuración en `pepper.json5`

```json5
{
  cortex_llm: {
    type: "PersonaPlexLLM",
    config: {
        model: "nvidia/personaplex-7b",
        voice_embedding: "pepper_voice.pt", // Voz clonada de Pepper
        barge_in_enabled: true,
    }
  },
  agent_actions: [
    {
      name: "speak",
      connector: "personaplex_stream", // Usa el stream directo
    }
  ]
}
```

## Beneficios para Pepper:
*   **Interacciones naturales**: Puedes interrumpir a Pepper y él reaccionará instantáneamente.
*   **Personalidad**: Puedes usar "audio embeddings" de la voz original de Pepper (robot-like pero fluida).
*   **Velocidad**: Al no haber conversión a texto intermedia, la respuesta es casi humana.
