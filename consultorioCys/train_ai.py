import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report
import pickle
from nltk.corpus import stopwords
import nltk

# Descargar stopwords en español si no están disponibles
nltk.download('stopwords')
spanish_stopwords = stopwords.words('spanish')

# Generar datos simulados
def generate_data():
    # Lista ampliada de enfermedades y síntomas comunes
    data = [
        # Infecciones y problemas respiratorios
        {"symptoms": "fiebre alta, dolor de cabeza, tos persistente", "diagnosis": "Infección respiratoria"},
        {"symptoms": "fiebre, dificultad para respirar, dolor en el pecho", "diagnosis": "Neumonía"},
        {"symptoms": "fiebre, tos seca, pérdida de olfato y gusto", "diagnosis": "COVID-19"},
        {"symptoms": "dolor de garganta, fiebre, dificultad para tragar", "diagnosis": "Amigdalitis"},
        {"symptoms": "secreción nasal, estornudos frecuentes, congestión", "diagnosis": "Resfriado común"},

        # Problemas digestivos
        {"symptoms": "dolor abdominal severo, vómitos, diarrea", "diagnosis": "Gastroenteritis"},
        {"symptoms": "acidez, dolor en la parte superior del abdomen, sensación de ardor", "diagnosis": "Reflujo gástrico"},
        {"symptoms": "estreñimiento, hinchazón abdominal, dolor al evacuar", "diagnosis": "Síndrome de intestino irritable"},
        {"symptoms": "dolor abdominal intenso, náuseas, fiebre", "diagnosis": "Apendicitis"},

        # Enfermedades cardíacas
        {"symptoms": "dolor en el pecho, dificultad para respirar, sudoración", "diagnosis": "Ataque al corazón"},
        {"symptoms": "palpitaciones, mareo, falta de aire", "diagnosis": "Arritmia cardíaca"},
        {"symptoms": "hinchazón en las piernas, cansancio, falta de aire", "diagnosis": "Insuficiencia cardíaca"},

        # Problemas musculoesqueléticos
        {"symptoms": "dolor muscular, fiebre, cansancio extremo", "diagnosis": "Gripe"},
        {"symptoms": "hinchazón, dificultad para caminar, dolor intenso en la articulación", "diagnosis": "Artritis"},
        {"symptoms": "dolor en la espalda baja, rigidez, dificultad para moverse", "diagnosis": "Lumbalgia"},
        {"symptoms": "dolor en la muñeca, entumecimiento, hormigueo", "diagnosis": "Síndrome del túnel carpiano"},
        {"symptoms": "dolor en el cuello, mareo, rigidez muscular", "diagnosis": "Cervicalgia"},

        # Enfermedades metabólicas
        {"symptoms": "pérdida de peso, cansancio, sed excesiva", "diagnosis": "Diabetes"},
        {"symptoms": "fatiga, piel seca, aumento de peso, intolerancia al frío", "diagnosis": "Hipotiroidismo"},
        {"symptoms": "irritabilidad, pérdida de peso, sudoración excesiva", "diagnosis": "Hipertiroidismo"},

        # Enfermedades hematológicas
        {"symptoms": "sangrado nasal frecuente, hematomas, debilidad", "diagnosis": "Leucemia"},
        {"symptoms": "palidez, fatiga, mareos, dificultad para concentrarse", "diagnosis": "Anemia"},

        # Enfermedades renales
        {"symptoms": "dolor de espalda, dificultad para orinar, sangre en la orina", "diagnosis": "Cálculos renales"},
        {"symptoms": "hinchazón en piernas y cara, disminución de la micción", "diagnosis": "Insuficiencia renal"},

        # Problemas neurológicos
        {"symptoms": "dolor de cabeza intenso, sensibilidad a la luz, náuseas", "diagnosis": "Migraña"},
        {"symptoms": "entumecimiento en un lado del cuerpo, dificultad para hablar, pérdida de visión", "diagnosis": "Accidente cerebrovascular"},
        {"symptoms": "temblores, rigidez muscular, lentitud de movimientos", "diagnosis": "Parkinson"},

        # Enfermedades infecciosas
        {"symptoms": "fiebre, dolor de garganta, inflamación de ganglios", "diagnosis": "Mononucleosis infecciosa"},
        {"symptoms": "fiebre, sarpullido, dolor en las articulaciones", "diagnosis": "Dengue"},
        {"symptoms": "fiebre, escalofríos, sudoración nocturna, fatiga", "diagnosis": "Tuberculosis"},
        {"symptoms": "úlceras bucales dolorosas, fiebre, ganglios inflamados", "diagnosis": "Herpes oral"},

        # Problemas crónicos
        {"symptoms": "mareo, visión borrosa, dolor de cabeza intenso", "diagnosis": "Hipertensión"},
        {"symptoms": "tos persistente, flema, dificultad para respirar", "diagnosis": "EPOC (Enfermedad Pulmonar Obstructiva Crónica)"},
        {"symptoms": "cansancio extremo, falta de motivación, insomnio", "diagnosis": "Depresión"},
        {"symptoms": "ansiedad, sudoración, sensación de opresión en el pecho", "diagnosis": "Trastorno de ansiedad"},

        # Otras enfermedades
        {"symptoms": "pérdida de cabello, piel seca, fatiga", "diagnosis": "Alopecia"},
        {"symptoms": "manchas rojas en la piel, picazón, hinchazón", "diagnosis": "Dermatitis"},
        {"symptoms": "tos seca, dificultad para respirar, opresión en el pecho", "diagnosis": "Asma"}
    ]
    return pd.DataFrame(data)

# Entrenar el modelo
def train_model():
    data = generate_data()
    X = data["symptoms"]
    y = data["diagnosis"]

    # Verificar el número mínimo de ejemplos por clase
    min_class_count = data['diagnosis'].value_counts().min()
    if min_class_count < 2:
        print(f"Advertencia: Hay clases con menos de 2 ejemplos. Usando alpha=1.0 directamente.")
        use_grid_search = False
    else:
        use_grid_search = True

    # Dividir en conjunto de entrenamiento y prueba
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Configurar el vectorizador
    vectorizer = TfidfVectorizer(
        max_features=2000,
        ngram_range=(1, 2),
        stop_words=spanish_stopwords,
        sublinear_tf=True
    )
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)

    if use_grid_search:
        # Configurar Grid Search para optimizar Naive Bayes
        parameters = {'alpha': [0.1, 0.5, 1.0, 2.0]}
        grid_search = GridSearchCV(MultinomialNB(), parameters, cv=2, scoring='accuracy')  # cv mínimo = 2
        grid_search.fit(X_train_tfidf, y_train)

        # Mejor modelo encontrado
        best_model = grid_search.best_estimator_
        print("Mejor valor de alpha:", grid_search.best_params_)
    else:
        # Entrenar directamente sin Grid Search
        best_model = MultinomialNB(alpha=1.0)
        best_model.fit(X_train_tfidf, y_train)
        print("Modelo entrenado directamente con alpha=1.0")

    # Evaluar el modelo
    y_pred = best_model.predict(X_test_tfidf)
    print(classification_report(y_test, y_pred))

    # Guardar el modelo y el vectorizador
    with open("informe_analysis_model.pkl", "wb") as file:
        pickle.dump((vectorizer, best_model), file)

    print("Modelo y vectorizador guardados correctamente.")

if __name__ == "__main__":
    train_model()