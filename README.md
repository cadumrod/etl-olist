# 🇧🇷 Olist End-to-End Data Pipeline

![Python](https://img.shields.io/badge/Python-3.10-blue?style=for-the-badge&logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-24.0-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Postgres](https://img.shields.io/badge/PostgreSQL-15-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-EC2-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)

## 📋 Sobre o Projeto

Este projeto consiste em uma **Plataforma de Engenharia de Dados** completa, desenhada para ingerir, processar e analisar dados do E-commerce brasileiro (Dataset público Olist).

O objetivo de negócio é centralizar informações dispersas para gerar **KPIs Logísticos e Financeiros** (com conversão multimoeda), simulando um ambiente corporativo real com sistemas legados e fontes externas.

### 🏗️ Arquitetura da Solução

O pipeline segue a **Arquitetura Medalhão (Medallion Architecture)** e integra três tipos distintos de fontes de dados:

1.  **Arquivos Flat (CSV):** Logs de vendas e dados de clientes (Olist).
2.  **Banco de Dados Relacional (Postgres):** Simulação de um **ERP** contendo regras fiscais (tabela de impostos).
3.  **API Externa (Web):** Consumo de API de Câmbio em tempo real para cálculo de faturamento em Dólar.

```mermaid
graph TD;
    A[📄 CSVs Olist] -->|Ingestão| D[🐍 Python ETL Container];
    B[🗄️ ERP Postgres] -->|Query SQL| D;
    C[🌐 API Câmbio] -->|Request JSON| D;
    D -->|Load Raw| E[(🥉 Bronze Schema)];
    E -->|Clean & Join| F[(🥈 Silver Schema)];
    F -->|Aggregate| G[(🥇 Gold Schema)];

🛠️ Tech Stack

    Linguagem: Python 3.10

    Orquestração & Infra: Docker & Docker Compose

    Banco de Dados: PostgreSQL 15 (Containers isolados para ERP e DW)

    Bibliotecas Principais: Pandas, SQLAlchemy, Requests, Psycopg2

    Cloud: AWS EC2 (Ubuntu Linux)

📸 Evidências de Execução (Deploy na AWS)

O projeto foi implantado e executado com sucesso em uma instância EC2 na AWS, comprovando a portabilidade da infraestrutura Docker.

1. Infraestrutura Provisionada (EC2)

Servidor Linux Ubuntu rodando na região us-east-1.

2. Orquestração de Containers

Três serviços rodando simultaneamente: Aplicação ETL, Banco ERP (Origem) e Banco DW (Destino).

3. Pipeline em Execução

Log do processamento ETL, demonstrando conexão com API, Extração SQL e Carga.

4. Resultado Final (Banco de Dados Gold)

Dados agregados e monetariamente formatados disponíveis no Data Warehouse na nuvem.

🚀 Como Executar

Pré-requisitos

    Docker e Docker Compose instalados.

    Git.

Passo a Passo

    Clone o repositório:
    Bash

git clone [https://github.com/SEU_USUARIO/etl-olist.git](https://github.com/SEU_USUARIO/etl-olist.git)
cd etl-olist

Adicione os Dados:

    Baixe o dataset do Olist no Kaggle.

    Coloque os arquivos .csv na pasta data/raw/.

Suba a Infraestrutura:
Bash

docker compose up -d --build

Inicialize os Bancos (Primeira vez apenas):

    É necessário criar as tabelas no ERP e os schemas no DW.

    Utilize os scripts contidos na pasta sql/ (init_erp.sql e init_dw.sql) via cliente SQL ou linha de comando.

Execute o Pipeline:

    Se estiver usando VS Code Dev Container, apenas rode:

Bash

python src/etl.py

    Se estiver externo:

Bash

    docker exec olist_app_etl python src/etl.py

👨‍💻 Autor

Cadu Engenheiro de Dados em Transição de Carreira Focado em construção de pipelines robustos, arquitetura de dados e cloud computing.