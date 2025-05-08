from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("API_KEY")

client = OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)


historial = [
    {"role": "system", "content": "Eres un modelo de ia que responde en español"}
]


while True:
    mensaje_usuario = input("Tú: ")

    if mensaje_usuario.lower() in ["salir", "chau", "bye", "adiós"]:
        print("👋 ¡Hasta luego!")
        break

    historial.append({"role": "user", "content": mensaje_usuario})

    respuesta = client.chat.completions.create(
        model="deepseek/deepseek-r1:free",
        messages=historial
    )

    respuesta_modelo = respuesta.choices[0].message.content.strip()
    print(f"DeepSeek:{respuesta_modelo}\n")

    historial.append({"role": "assistant", "content": respuesta_modelo})
