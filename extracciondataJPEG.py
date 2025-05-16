from openai import OpenAI
from dotenv import load_dotenv
import os
import pandas as pd
import pytesseract
from PIL import Image

# Configurar ruta a ejecutable de Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:/Users/lchavez/AppData/Local/Programs/Tesseract-OCR/tesseract.exe"
os.environ['TESSDATA_PREFIX'] = r"C:/Users/lchavez/AppData/Local/Programs/Tesseract-OCR/tessdata"

# Cargar variables de entorno
load_dotenv()
api_key = os.getenv("API_KEY")

# Configurar cliente de DeepSeek
client = OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

# Ruta de la carpeta con las imágenes
carpeta_comprobantes = "comprobantes"

# Lista para almacenar los datos extraídos
datos = []

# Función para procesar una imagen con Tesseract y DeepSeek
def procesar_imagen_con_tesseract_y_deepseek(ruta_imagen):
    # Convertir la imagen a texto usando Tesseract
    texto_crudo = pytesseract.image_to_string(Image.open(ruta_imagen), lang='spa')

    # Enviar el texto crudo como mensaje a DeepSeek
    respuesta = client.chat.completions.create(
        model="deepseek/deepseek-r1:free",
        messages=[
            {"role": "system", "content": "Eres un modelo de ia que responde en español"},
            {"role": "user", "content": "Extrae los datos de este texto."},
            {"role": "user", "content": texto_crudo}
        ]
    )

    # Obtener y devolver la respuesta de DeepSeek
    respuesta_modelo = respuesta.choices[0].message.content.strip()
    print(f"Datos extraídos de {ruta_imagen}:\n{respuesta_modelo}\n")
    return respuesta_modelo

# Procesar todas las imágenes en la carpeta
for archivo in os.listdir(carpeta_comprobantes):
    if archivo.lower().endswith((".jpg", ".jpeg", ".png")):
        ruta_imagen = os.path.join(carpeta_comprobantes, archivo)
        print(f"Procesando archivo: {archivo}...")  # Imprimir el archivo que se está procesando
        datos_extraidos = procesar_imagen_con_tesseract_y_deepseek(ruta_imagen)
        print(f"Respuesta de DeepSeek para {archivo}: {datos_extraidos}\n")  # Imprimir la respuesta de DeepSeek
        datos.append({"Archivo": archivo, "Datos": datos_extraidos})

# Crear un DataFrame con los datos
df = pd.DataFrame(datos)

# Guardar los datos en un archivo Excel
df.to_excel("comprobantes.xlsx", index=False)
print("Datos extraídos y guardados en comprobantes.xlsx")