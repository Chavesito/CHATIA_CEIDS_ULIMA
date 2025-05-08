from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
api = os.getenv("API_KEY")

client = OpenAI(api_key=f"{api}", base_url="https://openrouter.ai/api/v1")

response = client.chat.completions.create(
    model="deepseek/deepseek-r1:free",
    messages=[
        {"role": "system", "content": "Eres una IA de asistencia para alumnos del circulo de estudios de programacion"},
        {"role": "user", "content": f"Hola, me puedes decir los feriados de este mes, en Peru"}
    ]
)


print(response.choices[0].message.content)