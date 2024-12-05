import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

# Datos de entrenamiento de ejemplo
training_data = [
    ("El paciente presenta síntomas de fiebre y tos.", "Infección Respiratoria"),
    ("Dolor agudo en el pecho durante el ejercicio.", "Problema Cardiaco"),
    ("Se observa inflamación en las articulaciones.", "Artritis"),
    ("Dificultad para respirar y dolor de cabeza frecuente.", "Asma"),
    ("El paciente sufre de presión arterial alta.", "Hipertensión"),
]

# Separar texto y etiquetas
texts, labels = zip(*training_data)

# Crear pipeline para procesar texto y entrenar modelo
model_pipeline = make_pipeline(
    TfidfVectorizer(),
    MultinomialNB()
)

# Entrenar el modelo
model_pipeline.fit(texts, labels)

# Guardar el modelo entrenado
model_path = "informe_analysis_model.pkl"
with open(model_path, "wb") as model_file:
    pickle.dump(model_pipeline, model_file)

print(f"Modelo entrenado y guardado en {model_path}")