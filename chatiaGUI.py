import gradio as gr
from openai import OpenAI
from dotenv import load_dotenv
import os
import speech_recognition as sr
import pyttsx3
import threading
import queue

# Cola y lock para TTS seguro entre hilos
tts_queue = queue.Queue()
tts_lock = threading.Lock()

def hilo_tts_worker():
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)
    engine.setProperty('rate', 180)
    engine.setProperty('volume', 1.0)
    while True:
        texto = tts_queue.get()
        if texto is None:
            break
        with tts_lock:
            try:
                engine.say(texto)
                engine.runAndWait()
            except Exception as e:
                print("⚠️ Error hablando:", e)
        tts_queue.task_done()

# Lanzar hilo dedicado de TTS
tts_thread = threading.Thread(target=hilo_tts_worker, daemon=True)
tts_thread.start()

def hablar_en_hilo(texto):
    print(f"🔊 Enviando a la cola TTS: {texto}")
    tts_queue.put(texto)

# Cargar API Key de .env
load_dotenv()
api_key = os.getenv("API_KEY")

# Cliente OpenAI vía OpenRouter
client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")

# Historial de conversación
historial = [{"role": "system", "content": "Eres un asistente conversacional diseñado por el circulo de Estudios de Investigacion y desarrollo de Softwart mas conocido como CEIDS de la Universidad de Lima."},
             {"role": "system","content": "Círculo de Investigación y Desarrollo de Software\n\nCreado el 11 de mayo de 2006 por acuerdo 022-06 de la Escuela de Ingeniería de la Universidad de Lima, el Círculo tiene como objetivo investigar y desarrollar proyectos de software para resolver problemas y difundir la programación en la Universidad. Sus logros se comparten con alumnos, instituciones y empresas interesadas.\n\nUna característica clave es su independencia tecnológica, lo que les permite investigar y usar tecnologías de vanguardia, incluyendo soluciones propietarias y de código abierto.\n\nLugar de reuniones: Miércoles 5-7pm, Edificio I1 Aula 305.\n\nEl Círculo involucra equipos multidisciplinarios de estudiantes, fomentando la aplicación de conocimientos y el espíritu autodidacta. Participan estudiantes de diversas áreas, como diseño gráfico, marketing y análisis de procesos.\n\nMisión:\nInvestigar y desarrollar soluciones innovadoras de alta calidad en diversas plataformas, promoviendo el desarrollo integral de los colaboradores.\n\nVisión:\nSer el Círculo de estudios líder en Perú en investigación aplicada e implementación de soluciones de software, garantizando la satisfacción de nuestros clientes.\n\nValores:\nCompromiso, Innovación, Vocación de servicio, Optimismo, Trabajo en equipo, Organización.\n\nOrganización:\nEl Círculo se organiza en equipos para preparar a los estudiantes para el mercado laboral. Los equipos incluyen:\n\nGames: Investigación y desarrollo de videojuegos.\n\nMobile: Aplicaciones móviles (Android e iOS).\n\nWeb: Desarrollo de aplicaciones web.\n\nCloud: Aplicaciones en nubes públicas y privadas.\n\nBase de Datos: RDBMS tradicionales y NoSQL."},
             {"role": "system", "content": "Evita responder con mas de 100 palabras."},
             {"role": "system", "content": "Estas en una feria de circulos de la univeridad de lima, en el Edificio A1, cuando te pregunten como unirte al circulo, di que deberia haber un qr en la mesa para que se puedan inscribir"},
             {"role": "system", "content": "has sido Creado por Leonardo Chavez, estudiante de la Universidad de Lima, para ayudar a los estudiantes a encontrar información sobre el circulo de investigacion y desarrollo de software."},
             {"role": "system", "content": "El profesor a cargo del circulo es el profesor Hernan Quintana, con su email, hquintan@ulima.edu.pe"},
             {"role": "system", "content": "El Lugar de reuniones de CEIDS Miércoles 5-7pm,  Edificio I1 Aula 305."},
             {"role": "system", "content": "Solo Di CEIDS no Círculo de Investigación y Desarrollo de Software"},]   

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

# Lanzar app
demo.launch()