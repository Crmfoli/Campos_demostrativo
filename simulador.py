# -*- coding: utf-8 -*-

# ===================================================================================
#   SIMULADOR WEB (VERSÃO 18.1 - ADAPTAÇÃO PARA PLANILHA REAL)
#
#   - Adaptado para ler os nomes de colunas específicos da sua planilha.
#   - Une as colunas 'Data' e 'Hora' em uma única coluna 'timestamp'.
# ===================================================================================

import os
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask, jsonify, render_template, request
import pandas as pd
import threading
import time

app = Flask(__name__)

# --- CONFIGURAÇÃO ---
TZ_BRASILIA = ZoneInfo("America/Sao_Paulo")
DATA_FILE = "dados_sensores.xlsx"
dados_excel = pd.DataFrame()
current_index = 0

# --- FUNÇÕES DE MANIPULAÇÃO DE DADOS ---

def carregar_dados_do_excel():
    """Carrega a planilha Excel específica do usuário para um DataFrame do Pandas."""
    global dados_excel
    try:
        if os.path.exists(DATA_FILE):
            print(f"Carregando dados do arquivo {DATA_FILE}...")
            
            # 1. Lê o arquivo Excel.
            df = pd.read_excel(DATA_FILE)

            # 2. Une as colunas 'Data' e 'Hora' em uma única coluna 'timestamp'.
            # O Pandas é inteligente para entender os formatos mais comuns de data e hora.
            df['timestamp'] = pd.to_datetime(df['Data'].astype(str) + ' ' + df['Hora'].astype(str))

            # 3. Renomeia as colunas da sua planilha para os nomes padrão que o resto do programa espera.
            df = df.rename(columns={
                'Sensor_Chuva (mm)': 'chuva',
                'Sensor_Umidade (%)': 'umidade'
            })
            
            # Adiciona a coluna 'temperatura' com dados simulados, já que ela não existe na sua planilha.
            # Se você adicionar essa coluna no seu Excel, o programa a usará.
            if 'temperatura' not in df.columns:
                df['temperatura'] = [round(random.uniform(18.0, 30.0), 2) for _ in range(len(df))]

            # 4. Seleciona apenas as colunas que vamos usar, na ordem correta.
            df = df[['timestamp', 'umidade', 'temperatura', 'chuva']]
            
            # 5. Ordena os dados por data para garantir a sequência correta.
            df = df.sort_values(by='timestamp').reset_index(drop=True)
            
            dados_excel = df
            print(f"Sucesso! {len(dados_excel)} registros carregados e processados.")
        else:
            print(f"AVISO: Arquivo '{DATA_FILE}' não encontrado.")
            dados_excel = pd.DataFrame(columns=['timestamp', 'umidade', 'temperatura', 'chuva'])
    except Exception:
        print(f"FALHA CRÍTICA AO LER O ARQUIVO EXCEL: {traceback.format_exc()}")


# --- ROTAS DA APLICAÇÃO (sem alterações) ---
@app.route('/')
def pagina_de_acesso(): return render_template('index.html')

@app.route('/mapa', methods=['GET', 'POST'])
def pagina_mapa(): return render_template('mapa.html')

@app.route('/dashboard')
def pagina_dashboard():
    device_id = request.args.get('device_id', 'SN-A7B4')
    return render_template('dashboard.html', device_id=device_id)

# --- ROTAS DE API (sem alterações) ---

@app.route('/api/dados')
def api_dados():
    try:
        if dados_excel.empty: return jsonify([])
        mes_selecionado = request.args.get('month')
        df = dados_excel.copy()
        if mes_selecionado:
            df_filtrado = df[df['timestamp'].dt.strftime('%Y-%m') == mes_selecionado]
        else:
            df_filtrado = df.tail(30)
        dados_formatados = df_filtrado.apply(lambda row: { "timestamp_completo": row['timestamp'].astimezone(TZ_BRASILIA).strftime('%d/%m/%Y %H:%M:%S'), "timestamp_grafico": row['timestamp'].astimezone(TZ_BRASILIA).strftime('%H:%M:%S'), "umidade": row['umidade'], "temperatura": row['temperatura'], "chuva": row['chuva'] }, axis=1).tolist()
        return jsonify(dados_formatados)
    except Exception:
        print(f"Erro na rota /api/dados: {traceback.format_exc()}"); return jsonify({"error": "Erro interno"}), 500

@app.route('/api/dados_atuais')
def api_dados_atuais():
    global current_index
    try:
        if dados_excel.empty: return jsonify({"error": "Nenhum dado carregado"}), 404
        leitura_atual = dados_excel.iloc[current_index]
        current_index = (current_index + 1) % len(dados_excel)
        leitura_formatada = { "timestamp_completo": leitura_atual['timestamp'].astimezone(TZ_BRASILIA).strftime('%d/%m/%Y %H:%M:%S'), "timestamp_grafico": leitura_atual['timestamp'].astimezone(TZ_BRASILIA).strftime('%H:%M:%S'), "umidade": leitura_atual['umidade'], "temperatura": leitura_atual['temperatura'], "chuva": leitura_atual['chuva'] }
        return jsonify(leitura_formatada)
    except Exception:
        print(f"Erro na rota /api/dados_atuais: {traceback.format_exc()}"); return jsonify({"error": "Erro interno"}), 500

@app.route('/api/meses_disponiveis')
def api_meses_disponiveis():
    try:
        if dados_excel.empty: return jsonify([])
        meses = dados_excel['timestamp'].dt.strftime('%Y-%m').unique().tolist()
        meses.sort(reverse=True)
        return jsonify(meses)
    except Exception:
        print(f"Erro na rota /api/meses_disponiveis: {traceback.format_exc()}"); return jsonify({"error": "Erro interno"}), 500
        
# --- INICIALIZAÇÃO ---
carregar_dados_do_excel()
