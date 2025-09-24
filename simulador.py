# -*- coding: utf--8 -*-

# ===================================================================================
#   SIMULADOR WEB (VERSÃO 18.3 - CORREÇÃO FINAL DE FUSO HORÁRIO DO EXCEL)
#
#   - Garante que as datas lidas do Excel sejam corretamente tratadas com fuso horário.
# ===================================================================================

import os
import traceback
import random
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask, jsonify, render_template, request
import pandas as pd

app = Flask(__name__)

# --- CONFIGURAÇÃO ---
TZ_BRASILIA = ZoneInfo("America/Sao_Paulo")
DATA_FILE = "dados_sensores.xlsx"
dados_excel = pd.DataFrame()
current_index = 0

# --- FUNÇÕES DE MANIPULAÇÃO DE DADOS ---

def carregar_dados_do_excel():
    """Carrega a planilha Excel e trata corretamente o fuso horário."""
    global dados_excel
    try:
        if os.path.exists(DATA_FILE):
            print("--- INICIANDO CARREGAMENTO DO EXCEL ---")
            df = pd.read_excel(DATA_FILE)
            print(">>> Colunas encontradas:", df.columns.tolist())

            # Une as colunas 'Data' e 'Hora'
            df['timestamp'] = pd.to_datetime(df['Data'].astype(str) + ' ' + df['Hora'].astype(str))
            
            # =======================================================================
            # CORREÇÃO CRÍTICA AQUI:
            # Informamos ao Pandas que as datas da planilha representam o horário de Brasília.
            # Isso evita erros de fuso horário nas APIs.
            # =======================================================================
            df['timestamp'] = df['timestamp'].dt.tz_localize(TZ_BRASILIA)

            df = df.rename(columns={
                'Sensor_Chuva (mm)': 'chuva',
                'Sensor_Umidade (%)': 'umidade'
            })
            
            if 'temperatura' not in df.columns:
                df['temperatura'] = [round(random.uniform(18.0, 30.0), 2) for _ in range(len(df))]

            df = df[['timestamp', 'umidade', 'temperatura', 'chuva']]
            df = df.sort_values(by='timestamp').reset_index(drop=True)
            
            dados_excel = df
            print(f">>> SUCESSO! {len(dados_excel)} registros carregados.")
            print("--- FIM DO CARREGAMENTO DO EXCEL ---")
        else:
            print(f"AVISO: Arquivo '{DATA_FILE}' não encontrado.")
            dados_excel = pd.DataFrame(columns=['timestamp', 'umidade', 'temperatura', 'chuva'])
    except Exception as e:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(f"!!!!!!!!!!! FALHA CRÍTICA AO LER O ARQUIVO EXCEL !!!!!!!!!!!")
        print(f"!!!!!!!!!!! O ERRO FOI: {e}")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(traceback.format_exc())
        dados_excel = pd.DataFrame(columns=['timestamp', 'umidade', 'temperatura', 'chuva'])

# --- ROTAS (sem alterações) ---
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
        dados_formatados = df_filtrado.apply(lambda row: { "timestamp_completo": row['timestamp'].strftime('%d/%m/%Y %H:%M:%S'), "timestamp_grafico": row['timestamp'].strftime('%H:%M:%S'), "umidade": row['umidade'], "temperatura": row['temperatura'], "chuva": row['chuva'] }, axis=1).tolist()
        return jsonify(dados_formatados)
    except Exception: print(f"Erro na rota /api/dados: {traceback.format_exc()}"); return jsonify({"error": "Erro interno"}), 500

@app.route('/api/dados_atuais')
def api_dados_atuais():
    global current_index
    try:
        if dados_excel.empty: return jsonify({"error": "Nenhum dado carregado"}), 404
        leitura_atual = dados_excel.iloc[current_index]
        current_index = (current_index + 1) % len(dados_excel)
        leitura_formatada = { "timestamp_completo": leitura_atual['timestamp'].strftime('%d/%m/%Y %H:%M:%S'), "timestamp_grafico": leitura_atual['timestamp'].strftime('%H:%M:%S'), "umidade": leitura_atual['umidade'], "temperatura": leitura_atual['temperatura'], "chuva": leitura_atual['chuva'] }
        return jsonify(leitura_formatada)
    except Exception: print(f"Erro na rota /api/dados_atuais: {traceback.format_exc()}"); return jsonify({"error": "Erro interno"}), 500

@app.route('/api/meses_disponiveis')
def api_meses_disponiveis():
    try:
        if dados_excel.empty: return jsonify([])
        meses = dados_excel['timestamp'].dt.strftime('%Y-%m').unique().tolist()
        meses.sort(reverse=True)
        return jsonify(meses)
    except Exception: print(f"Erro na rota /api/meses_disponiveis: {traceback.format_exc()}"); return jsonify({"error": "Erro interno"}), 500

# --- INICIALIZAÇÃO ---
carregar_dados_do_excel()

