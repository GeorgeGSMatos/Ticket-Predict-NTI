"""
Modelagem Preditiva e Validação Estatística.
"""

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import TimeSeriesSplit
import xgboost as xgb

class ModelEvaluator:
    """Implementa a infraestrutura de validação MLOps cruzada pelo tempo.
    
    Attributes:
        n_splits (int): Quantidade de cortes na validação cruzada.
        target_col (str): Coluna contendo o alvo para predição.
    """
    def __init__(self, n_splits: int = 5, target_col: str = "Volume_Global"):
        self.tscv = TimeSeriesSplit(n_splits=n_splits)
        self.target_col = target_col

    def evaluate_baseline(self, df: pd.DataFrame, window: int = 7) -> dict:
        """Avalia a regressão de baseline clássica SMA.
        
        Args:
            df (pd.DataFrame): Dados Gold.
            window (int): Janela da média móvel.
            
        Returns:
            dict: Métricas agregadas RMSE e MAE do baseline.
        """
        df_eval = df.copy()
        df_eval[f"Baseline_SMA_{window}"] = (
            df_eval[self.target_col].shift(1).rolling(window=window).mean()
        )
        df_eval.dropna(inplace=True)

        target_hist = df_eval[self.target_col]
        predictions_sma = df_eval[f"Baseline_SMA_{window}"]

        rmse_scores, mae_scores = [], []
        predictions_total = pd.Series(index=df_eval.index, dtype=float)

        for train_index, test_index in self.tscv.split(df_eval):
            y_truth = target_hist.iloc[test_index]
            y_forecast = predictions_sma.iloc[test_index]

            rmse_scores.append(np.sqrt(mean_squared_error(y_truth, y_forecast)))
            mae_scores.append(mean_absolute_error(y_truth, y_forecast))
            predictions_total.iloc[test_index] = y_forecast

        return {
            "model_name": f"Baseline_SMA_{window}",
            "mean_rmse": np.mean(rmse_scores),
            "mean_mae": np.mean(mae_scores),
            "predictions": predictions_total.dropna(),
            "truth": target_hist.loc[predictions_total.dropna().index]
        }

    def evaluate_xgboost(self, df: pd.DataFrame, features: list) -> dict:
        """Treina e valida um modelo XGBoost utilizando o histórico sequencial.
        
        Args:
            df (pd.DataFrame): Dados Gold preenchidos com features temporais.
            features (list): Lista com variáveis previsoras.
            
        Returns:
            dict: Métricas do modelo avançado.
        """
        df_eval = df.copy().dropna()
        target = df_eval[self.target_col]
        x_data = df_eval[features]

        rmse_scores, mae_scores = [], []
        predictions_total = pd.Series(index=df_eval.index, dtype=float)

        model = xgb.XGBRegressor(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=4,
            random_state=42,
            objective="reg:squarederror"
        )

        for train_index, test_index in self.tscv.split(df_eval):
            X_train, X_test = x_data.iloc[train_index], x_data.iloc[test_index]
            y_train, y_test = target.iloc[train_index], target.iloc[test_index]

            model.fit(X_train, y_train)
            y_forecast = model.predict(X_test)

            rmse_scores.append(np.sqrt(mean_squared_error(y_test, y_forecast)))
            mae_scores.append(mean_absolute_error(y_test, y_forecast))
            predictions_total.iloc[test_index] = y_forecast

        return {
            "model_name": "XGBoost",
            "mean_rmse": np.mean(rmse_scores),
            "mean_mae": np.mean(mae_scores),
            "predictions": predictions_total.dropna(),
            "truth": target.loc[predictions_total.dropna().index]
        }
