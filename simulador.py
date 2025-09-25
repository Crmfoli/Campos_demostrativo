# -*- coding: utf-8 -*-
# VERSÃO 18.1 - Lendo colunas customizadas do arquivo Excel.
import traceback
from flask import Flask, jsonify, render_template, request
import pandas as pd

app = Flask(__name__)

# Variável para armazenar os dados do Excel em memória e evitar releituras constantes do arquivo.
df_cache = None

def ler_dados_do_excel():
    """
    Esta função lê o arquivo 'dados_sensores_final.xlsx', renomeia as colunas
    para o padrão do programa e o armazena em cache.
    """
    global df_cache
    if df_cache is None:
        try:
            print("Lendo o arquivo 'dados_sensores_final.xlsx'...")
            
            # Lê o arquivo. É importante que a coluna 'Data e Hora' seja lida como data.
            df = pd.read_excel('dados_sensores_final.xlsx', parse_dates=['Data e Hora'])
            
            # --- INÍCIO DA NOVA ALTERAÇÃO ---
            # Renomeia as colunas do seu arquivo para os nomes que o programa espera.
            df.rename(columns={
                'Data e Hora': 'timestamp',
                'Umidade do Solo': 'umidade',
                'Temperatura': 'temperatura',
                'Precipitação': 'chuva'
            }, inplace=True)
            # --- FIM DA NOVA ALTERAÇÃO ---
            
            # Garante que os dados estejam ordenados pela data/hora.
            df.sort_values(by='timestamp', inplace=True)
            
            df_cache = df
            print("Arquivo lido, colunas renomeadas e dados armazenados em cache com sucesso.")

        except FileNotFoundError:
            print("ERRO CRÍTICO: O arquivo 'dados_sensores_final.xlsx' não foi encontrado!")
            return pd.DataFrame()
        except Exception as e:
            print(f"ERRO CRÍTICO ao ler o arquivo Excel: {traceback.format_exc()}")
            print("VERIFIQUE SE OS NOMES DAS COLUNAS NO ARQUIVO EXCEL ('Data e Hora', 'Umidade do Solo', etc.) ESTÃO EXATAMENTE IGUAIS AOS DO CÓDIGO.")
            return pd.DataFrame()
    
    return df_cache


@app.route('/')
def pagina_de_acesso(): return render_template('index.html')

@app.route('/mapa', methods=['GET', 'POST'])
def pagina_mapa(): return render_template('mapa.html')

@app.route('/dashboard')
def pagina_dashboard():
    device_id = request.args.get('device_id', 'SN-A7B4')
    return render_template('dashboard.html', device_id=device_id)

@app.route('/api/dados')
def api_dados():
    try:
        df = ler_dados_do_excel()
        if df.empty: return jsonify([])
        
        mes_selecionado = request.args.get('month')
        if mes_selecionado:
            df_filtrado = df[df['timestamp'].dt.strftime('%Y-%m') == mes_selecionado]
        else:
            df_filtrado = df.tail(30)
            
        dados_formatados = df_filtrado.apply(lambda row: {
            "timestamp_completo": row['timestamp'].strftime('%d/%m/%Y %H:%M:%S'),
            "timestamp_grafico": row['timestamp'].strftime('%H:%M:%S'),
            "umidade": row['umidade'],
            "temperatura": row['temperatura'],
            "chuva": row['chuva']
        }, axis=1).tolist()
        return jsonify(dados_formatados)
    except Exception:
        print(f"Erro na rota /api/dados: {traceback.format_exc()}"); return jsonify({"error": "Erro interno"}), 500

@app.route('/api/dados_atuais')
def api_dados_atuais():
    try:
        df = ler_dados_do_excel()
        if df.empty:
            return jsonify({"error": "Arquivo de dados não encontrado ou vazio"}), 404
        
        nova_leitura = df.iloc[-1]
        
        leitura_formatada = {
            "timestamp_completo": nova_leitura['timestamp'].strftime('%d/%m/%Y %H:%M:%S'),
            "timestamp_grafico": nova_leitura['timestamp'].strftime('%H:%M:%S'),
            "umidade": nova_leitura['umidade'],
            "temperatura": nova_leitura['temperatura'],
            "chuva": nova_leitura['chuva']
        }
        return jsonify(leitura_formatada)
    except Exception:
        print(f"Erro na rota /api/dados_atuais: {traceback.format_exc()}"); return jsonify({"error": "Erro interno"}), 500

@app.route('/api/meses_disponiveis')
def api_meses_disponiveis():
    try:
        df = ler_dados_do_excel()
        if df.empty: return jsonify([])
        
        meses = df['timestamp'].dt.strftime('%Y-%m').unique().tolist()
        meses.reverse()
        return jsonify(meses)
    except Exception:
        print(f"Erro na rota /api/meses_disponiveis: {traceback.format_exc()}"); return jsonify({"error": "Erro interno"}), 500

@app.route('/api/status_sensores')
def api_status_sensores():
    try:
        df = ler_dados_do_excel()
        if df.empty:
            return jsonify({"error": "Arquivo de dados não encontrado ou vazio"}), 404
        
        leitura_atual = df.iloc[-1]
        status = {
            "umidade": leitura_atual['umidade'],
            "chuva": leitura_atual['chuva']
        }
        return jsonify(status)
    except Exception:
        print(f"Erro na rota /api/status_sensores: {traceback.format_exc()}"); return jsonify({"error": "Erro interno ao buscar status"}), 500
