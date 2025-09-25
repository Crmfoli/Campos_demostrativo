# -*- coding: utf-8 -*-
# VERSÃO 19.0 - Lendo colunas de profundidade.
import traceback
from flask import Flask, jsonify, render_template, request
import pandas as pd

app = Flask(__name__)

# Variável para armazenar os dados do Excel em memória.
df_cache = None

def ler_dados_do_excel():
    """
    Esta função lê o arquivo Excel com a estrutura de profundidade,
    processa os dados e os armazena em cache.
    """
    global df_cache
    if df_cache is None:
        try:
            print("Lendo o arquivo 'dados_sensores_final.xlsx' (Estrutura de Profundidade)...")
            
            df = pd.read_excel('dados_sensores_final.xlsx', header=None)

            # --- ALTERAÇÃO AQUI ---
            # Nomes definidos exatamente como você especificou.
            colunas_esperadas = [
                'data_hora', 'profundidade 0,3 m', 'profundidade 0,8 m',
                'profundidade1,5 m', 'profundidade 2,0 m', 'profundidade 2,5 m'
            ]
            
            if len(df.columns) != len(colunas_esperadas):
                 print(f"ERRO: O arquivo tem {len(df.columns)} colunas, mas o programa esperava {len(colunas_esperadas)}.")
                 return pd.DataFrame()

            df.columns = colunas_esperadas
            df = df.iloc[1:].reset_index(drop=True)

            # --- E ALTERAÇÃO AQUI ---
            # Renomeia as colunas para nomes simples para uso interno no programa (p1, p2, etc.).
            df.rename(columns={
                'data_hora': 'timestamp',
                'profundidade 0,3 m': 'p1',
                'profundidade 0,8 m': 'p2',
                'profundidade1,5 m': 'p3',
                'profundidade 2,0 m': 'p4',
                'profundidade 2,5 m': 'p5'
            }, inplace=True)
            
            # Converte a coluna de data/hora.
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df.dropna(subset=['timestamp'], inplace=True)

            # Seleciona apenas as colunas que o programa vai usar.
            colunas_finais = ['timestamp', 'p1', 'p2', 'p3', 'p4', 'p5']
            df = df[colunas_finais]

            df.sort_values(by='timestamp', inplace=True)
            df_cache = df
            print("Arquivo lido, colunas de profundidade processadas e dados em cache com sucesso.")

        except FileNotFoundError:
            print("ERRO CRÍTICO: O arquivo 'dados_sensores_final.xlsx' não foi encontrado!")
            return pd.DataFrame()
        except Exception as e:
            print(f"ERRO CRÍTICO ao processar o arquivo Excel: {traceback.format_exc()}")
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

# --- ALTERAÇÃO NAS APIS PARA ENVIAR OS NOVOS DADOS ---
@app.route('/api/dados')
def api_dados():
    try:
        df = ler_dados_do_excel()
        if df.empty: return jsonify([])
        mes_selecionado = request.args.get('month')
        if mes_selecionado: df_filtrado = df[df['timestamp'].dt.strftime('%Y-%m') == mes_selecionado]
        else: df_filtrado = df.tail(30)
        
        dados_formatados = df_filtrado.apply(lambda row: {
            "timestamp_completo": row['timestamp'].strftime('%d/%m/%Y %H:%M:%S'),
            "p1": row['p1'], "p2": row['p2'], "p3": row['p3'], "p4": row['p4'], "p5": row['p5']
        }, axis=1).tolist()
        return jsonify(dados_formatados)
    except Exception:
        print(f"Erro na rota /api/dados: {traceback.format_exc()}"); return jsonify({"error": "Erro interno"}), 500

@app.route('/api/dados_atuais')
def api_dados_atuais():
    try:
        df = ler_dados_do_excel()
        if df.empty: return jsonify({"error": "Arquivo de dados não encontrado ou vazio"}), 404
        nova_leitura = df.iloc[-1]
        leitura_formatada = {
            "timestamp_completo": nova_leitura['timestamp'].strftime('%d/%m/%Y %H:%M:%S'),
            "p1": nova_leitura['p1'], "p2": nova_leitura['p2'], "p3": nova_leitura['p3'], 
            "p4": nova_leitura['p4'], "p5": nova_leitura['p5']
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
        if df.empty: return jsonify({"error": "Arquivo de dados não encontrado ou vazio"}), 404
        leitura_atual = df.iloc[-1]
        # Para manter a compatibilidade com outras partes, o status de "umidade" usará a primeira profundidade.
        # O conceito de chuva não existe mais nestes dados.
        status = {"umidade": leitura_atual['p1'], "chuva": 0} 
        return jsonify(status)
    except Exception:
        print(f"Erro na rota /api/status_sensores: {traceback.format_exc()}"); return jsonify({"error": "Erro interno ao buscar status"}), 500
