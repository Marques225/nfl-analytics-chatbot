import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import joblib
import os
from database import engine
from sqlalchemy import text  # <--- Essential Import

MODEL_PATH = "backend/ml/fantasy_model.pkl"

class FantasyPredictor:
    def __init__(self):
        self.model = None
        self.is_trained = False

    def train(self):
        print("🧠 Training Predictive Model...")
        
        # --- THE FIX IS HERE ---
        # We wrap the string in text() to make it "executable" for SQLAlchemy 2.0
        query = text("SELECT * FROM season_stats")
        
        try:
            with engine.connect() as connection:
                df = pd.read_sql(query, connection)
        except Exception as e:
            print(f"❌ Database Error during training: {e}")
            return

        if df.empty:
            print("⚠️ No data to train on!")
            return

        # 2. Prepare Features (X) and Target (y)
        features = ['passing_yards', 'passing_tds', 'rushing_yards', 'rushing_tds', 'receiving_yards', 'receptions']
        target = 'fantasy_points'
        
        # Fill NaNs
        df = df.fillna(0)
        
        # Ensure columns exist before training
        missing_cols = [col for col in features if col not in df.columns]
        if missing_cols:
            print(f"❌ Missing columns for training: {missing_cols}")
            return

        X = df[features]
        y = df[target]

        # 3. Train Model
        self.model = LinearRegression()
        self.model.fit(X, y)
        self.is_trained = True
        
        print("✅ Model Trained Successfully!")
        print(f"   Coefficients: {self.model.coef_}")

    def predict_next_game(self, player_stats):
        """
        Predicts 'Next Game' points based on a player's season averages.
        """
        if not self.is_trained:
            self.train()
            
        if not self.is_trained: # If training failed
            return 0.0
            
        # Estimate 'Per Game' stats for the prediction.
        games_played_est = 17 
        
        # Safe fetch with defaults
        input_data = pd.DataFrame([{
            'passing_yards': float(player_stats.get('passing_yards', 0) or 0) / games_played_est,
            'passing_tds': float(player_stats.get('passing_tds', 0) or 0) / games_played_est,
            'rushing_yards': float(player_stats.get('rushing_yards', 0) or 0) / games_played_est,
            'rushing_tds': float(player_stats.get('rushing_tds', 0) or 0) / games_played_est,
            'receiving_yards': float(player_stats.get('receiving_yards', 0) or 0) / games_played_est,
            'receptions': float(player_stats.get('receptions', 0) or 0) / games_played_est
        }])
        
        # Predict
        try:
            prediction = self.model.predict(input_data)[0]
            return round(prediction, 2)
        except Exception as e:
            print(f"❌ Prediction Error: {e}")
            return 0.0

# Global Instance
predictor = FantasyPredictor()