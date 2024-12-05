import os
import pickle
import re
from nltk.corpus import stopwords
import nltk

# Ruta al modelo guardado
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "informe_analysis_model.pkl")

# Descargar stopwords si no están disponibles
nltk.download('stopwords')
stop_words = set(stopwords.words('spanish'))

# Cargar el modelo y el vectorizador
with open(MODEL_PATH, "rb") as file:
    vectorizer, model = pickle.load(file)

def preprocess_text(text):
    # Limpia y normaliza el texto de entrada
    text = text.lower()
    text = re.sub(r'\d+', '', text)  # Eliminar números
    text = re.sub(r'[^\w\s]', '', text)  # Eliminar caracteres especiales
    text = re.sub(r'\s+', ' ', text).strip()  # Eliminar espacios adicionales
    text = " ".join(word for word in text.split() if word not in stop_words)  # Eliminar stopwords
    return text

def analyze_informe(description):
    # Analiza la descripción de un informe y devuelve el diagnóstico más probable con confianza
    description = preprocess_text(description)
    description_tfidf = vectorizer.transform([description])
    probabilities = model.predict_proba(description_tfidf)

    # Índice del diagnóstico más probable
    max_prob_index = probabilities[0].argmax()
    max_prob = probabilities[0][max_prob_index]

    # Diagnóstico más probable
    most_probable = model.classes_[max_prob_index]

    # Diagnósticos alternativos (ordenados por probabilidad)
    top_indices = probabilities[0].argsort()[-3:][::-1]  # Los 3 diagnósticos más probables
    top_diagnoses = [
        {"diagnosis": model.classes_[i], "confidence": round(probabilities[0][i] * 100, 2)}
        for i in top_indices
    ]

    # Si la confianza es baja (menos del 60%), devolver "no concluyente"
    if max_prob < 0.6:
        return {
            "most_probable": "Diagnóstico no concluyente",
            "confidence": round(max_prob * 100, 2),
            "alternatives": top_diagnoses,
        }

    return {
        "most_probable": most_probable,
        "confidence": round(max_prob * 100, 2),
        "alternatives": top_diagnoses,
    }