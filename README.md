# Ticket Predict: Inteligência Artificial no Capacity Planning do NTI

## Capa
![Capa](./assets/capa.png)

## 📌 Problema de Negócio
No mundo corporativo, o Suporte de TI / NTI (Núcleo de Tecnologia da Informação) frequentemente atua de forma reativa, tornando-se refém de demandas logísticas imprevisíveis. Esse modelo reativo gera picos de chamados que causam:
- Estresse e *burnout* devido à sobrecarga inesperada da equipe;
- Quebra aguda nos SLAs (Acordos de Nível de Serviço);
- Despesas ocultas drásticas com banco de horas e *overtime* da equipe técnica.

Nesse cenário, a equipe técnica e gerencial gasta a maior parte do expediente atuando como "bombeiros" para apagar incêndios operacionais, em vez de alocar tempo para melhorias sistêmicas e garantia da qualidade.

## 🎯 Objetivo do Projeto
Transformar o suporte do NTI de uma central reativa padrão da indústria para um modelo operacional **Proativo**, focado em *Capacity Planning* preditivo de ponta a ponta (do Data Prep ao Deploy).

O objetivo macro do modelo preditivo (MLOps) é antecipar de forma estatística:
1. **O Volume Diário de Chamados Esperados.**
2. **A Carga de Trabalho Total Estimada (Workload em horas alocadas para o dia).**

## 🏗️ Estratégia da Solução
A fundação da arquitetura lógica foi desenhada seguindo as regras de ouro da Engenharia de Software (SOLID e DRY), unidas ao rigor das proteções sistêmicas para Aprendizado de Máquina (prevenção contra *Data Leakage*). O pipeline consumiu dados tabulares contínuos de ITSM do ServiceNow e foi estruturado da seguinte forma:

* **Pipeline em Medallion Architecture:**
    * **Bronze:** Extração bruta, garantindo a ingestão e o versionamento dos dados originais.
    * **Silver:** Limpeza e transformação. Features temporais foram convertidas em dimensões *Cíclicas Trigonométricas*. Ocorreu também o agrupamento dinâmico de categorias de cauda longa (Rare Label Encoding) e a imputação de prioridades baseada na matriz de negócio ITIL.
    * **Gold:** Transformação de dados transacionais (linhas independentes) em Séries Temporais contínuas (*Resampling* diário multi-target), garantindo a integridade temporal mesmo em dias sem chamados (Feriados/Domigos).
* **Abordagem Preditiva Focada em Negócios:** O forecasting utilizou uma separação estratégica de métricas. O `RMSE` foi utilizado para penalização matemática rigorosa de erros graves (picos inesperados), enquanto o `MAE` foi estabelecido como a régua de comunicação gerencial com a Diretoria e o C-Level.

## 🛠️ Tecnologias Utilizadas
* **Linguagem:** Python 3.12+
* **Manipulação de Dados (ETL Vetorizado):** Pandas, NumPy
* **Gestão de Configuração e Governança:** PyYAML
* **Machine Learning / Cross Validation:** Scikit-Learn (`TimeSeriesSplit`, `Pipeline`)
* **Time Series Analytics:** Statsmodels (`seasonal_decompose`, `ACF/PACF`)
* **Data Visualization:** Matplotlib, Seaborn
* **Infraestrutura e Ambiente:** Docker, Python `venv`

## 🛤️ Etapas do Projeto
1. **Ingestão e Tipagem:** Leitura otimizada O(N) de grandes volumes de dados brutos.
2. **Data Cleansing Vetorial:** Tratamento de valores nulos, categorização estrita de features e *Dynamic Encoding*.
3. **Deep EDA (Física do Tempo):** Análise de Autocorrelação (ACF/PACF) e decomposição estatística para mapear tendências e sazonalidades ocultas no NTI.

    ![Geometria da Demanda NTI](./assets/heatmap_sazonalidade.png)

4. **Estabelecimento de Benchmark (Modelo Baseline):** Construção de um modelo *Naive* (Média Móvel Simples - SMA) como régua de performance mínima. Implementação rigorosa de janelas deslizantes `.shift(1)` combinadas com `.rolling()` para blindagem contra vazamento de dados do futuro (*Data Leakage*).

## 💡 Principais Insights e Próximos Passos

![Importância das Features no Modelo](./assets/feature_importance.png)

* **A Volatilidade Extrema do Help Desk:** A análise estatística e a validação cruzada do Baseline comprovaram que a demanda do NTI não segue uma distribuição normal estável. O desvio padrão é significativamente maior que a média (alta volatilidade). Modelos lineares sofrem com "atraso de percepção" retroativo e falham em prever crises.
* **A Necessidade de IA Avançada:** A métrica de erro gerada pelo Baseline provou matematicamente a ineficiência de ferramentas analíticas simples. Esse resultado justifica técnica e financeiramente a transição para algoritmos baseados em árvores (*Tree-based Models*, como o XGBoost), que são capazes de antecipar picos através do cruzamento complexo de features temporais (Lags) e limites operacionais.

## 📊 Resultados e Conclusão

![Gráfico de Resultados Preditivos](./assets/resultados.png)

A fundação computacional construída isolou os gargalos de dados do ecossistema original de ITSM e gerou a Régua Base (Benchmark RMSE/MAE). Com o pipeline preditivo estruturado contra *Data Leakage* e validado por `TimeSeriesSplit`, o projeto atinge um estado maduro e seguro para implantação. A infraestrutura agora está pronta para acolher algoritmos avançados, permitindo escalar previsões com segurança sistêmica, otimizar orçamentos futuros e gerar economia real por meio da redução de horas gerenciais e operacionais reativas.
