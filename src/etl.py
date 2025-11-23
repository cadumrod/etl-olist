import pandas as pd
import os
import sys

# Config para evitar poluição visual
import warnings
warnings.filterwarnings("ignore")




# Extração
caminho_pasta = "../data/raw"
def extrair_dados(caminho_pasta):
    print("### 1/3 Iniciando extração ###")

    # caminhos de arquivos
    arquivo_pedidos = os.path.join(caminho_pasta, 'olist_orders_dataset.csv')
    arquivo_clientes = os.path.join(caminho_pasta, 'olist_customers_dataset.csv')

    # leitura
    print("Lendo arquivos CSV...")
    df_pedidos = pd.read_csv(arquivo_pedidos)
    df_clientes = pd.read_csv(arquivo_clientes)

    print(f"Pedidos carregados: {df_pedidos.shape[0]}")
    print(f"Clientes carregados: {df_clientes.shape[0]}")

    return df_pedidos, df_clientes


# Transformação
def transformar_dados(df_pedidos, df_clientes):
    print("### 2/3 Iniciando transformação ###")

    # Conversão de datas
    data_cols = [
        'order_purchase_timestamp', 'order_approved_at',
        'order_delivered_carrier_date', 'order_delivered_customer_date',
        'order_estimated_delivery_date'
    ]

    print("Convertendo colunas de data...")
    for col in data_cols:
        # para nao travar script caso encontre data ruim, utilizo o coerce e transforma em nulo
        df_pedidos[col] = pd.to_datetime(df_pedidos[col], errors='coerce')

    # Merge
    print("Realizando Merge (join) de pedidos e clientes...")
    df_completo = df_pedidos.merge(df_clientes,
                                   on='customer_id',
                                   how= 'inner')
    
    # Filtragem apenas de pedidos entregues
    print("Filtrando entregues e calculando tempo...")
    df_final = df_completo[df_completo['order_status'] == 'delivered'].copy()

    # Calcular os dias
    df_final['tempo_entrega_dias'] = (df_final['order_delivered_customer_date'] - df_final['order_purchase_timestamp']).dt.days

    return df_final


# Load
caminho_saida = "../data/processed/olist_processed.csv"
def carregar_dados(df_final, caminho_saida):
    print(f"### 3/3 Iniciando Load ###")

    # garantir que a pasta existe
    destino = os.path.dirname(caminho_saida)
    if not os.path.exists(destino):
        os.makedirs(destino)

    # salvar
    df_final.to_csv(caminho_saida, index=False)
    print(f"Arquivo salvo com sucesso em: {caminho_saida}")



if __name__ == "__main__":
    PASTA_RAW = 'data/raw'
    ARQUIVO_SAIDA = 'data/processed/olist_processed.csv'

    # pipeline
    try:
        df_orders, df_customers = extrair_dados(PASTA_RAW)

        df_limpo = transformar_dados(df_orders, df_customers)

        carregar_dados(df_limpo, ARQUIVO_SAIDA)

        print("\n### Pipeline finalizado com sucesso. ###")
    
    except Exception as e:
        print(f"\nA operação falhou: {e}")
        # codigo 1 para avisar os que existe erro
        sys.exit(1)