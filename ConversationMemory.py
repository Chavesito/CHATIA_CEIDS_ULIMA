import gradio as gr
from openai import OpenAI
from dotenv import load_dotenv
import os
import speech_recognition as sr
import pyttsx3
import threading

# Inicializar TTS con candado
tts = pyttsx3.init()
voices = tts.getProperty('voices')
tts.setProperty('voice', voices[0].id) 
tts.setProperty('rate', 160)
tts.setProperty('volume', 1.0)
tts_lock = threading.Lock()

def hablar_en_hilo(texto):
    print(f"🔊 Intentando hablar: {texto}")  # Depuración
    with tts_lock:
        try:
            tts.stop()  # Detiene cualquier reproducción en curso
            tts.say(texto)
            print("⏳ Ejecutando tts.runAndWait()...")  # Depuración
            tts.runAndWait()  # Bloquea hasta que termine de hablar
            print("✅ Hablar completado")  # Depuración
        except Exception as e:
            print("⚠️ Error hablando en voz alta:", e)
# Cargar API Key de .env
load_dotenv()
api_key = os.getenv("API_KEY")

# Cliente OpenAI vía OpenRouter
client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")

# Historial de conversación
historial = [{"role": "system", "content": "Eres un asistente conversacional que responde en español."}]

# Transcripción de voz a texto
def transcribir_local(audio_filepath):
    r = sr.Recognizer()
    with sr.AudioFile(audio_filepath) as source:
        audio = r.record(source, duration=10)
    try:
        texto = r.recognize_google(audio, language="es-ES")
        return texto
    except sr.UnknownValueError:
        return "⚠️ No entendí lo que dijiste."
    except sr.RequestError as e:
        return f"⚠️ Error de conexión con Google: {e}"
    except Exception as e:
        return f"⚠️ Error procesando el audio: {e}"

# Función principal
def procesar_mensaje(mensaje_usuario, chat_history):
    if not mensaje_usuario.strip():
        return "", chat_history

    historial.append({"role": "user", "content": mensaje_usuario})
    print("🗣️ Usuario:", mensaje_usuario)

    try:
        respuesta = client.chat.completions.create(
            model="meta-llama/llama-3-8b-instruct",
            messages=historial,
            timeout=30
        )
        respuesta_texto = respuesta.choices[0].message.content.strip()
    except Exception as e:
        respuesta_texto = f"⚠️ Error al generar respuesta: {e}"

    historial.append({"role": "assistant", "content": respuesta_texto})
    chat_history.append({"role": "user", "content": mensaje_usuario})
    chat_history.append({"role": "assistant", "content": respuesta_texto})

    threading.Thread(target=hablar_en_hilo, args=(respuesta_texto,)).start()
    return "", chat_history

# Entrada por voz
def responder_audio(audio_filepath, chat_history):
    if not audio_filepath or not os.path.exists(audio_filepath):
        return None, [{"role": "system", "content": "⚠️ No se detectó un audio válido."}]
    try:
        mensaje_usuario = transcribir_local(audio_filepath)
        # Eliminar el archivo después de usarlo
        try:
            os.remove(audio_filepath)
        except Exception as e:
            print("⚠️ No se pudo eliminar el archivo:", e)
        return None, procesar_mensaje(mensaje_usuario, chat_history)[1]
    except Exception as e:
        print("❌ Error:", e)
        return None, [{"role": "system", "content": f"⚠️ Error: {e}"}]

# Entrada por texto
def responder_texto(mensaje_usuario, chat_history):
    return procesar_mensaje(mensaje_usuario, chat_history)

# Interfaz Gradio
with gr.Blocks(title="Chat IA ULIMA por Voz y Texto") as demo:
    gr.Markdown("### 🤖 Chat IA ULIMA por Voz y Texto\nPuedes hablar o escribir, y la IA responderá en voz alta.")

    chatbot = gr.Chatbot(label="Chat IA ULIMA", height=400, type="messages")

    with gr.Row():
        entrada_texto = gr.Textbox(placeholder="Escribe tu mensaje aquí y presiona Enter...", show_label=False)
        entrada_voz = gr.Audio(sources=["microphone"], type="filepath", format="wav", label="🎙️ O habla aquí")

    with gr.Row():
        btn_enviar_texto = gr.Button("Enviar texto")
        btn_enviar_voz = gr.Button("Enviar voz")
        btn_limpiar = gr.Button("Limpiar")

    btn_enviar_texto.click(fn=responder_texto, inputs=[entrada_texto, chatbot], outputs=[entrada_texto, chatbot])
    entrada_texto.submit(fn=responder_texto, inputs=[entrada_texto, chatbot], outputs=[entrada_texto, chatbot])
    btn_enviar_voz.click(fn=responder_audio, inputs=[entrada_voz, chatbot], outputs=[entrada_voz, chatbot])
    btn_limpiar.click(fn=lambda: ("", []), inputs=None, outputs=[entrada_texto, chatbot])

demo.launch()
