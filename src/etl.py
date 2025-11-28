import pandas as pd
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool # Utilizado para gerenciar o pool de conexões. Evita travamento.
import requests

import warnings # Ignorar avisos do pandas de limpar terminal
warnings.filterwarnings("ignore")


# Conexões
def criar_conexoes():
    # Lê as variáveis de ambiente, cria as engines e testa a conexão
    print("### Configurando e Testando Conexões ###")

    # Configurar Credenciais
    DW_USER = os.getenv('DW_USER', 'postgres')
    DW_PASS = os.getenv('DW_PASS', 'postgres')
    DW_HOST = os.getenv('DW_HOST', 'db_dw')
    DW_NAME = os.getenv('DW_NAME', 'olist_dw')

    ERP_USER = os.getenv('ERP_USER', 'postgres')
    ERP_PASS = os.getenv('ERP_PASS', 'postgres')
    ERP_HOST = os.getenv('ERP_HOST', 'db_erp')
    ERP_NAME = os.getenv('ERP_NAME', 'olist_erp')

    # Montar URLs
    URL_DW = f"postgresql://{DW_USER}:{DW_PASS}@{DW_HOST}:5432/{DW_NAME}"
    URL_ERP = f"postgresql://{ERP_USER}:{ERP_PASS}@{ERP_HOST}:5432/{ERP_NAME}"

    # Criar Engines
    engine_dw = create_engine(URL_DW, poolclass=NullPool)
    engine_erp = create_engine(URL_ERP, poolclass=NullPool)

    # Health Check
    try:
        with engine_dw.connect() as conn:
            conn.execute(text("SELECT 1"))
            print("Conexão DW: OK")
        
        with engine_erp.connect() as conn:
            conn.execute(text("SELECT 1"))
            print("Conexão ERP: OK")
            
        return engine_dw, engine_erp

    except Exception as e:
        print(f"FALHA CRÍTICA DE CONEXÃO: {e}")
        sys.exit(1)

engine_dw, engine_erp = criar_conexoes()



# Funcões de extração ( Bronze )

def extrair_csv(caminho_pasta):
    print("\nExtraindo CSVs Locais...")

    try:
        arquivos = {
            'pedidos': 'olist_orders_dataset.csv',
            'itens': 'olist_order_items_dataset.csv',
            'clientes': 'olist_customers_dataset.csv',
            'produtos': 'olist_products_dataset.csv'
        }

        # Loop de verificação
        for chave, arquivo in arquivos.items():
            caminho_completo = os.path.join(caminho_pasta,
                                            arquivo)
            if not os.path.exists(caminho_completo):
                raise FileNotFoundError(
                    f"Arquivo não encontrado: {arquivo}"
                )
        
        # Leitura efetiva
        df_pedidos = pd.read_csv(os.path.join(caminho_pasta, arquivos['pedidos']))
        df_itens = pd.read_csv(os.path.join(caminho_pasta, arquivos['itens']))
        df_clientes = pd.read_csv(os.path.join(caminho_pasta, arquivos['clientes']))
        df_produtos = pd.read_csv(os.path.join(caminho_pasta, arquivos['produtos']))

        print(f"Pedidos carregados: {len(df_pedidos)}")
        return df_pedidos, df_itens, df_clientes, df_produtos
    
    except Exception as e:
        print(f"Erro nos CSVs: {e}")
        sys.exit(1)


def extrair_erp_impostos():
    # Busca a tabela de impostos via SQL
    print("\nExtraindo do ERP...")
    try:
        query = "SELECT * FROM category_taxes"
        df_impostos = pd.read_sql(query, engine_erp)
        print(f"Impostos carregados: {len(df_impostos)}")
        return df_impostos
    except Exception as e:
        print(f"Erro ao ler ERP: {e}")
        # Retornar DF vazio para não quebrar pipeline
        return pd.DataFrame()
    

def extrair_cotacao_dolar():
    # Extrai de API externa em USD-BRL
    print("\nExtraindo cotação de API...")
    try:
        url = "https://open.er-api.com/v6/latest/USD"
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            dados = response.json()
            bid = float(dados['rates']['BRL'])
            print(f"Dólar hoje: R${bid:.2f}")
            return bid
        else:
            print("API com erro. Usando valor fixo.")
            return 5.50
    except Exception as e:
        print(f"Falha na API: {e}. Usando fallback de 5.50")
        return 5.50
    



# Transformação ( Silver )
def processar_silver(df_pedidos, df_itens, df_produtos, df_clientes, df_impostos, valor_dolar):
    print(f"Processando silver...")

    # Garantindo formatação de datas
    cols_data = ['order_purchase_timestamp',
                 'order_approved_at',
                 'order_delivered_carrier_date',
                 'order_delivered_customer_date',
                 'order_estimated_delivery_date']
    
    for col in cols_data:
        # coerce para transformar error em NaT para evitar travamento
        df_pedidos[col] = pd.to_datetime(df_pedidos[col],
                                         errors='coerce')
    
    # Apenas os entregues
    df_vendas = df_pedidos[df_pedidos['order_status'] == 'delivered'].copy()

    # Merges com inner para manter apenas pedidos válidos
    df_final = df_vendas.merge(df_itens, on='order_id', how='inner')
    df_final = df_final.merge(df_produtos, on='product_id', how='inner')
    df_final = df_final.merge(df_clientes, on='customer_id', how='inner')

    # Impostos
    # left utilizado para caso o produto nao ter categoria,
    # manter a venda, mas com imposto vazio
    df_final = df_final.merge(df_impostos, left_on='product_category_name',right_on='category_name', how='left')

    # Tratando nulos para transformar em 0
    df_final['tax_rate'] = df_final['tax_rate'].fillna(0)

    # Calculo final
    df_final['total_bruto_real'] = (df_final['price'] + df_final['freight_value']).round(2)

    # Conversao para dolar
    df_final['total_bruto_dolar'] = (df_final['total_bruto_real'] / valor_dolar).round(2)

    # Calculo de dias
    df_final['tempo_entrega_dias'] = (df_final['order_delivered_customer_date'] - df_final['order_purchase_timestamp']).dt.days

    print(f"Silver gerada: {len(df_final)} linhas.")
    return df_final




# Funcoes de load

# Salvar dados brutos no schema bronze do DW
def load_bronze(df_pedidos, df_itens, df_impostos):
    print(f"\nSalvando camada bronze...")
    try:
        # is_exists para sobrescrever
        # index false para nao salvar indice do pandas
        df_pedidos.to_sql('orders_raw', engine_dw, schema='bronze', if_exists='replace', index=False)
        df_itens.to_sql('items_raw', engine_dw, schema='bronze', if_exists='replace', index=False)
        df_impostos.to_sql('taxes_erp_raw', engine_dw, schema='bronze', if_exists='replace', index=False)
        print("Bronze salvo.")
    except Exception as e:
        print(f"Erro ao salvar bronze: {e}")

# Cria gold e gera KPI para dashboard
def load_gold(df_silver):
    print(f"Gerando camada gold...")

    # Agrupamento - group by
    df_kpi = df_silver.groupby('customer_state').agg({
        'total_bruto_real': 'sum',
        'total_bruto_dolar': 'sum',
        'tempo_entrega_dias': 'mean',
        'order_id': 'count'
    }).reset_index().rename(columns={'order_id': 'qtd_pedidos'})

    # Arredonda colunas numericas
    df_kpi = df_kpi.round(2)

    # Salvar no schema gold
    try:
        df_kpi.to_sql('kpi_vendas_estado', engine_dw, schema='gold', if_exists='replace', index=False)
        print("Gold salvo. KPI no DW.")
    except Exception as e:
        print(f"Erro ao salvar Gold: {e}")


if __name__ == "__main__":
    print("INICIANDO PIPELINE OLIST...")

    PASTA_RAW = 'data/raw'

    df_pedidos, df_itens, df_clientes, df_produtos = extrair_csv(PASTA_RAW)
    df_impostos = extrair_erp_impostos()
    dolar_hoje = extrair_cotacao_dolar()

    # Bronze
    load_bronze(df_pedidos, df_itens, df_impostos)

    # Silver
    df_silver = processar_silver(df_pedidos, df_itens, df_produtos, df_clientes, df_impostos, dolar_hoje)

    # Gold
    load_gold(df_silver)

    print("\nPIPELINE FINALIZADO...")