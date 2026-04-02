"""
Conjunto de Extratores, Limpadores e Agregadores de Séries Temporais para ITSM.
"""

import warnings
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import yaml
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import TimeSeriesSplit
import statsmodels.api as sm
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import os

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid")


def load_bronze_data(file_path: str) -> pd.DataFrame:
    """Carrega dados da camada bronze para avaliação in natura.

    Args:
        file_path (str): Caminho para o arquivo CSV referenciado.

    Returns:
        pd.DataFrame: Tabela contendo os dados brutos.

    Raises:
        FileNotFoundError: Interrompe execuções subsequentes na falha.
    """
    try:
        return pd.read_csv(file_path, encoding="latin1", low_memory=False)
    except FileNotFoundError as error:
        raise FileNotFoundError(
            f"Arquivo de dados não acessível: {file_path}"
        ) from error


class TemporalFeaturesExtractor:
    """Extrai e consolida informações periódicas provenientes dos logs de ticket.

    Attributes:
        time_columns (list): Relatório das colunas marcadas contendo as referências originais.
        expected_format (str): Estruturação de data garantida no parsing.
    """

    def __init__(
        self, time_columns: list, expected_format: str = "%d/%m/%Y %H:%M"
    ) -> None:
        self.time_columns = time_columns
        self.expected_format = expected_format

    def standardize_datetimes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpa irregularidades textuais das cronometragens originais.

        Args:
            df (pd.DataFrame): Dados Silver-to-be contendo datas não-tipadas.

        Returns:
            pd.DataFrame: Resultado tipado explicitamente via datetime.
        """
        df_silver = df.copy()
        for col in self.time_columns:
            if col in df_silver.columns:
                padronizado = df_silver[col].astype(str).str.replace("-", "/")
                df_silver[col] = pd.to_datetime(
                    padronizado, format=self.expected_format, errors="coerce"
                )
        return df_silver

    def add_cyclical_features(self, df: pd.DataFrame, target_col: str) -> pd.DataFrame:
        """Inclui dimensões trigonométricas modeladas via características cíclicas.

        Args:
            df (pd.DataFrame): DataFrame tratado inicialmente.
            target_col (str): Foco base principal para cálculos de amplitude temporal.

        Returns:
            pd.DataFrame: Tabela adaptada com atributos trigonométricos mensais e diários.
        """
        df_silver = df.copy()
        if target_col in df_silver.columns:
            valid_idx = df_silver[df_silver[target_col].notnull()].index
            time_series = df_silver.loc[valid_idx, target_col]

            mes_radiano = 2 * np.pi * time_series.dt.month / 12
            semana_radiano = 2 * np.pi * time_series.dt.dayofweek / 7

            df_silver.loc[valid_idx, f"{target_col}_month_sin"] = np.sin(mes_radiano)
            df_silver.loc[valid_idx, f"{target_col}_month_cos"] = np.cos(mes_radiano)
            df_silver.loc[valid_idx, f"{target_col}_dow_sin"] = np.sin(semana_radiano)
            df_silver.loc[valid_idx, f"{target_col}_dow_cos"] = np.cos(semana_radiano)

        return df_silver


class DataCleaner:
    """Agrupador logístico para validação unificada sobre dados inconsistentes.

    Attributes:
        config (dict): Dicionário populado via arquivos .yaml injetados.
        priority_matrix (dict): Dicionário de peso inferente sobre matriz impacto/urgência.
        rare_threshold (float): Proporção para classificar valores em tail distribution (cauda longa).
    """

    def __init__(self, config_path: str) -> None:
        with open(config_path, "r", encoding="utf-8") as file:
            self.config = yaml.safe_load(file)
        self.priority_matrix = self.config["business_rules"][
            "priority_imputation_matrix"
        ]
        self.rare_threshold = self.config["business_rules"].get(
            "rare_labels_threshold", 0.05
        )

    def impute_priority_with_matrix(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preenche prioridades de maneira implícita quando existem campos auxiliares preenchidos.

        Args:
            df (pd.DataFrame): Dados imperfeitos de operação primária.

        Returns:
            pd.DataFrame: Resultado complementado das prioridades faltantes.
        """
        df_silver = df.copy()
        if all(col in df_silver.columns for col in ["Priority", "Impact", "Urgency"]):
            chave_composta = (
                df_silver["Impact"].astype(str) + "_" + df_silver["Urgency"].astype(str)
            )
            valores_inferidos = chave_composta.map(self.priority_matrix)
            df_silver["Priority"] = df_silver["Priority"].fillna(valores_inferidos)
        return df_silver

    def group_rare_categories(
        self, df: pd.DataFrame, categorical_columns: list
    ) -> pd.DataFrame:
        """Desfaz granularidades não-treináveis em rótulos menos frequentes (estag. other).

        Args:
            df (pd.DataFrame): Informações textuais/categóricas puras.
            categorical_columns (list): Lista representativa destas colunas que necessitem de reajuste.

        Returns:
            pd.DataFrame: Dados menos fragmentados.
        """
        df_silver = df.copy()
        for col in categorical_columns:
            if col in df_silver.columns:
                frequencies = df_silver[col].value_counts(normalize=True)
                rare_labels = frequencies[frequencies < self.rare_threshold].index
                df_silver.loc[df_silver[col].isin(rare_labels), col] = "other"
        return df_silver

    def drop_noise_columns(
        self, df: pd.DataFrame, columns_to_drop: list
    ) -> pd.DataFrame:
        """Reduz largura transacional com a elisão de dados inúteis.

        Args:
            df (pd.DataFrame): Frame com excesso de informação irrelevante.
            columns_to_drop (list): Colunas categorizadas como não úteis.

        Returns:
            pd.DataFrame: Novo esqueleto limpo.
        """
        existing_cols = [col for col in columns_to_drop if col in df.columns]
        return df.drop(columns=existing_cols)

    def clean_handle_time(
        self, df: pd.DataFrame, time_col: str = "Handle_Time_hrs"
    ) -> pd.DataFrame:
        """Assegura representabilidade fracional e coesa para métricas de eficiência local/humana.

        Args:
            df (pd.DataFrame): Conjunto com durações atreladas.
            time_col (str): O cabeçalho dos tempos dedicados em chamados.

        Returns:
            pd.DataFrame: Colunas adaptadas ao formato tipo Float.
        """
        df_silver = df.copy()
        if time_col in df_silver.columns:
            df_silver[time_col] = df_silver[time_col].astype(str).str.replace(",", ".")
            df_silver[time_col] = pd.to_numeric(df_silver[time_col], errors="coerce")
        return df_silver


class TimeSeriesAggregator:
    """Converte o mar de registros pontuais em métricas sequenciais para séries diárias.

    Attributes:
        time_index_col (str): Teto do índice principal a ser colapsado diuturnamente.
        freq (str): Padrão adotado da frequência estatística (padrão 'D').
    """

    def __init__(self, time_index_col: str, freq: str = "D") -> None:
        self.time_index_col = time_index_col
        self.freq = freq

    def generate_global_pulse(self, df: pd.DataFrame) -> pd.DataFrame:
        """Realiza aglutinação bruta garantindo zeramento no hiato de dados.

        Args:
            df (pd.DataFrame): Instâncias contendo tempo demarcado.

        Returns:
            pd.DataFrame: Relatório indexável com base sequencial (série temporal forte).
        """
        df_gold = df.copy()
        grouper = pd.Grouper(key=self.time_index_col, freq=self.freq)

        aggregated = df_gold.groupby(grouper).agg(
            Volume_Global=("Incident_ID", "count"),
            Workload_Global=("Handle_Time_hrs", "sum"),
        )
        return aggregated.asfreq(self.freq).fillna(0)

    def generate_hierarchical_pulse(
        self, df: pd.DataFrame, grouping_col: str = "Category"
    ) -> pd.DataFrame:
        """Reparte e refrige dados isolando domínios/categorias no modelo.

        Args:
            df (pd.DataFrame): Base pronta (silver layer pivot).
            grouping_col (str): Atributo categórico principal.

        Returns:
            pd.DataFrame: Resposta esmagada e adaptada a vetores esparsos (flatten columns).
        """
        df_gold = df.copy()
        group_keys = [pd.Grouper(key=self.time_index_col, freq=self.freq), grouping_col]

        multi_index_df = (
            df_gold.groupby(group_keys)
            .agg(Volume=("Incident_ID", "count"), Workload=("Handle_Time_hrs", "sum"))
            .unstack(fill_value=0)
        )
        multi_index_df = multi_index_df.asfreq(self.freq).fillna(0)
        multi_index_df.columns = [
            f"{metric}_{categ}" for metric, categ in multi_index_df.columns
        ]
        return multi_index_df
