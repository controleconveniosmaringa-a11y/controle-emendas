import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
import os
import unicodedata
import datetime

# 1. CONFIGURAÇÃO ESTRUTURAL
st.set_page_config(page_title="Controle Convênios", page_icon="🏛️", layout="wide")

if 'pagina_atual' not in st.session_state:
    st.session_state.pagina_atual = 'menu_principal'

def mudar_pagina(nome_pagina):
    st.session_state.pagina_atual = nome_pagina

# Função de limpeza APENAS para os nomes dos Analistas/Responsáveis
def normalizar_texto(texto):
    if pd.isna(texto) or str(texto).strip() == '':
        return ""
    texto_limpo = str(texto).strip().upper()
    # CORREÇÃO AQUI: Estava escrito text_limpo em vez de texto_limpo
    nfkd_form = unicodedata.normalize('NFKD', texto_limpo)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

# 2. INTERFACE VISUAL (CSS)
st.markdown('''<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"], [data-testid="stAppViewContainer"] { font-family: 'Inter', sans-serif; background-color: #ffffff !important; color: #000000 !important; }
    [data-testid="stSidebar"], [data-testid="stSidebarUserContent"] { display: none !important; }
    .header-container { display: flex; justify-content: space-between; align-items: center; padding: 20px 25px; background-color: #0f172a; border-radius: 10px; margin-bottom: 25px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    .header-left { display: flex; align-items: center; }
    .main-title { font-size: 28px; font-weight: 800; color: #ffffff !important; letter-spacing: -0.8px; margin: 0; padding: 0; line-height: 1.2; }
    .header-right { display: flex; align-items: center; background-color: #1e293b; padding: 8px 16px; border-radius: 6px; border: 1px solid #334155; }
    .status-dot { width: 8px; height: 8px; background-color: #10b981; border-radius: 50%; margin-right: 8px; box-shadow: 0 0 8px #10b981; }
    .status-text { font-size: 11px; font-weight: 700; color: #f8fafc !important; text-transform: uppercase; letter-spacing: 0.5px; }
    .home-card { background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 40px 20px; text-align: center; margin-bottom: 15px; }
    .home-title { font-size: 20px; font-weight: 800; color: #0f172a; margin-top: 15px; margin-bottom: 5px; }
    .home-subtitle { font-size: 11px; font-weight: 600; color: #64748b; margin-bottom: 20px; }
    .kpi-row-container { display: flex; gap: 15px; margin-top: 10px; margin-bottom: 5px; }
    .kpi-card-head { flex: 1; background-color: #ffffff; border: 2px solid #000000; border-radius: 8px; padding: 14px 20px; }
    .kpi-card-head-blue { flex: 1; background-color: #f8fafc; border: 2px solid #2563eb; border-radius: 8px; padding: 14px 20px; border-left: 6px solid #2563eb; }
    .kpi-label { font-size: 12px; font-weight: 700; color: #475569; text-transform: uppercase; }
    .kpi-value { font-size: 24px; font-weight: 800; color: #059669; }
    .section-title { font-size: 14px; font-weight: 800; text-transform: uppercase; color: #000000; margin-top: 25px; margin-bottom: 10px; padding-bottom: 6px; border-bottom: 3px solid #000000; }
    .meta-tag { background-color: #f1f5f9; color: #000000; padding: 5px 12px; border-radius: 6px; font-weight: 700; font-size: 12px; border: 1px solid #cbd5e1; margin-right: 6px; display: inline-block; }
    .secretaria-header { font-size: 16px; font-weight: 800; color: #000000; margin-top: 15px; padding-left: 6px; border-left: 5px solid #000000; }
    .extrato-table { width: 100%; border-collapse: collapse; margin-top: 8px; background-color: #ffffff; border: 2px solid #000000; border-radius: 6px; overflow: hidden; }
    .extrato-table th { background-color: #f1f5f9; padding: 10px 15px; font-size: 12px; font-weight: 800; border-bottom: 2px solid #000000; text-align: left;}
    .extrato-row { border-bottom: 1px solid #cbd5e1; }
    .
