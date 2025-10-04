from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
import os

def train_and_save_model():
    """Train a simple ML model for Lambda inference"""
    
    # Load iris dataset
    print("Loading iris dataset...")
    iris = load_iris()
    X, y = iris.data, iris.target
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train RandomForest model
    print("Training RandomForest model...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=5,
        random_state=42
    )
    model.fit(X_train, y_train)
    
    # Evaluate
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    print(f"Train accuracy: {train_score:.4f}")
    print(f"Test accuracy: {test_score:.4f}")
    
    # Save model to src folder
    model_path = os.path.join('src', 'model.joblib')
    joblib.dump(model, model_path)
    print(f"Model saved to: {model_path}")
    
    return model

if __name__ == "__main__":
    train_and_save_model()
