import gradio as gr
from openai import OpenAI
from dotenv import load_dotenv
import os

# Cargar API Key
load_dotenv()
api_key = os.getenv("API_KEY")

client = OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

# Historial de conversación
historial = [
    {"role": "system", "content": "Eres un asistente inteligente y conversacional que responde en español."}
]

# Función para responder
def responder(mensaje_usuario, chat_historial):
    historial.append({"role": "user", "content": mensaje_usuario})

    respuesta = client.chat.completions.create(
        model="deepseek/deepseek-r1:free",
        messages=historial
    )

    respuesta_texto = respuesta.choices[0].message.content.strip()
    historial.append({"role": "assistant", "content": respuesta_texto})

    chat_historial.append((mensaje_usuario, respuesta_texto))
    return "", chat_historial

# Construir la interfaz manualmente con Blocks
tema_ulima = gr.themes.Base(
    primary_hue="orange",
    secondary_hue="gray",
    neutral_hue="gray",
    font=["Roboto", "sans-serif"]
    
)
with gr.Blocks(theme="tema_ulima",title="Chat IA ULIMA") as demo:
    gr.Markdown("### Aplicación realizada por estudiantes del CEIDS ULIMA para interactuar con un modelo de IA.")
    
    chatbot = gr.Chatbot(label="Chat IA ULIMA", height=400)
    msg = gr.Textbox(placeholder="Escribe un mensaje aquí...", show_label=False)
    
    with gr.Row():
        limpiar_btn = gr.Button("Limpiar")
        enviar_btn = gr.Button("Enviar") 

    # Evento al enviar mensaje
    enviar_btn.click(responder, inputs=[msg, chatbot], outputs=[msg, chatbot])
    msg.submit(responder, inputs=[msg, chatbot], outputs=[msg, chatbot])
    limpiar_btn.click(lambda: ("", []), inputs=None, outputs=[msg, chatbot])


demo.launch()
