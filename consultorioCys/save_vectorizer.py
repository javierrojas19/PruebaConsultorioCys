import pickle
from sklearn.feature_extraction.text import TfidfVectorizer

# Simulación de datos para entrenar el vectorizador (puedes usar tus propios datos)
data = [
    "El paciente presenta fiebre alta y dolor de cabeza",
    "El paciente tiene tos seca y dificultad para respirar",
    "El paciente muestra presión arterial elevada y mareos",
    "Dolor abdominal intenso acompañado de náuseas",
    "Cansancio extremo y pérdida de peso reciente",
    "El paciente tiene picazón en la piel y ojos amarillos",
    "Dolor en el pecho al realizar actividades físicas",
    "Fiebre, sudores nocturnos y pérdida de apetito",
    "Dolor en las articulaciones y rigidez matutina",
    "El paciente tiene dolor de garganta y congestión nasal"
]

# Crear y entrenar el vectorizador
vectorizer = TfidfVectorizer()
vectorizer.fit(data)

# Guardar el vectorizador como un archivo .pkl
with open("tfidf_vectorizer.pkl", "wb") as file:
    pickle.dump(vectorizer, file)

print("Archivo 'tfidf_vectorizer.pkl' creado con éxito.")
