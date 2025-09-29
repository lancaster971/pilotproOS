#!/usr/bin/env python3
"""
Train ML Classifier for Smart LLM Router
Trains the model with real query examples
"""
import pickle
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import os

# Training data with real examples
TRAINING_DATA = [
    # FREE tier queries (Groq)
    ("Ciao", "groq_free"),
    ("Buongiorno", "groq_free"),
    ("Come stai?", "groq_free"),
    ("Salve", "groq_free"),
    ("Arrivederci", "groq_free"),
    ("Grazie", "groq_free"),
    ("Prego", "groq_free"),
    ("OK", "groq_free"),
    ("Sì", "groq_free"),
    ("No", "groq_free"),

    # FREE tier queries (Gemini for batch)
    ("Elenca tutti i processi", "gemini_free"),
    ("Mostra tutte le elaborazioni", "gemini_free"),
    ("Lista completa dei messaggi", "gemini_free"),
    ("Tutti i workflow attivi", "gemini_free"),
    ("Elenco delle anomalie", "gemini_free"),

    # SPECIAL NANO tier (message extraction)
    ("Mostra ultimo messaggio", "openai_nano"),
    ("Estrai messaggio dal workflow", "openai_nano"),
    ("Recupera messaggio webhook", "openai_nano"),
    ("Ultimo messaggio ricevuto", "openai_nano"),
    ("Messaggio del processo Fatture", "openai_nano"),
    ("Dammi il messaggio più recente", "openai_nano"),

    # SPECIAL MINI tier (analysis)
    ("Analizza i dati del mese", "openai_mini"),
    ("Genera report dettagliato", "openai_mini"),
    ("Statistiche delle elaborazioni", "openai_mini"),
    ("Confronta performance mensili", "openai_mini"),
    ("Trend analysis dei processi", "openai_mini"),
    ("Metriche di sistema", "openai_mini"),

    # PREMIUM tier (complex)
    ("Analizza tutti i messaggi degli ultimi 30 giorni e genera un report dettagliato con trend analysis", "premium"),
    ("Crea dashboard completo con KPI, metriche e previsioni", "premium"),
    ("Ottimizza tutti i processi e suggerisci miglioramenti", "premium"),
    ("Diagnosi completa del sistema con raccomandazioni", "premium"),

    # More examples for better training
    ("Come va il sistema oggi?", "groq_free"),
    ("Status operativo", "groq_free"),
    ("Ci sono problemi?", "groq_free"),
    ("Quante elaborazioni oggi?", "openai_mini"),
    ("Messaggi non letti", "openai_nano"),
    ("Errori nelle ultime ore", "openai_mini"),
    ("Processi falliti", "openai_mini"),
    ("Webhook ricevuti oggi", "openai_nano"),
    ("Performance del sistema", "openai_mini"),
    ("Backup completato?", "groq_free"),
    ("Aiuto", "groq_free"),
    ("Cosa puoi fare?", "groq_free"),
    ("Mostrami i log", "gemini_free"),
    ("Tutti gli utenti attivi", "gemini_free"),
    ("Report settimanale", "openai_mini"),
    ("Dashboard real-time", "premium"),
    ("Configurazione sistema", "openai_mini"),
    ("Test connessione", "groq_free"),
    ("Ping", "groq_free"),
    ("Version", "groq_free"),
]

def extract_features(query):
    """Extract features from a query"""
    features = {
        'length': len(query),
        'word_count': len(query.split()),
        'has_greeting': any(g in query.lower() for g in ['ciao', 'buongiorno', 'salve']),
        'has_message': 'messaggio' in query.lower() or 'message' in query.lower(),
        'has_workflow': 'workflow' in query.lower() or 'processo' in query.lower(),
        'has_analysis': any(a in query.lower() for a in ['analizza', 'report', 'statistic']),
        'has_all': 'tutti' in query.lower() or 'tutte' in query.lower() or 'all' in query.lower(),
        'has_question': '?' in query,
        'has_number': any(c.isdigit() for c in query),
        'complexity_score': len(query.split()) * len(query) / 100,
    }
    return features

def train_classifier():
    """Train the ML classifier"""
    print("Training ML Classifier for Smart LLM Router")
    print("=" * 60)

    # Prepare data
    queries = [q for q, _ in TRAINING_DATA]
    labels = [l for _, l in TRAINING_DATA]

    # Create label mapping
    unique_labels = list(set(labels))
    label_to_idx = {label: idx for idx, label in enumerate(unique_labels)}
    idx_to_label = {idx: label for label, idx in label_to_idx.items()}

    # Convert labels to indices
    y = [label_to_idx[label] for label in labels]

    # Extract features
    print("\nExtracting features...")
    X_features = [list(extract_features(q).values()) for q in queries]

    # Create TF-IDF features
    tfidf = TfidfVectorizer(max_features=50, ngram_range=(1, 2))
    X_tfidf = tfidf.fit_transform(queries).toarray()

    # Combine features
    X = np.hstack([X_features, X_tfidf])

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )

    # Train model
    print("Training LogisticRegression model...")
    model = LogisticRegression(
        multi_class='ovr',
        max_iter=1000,
        random_state=42,
        C=1.0
    )
    model.fit(X_train, y_train)

    # Evaluate
    print("\nModel Performance:")
    print("-" * 40)
    y_pred = model.predict(X_test)

    # Calculate accuracy
    accuracy = (y_pred == y_test).mean()
    print(f"Accuracy: {accuracy:.2%}")

    # Detailed classification report
    print("\nDetailed Classification Report:")
    print(classification_report(
        y_test, y_pred,
        target_names=unique_labels,
        zero_division=0
    ))

    # Save models
    os.makedirs('models', exist_ok=True)

    # Save classifier
    with open('models/query_classifier.pkl', 'wb') as f:
        pickle.dump({
            'model': model,
            'scaler': scaler,
            'tfidf': tfidf,
            'label_to_idx': label_to_idx,
            'idx_to_label': idx_to_label
        }, f)

    print("\n✓ Model saved to models/query_classifier.pkl")

    # Test with examples
    print("\n" + "=" * 60)
    print("Testing with new queries:")
    print("-" * 40)

    test_queries = [
        "Ciao Milhena",
        "Mostra ultimo messaggio del workflow",
        "Analizza tutti i dati e genera report",
        "Come stai oggi?"
    ]

    for query in test_queries:
        # Extract features
        features = list(extract_features(query).values())
        tfidf_features = tfidf.transform([query]).toarray()[0]
        combined = np.hstack([features, tfidf_features]).reshape(1, -1)
        scaled = scaler.transform(combined)

        # Predict
        prediction = model.predict(scaled)[0]
        confidence = model.predict_proba(scaled).max()

        predicted_label = idx_to_label[prediction]
        print(f"\nQuery: '{query}'")
        print(f"Predicted: {predicted_label}")
        print(f"Confidence: {confidence:.2%}")

    print("\n✓ Training completed successfully!")

if __name__ == "__main__":
    train_classifier()