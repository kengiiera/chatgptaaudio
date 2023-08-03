import asyncio
from flask import Flask, request, jsonify
from cachetools import TTLCache
import openai
import json
import requests
import tempfile
from flask_cors import CORS

app = Flask(__name__)
openai.api_key = "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"
CORS(app)
# Configure caching with a TTLCache to store responses for 60 seconds
cache = TTLCache(maxsize=1000, ttl=60)

@app.route('/diagnostics', methods=['POST'])
def get_diagnostics():
    # Obtén el prompt del cuerpo de la solicitud POST
    url = request.json['url']
    response1 = requests.get(url)
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as temp_file:
        temp_file.write(response1.content)
    
    audio_file = open(temp_file.name, "rb")
    
    prompt = openai.Audio.transcribe("whisper-1", audio_file).text
    
    medical_keywords = ["paciente", "malestar","paraclìnicos", "dificultad", "consulta", "historia clínica", "anamnesis", "examen físico", "diagnóstico", "plan de manejo", "tratamiento", "medicamentos", "pruebas de laboratorio", "imágenes médicas", "presión arterial", "ritmo cardíaco", "frecuencia respiratoria", "temperatura corporal", "auscultación pulmonar", "palpitaciones", "disnea", "dolor torácico", "fatiga", "hipertensión arterial", "diabetes mellitus", "enfermedades cardiovasculares", "enfermedades respiratorias", "enfermedades gastrointestinales", "enfermedades endocrinas", "enfermedades metabólicas", "enfermedades infecciosas", "enfermedades autoinmunes", "colesterol", "glucemia", "hemoglobina", "índice de masa corporal", "tomografía computarizada", "resonancia magnética", "electrocardiograma", "ecografía", "endoscopia", "dieta y nutrición", "actividad física", "estilo de vida saludable", "prevención de enfermedades", "síntomas", "malestar", "dolor de cabeza", "dolor de estómago", "resfriado", "gripe", "tos", "dolor de garganta", "mareo", "náuseas", "vómitos", "diarrea", "estreñimiento", "fiebre", "escalofríos", "sudoración", "cansancio", "debilidad", "dolor muscular", "dolor articular", "ardor estomacal", "acidez estomacal", "hinchazón abdominal", "pérdida de apetito", "aumento de peso", "pérdida de peso", "palpitaciones del corazón", "falta de aire", "ronquidos", "dificultad para dormir", "picazón en la piel", "enrojecimiento de la piel", "sarpullido", "caída del cabello", "uñas quebradizas", "alergias", "migrañas", "dolor de espalda", "dolor en el pecho", "presión en el pecho", "hormigueo en las extremidades", "dificultad para concentrarse"]

    # Check if the response is cached
    if url in cache:
        return jsonify(cache[url])

    # Function to fetch data asynchronously
    async def fetch_data():
        is_medical_prompt = any(keyword in prompt.lower() for keyword in medical_keywords)

        if is_medical_prompt:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                   "content":"Con base en la conversación, entre un médico y un paciente, proporciona un resumen en formato JSON con detalles específicos en términos médicos comprensibles. El resumen debe incluir las siguientes items, diligencia todos los items, el json solo debe tener la siguientes propiedades tal como están escritas: Enfermedad_actual, examen_fisico, impresion y plan_de_manejo."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0,
                max_tokens=1024,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
        else:
            # Si el prompt no es relevante para atención médica, proporcionar una respuesta predeterminada
            response = {"choices": [{"message": {"content": "", "role": "assistant"}}]}

        # Extrae la respuesta del modelo
        content = response['choices'][0]['message']['content']

        # Convierte la respuesta en formato JSON
        if content:
            data_json = json.loads(content)
            # Store the response in cache
            cache[url] = data_json
            return data_json
        else:
            return ""
    # Run the asynchronous function and get the result
    data_json = asyncio.run(fetch_data())
    return jsonify(data_json)
if __name__ == '__main__':
    app.run()