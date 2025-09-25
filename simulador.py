# -*- coding: utf-8 -*-
# VERSÃO 19.5 - Diagnóstico Final com o nome de arquivo correto (minúsculas)
import traceback
from flask import Flask, jsonify, render_template, request
import pandas as pd
import os

app = Flask(__name__)

# --- O nome do arquivo CORRETO (tudo minúsculo), como está na sua última imagem ---
CAMINHO_DO_ARQUIVO = os.path.join(app.root_path, 'dados_sensores_final.xlsx')


# --- FUNÇÃO DE DIAGNÓSTICO ---
def ler_dados_do_excel():
    try:
        print("\n" + "="*50)
        print("--- INICIANDO DIAGNÓSTICO DO ARQUIVO EXCEL ---")
        print("="*50)
        
        print(f"\n[INFO] Procurando pelo arquivo no caminho correto: {CAMINHO_DO_ARQUIVO}\n")
        
        # Lê a planilha usando a constante do caminho.
        df = pd.read_excel(CAMINHO_DO_ARQUIVO, header=None)

        # Imprime o número de colunas que o pandas encontrou
        num_colunas = len(df.columns)
        print(f"[INFO] SUCESSO! Arquivo encontrado.")
        print(f"[INFO] Número de colunas encontradas: {num_colunas}\n")
        
        # Imprime o conteúdo da primeira linha do arquivo (que deveriam ser os cabeçalhos)
        if not df.empty:
            primeira_linha = df.iloc[0].to_list()
            print("[INFO] Conteúdo da primeira linha (cabeçalhos):")
            print(primeira_linha)
        
        print("\n" + "="*50)
        print("--- FIM DO DIAGNÓSTICO ---")
        print("="*50)
        print("\n>>> Por favor, copie e cole todo o texto do log (a partir de 'INICIANDO DIAGNÓSTICO') e me envie. <<<\n")


    except FileNotFoundError:
        print(f"ERRO CRÍTICO: O arquivo '{CAMINHO_DO_ARQUIVO}' NÃO FOI ENCONTRADO! Mesmo com o nome e caminho corrigidos.")
        print("Por favor, verifique se o último push para o GitHub foi concluído com sucesso.")
    except Exception as e:
        print(f"ERRO ao tentar diagnosticar o arquivo: {traceback.format_exc()}")
    
    return pd.DataFrame()


# O restante do programa permanece aqui para que ele possa ser executado.
@app.route('/')
def pagina_de_acesso(): 
    ler_dados_do_excel() # Roda o diagnóstico quando a página é acessada
    return "Modo de Diagnóstico. Verifique o log do Render para informações."

@app.route('/mapa', methods=['GET', 'POST'])
def pagina_mapa(): return "Modo de Diagnóstico."
@app.route('/dashboard')
def pagina_dashboard(): return "Modo de Diagnóstico."
@app.route('/api/dados')
def api_dados(): return jsonify([])
@app.route('/api/dados_atuais')
def api_dados_atuais(): return jsonify({})
@app.route('/api/meses_disponiveis')
def api_meses_disponiveis(): return jsonify([])
@app.route('/api/status_sensores')
def api_status_sensores(): return jsonify({})
