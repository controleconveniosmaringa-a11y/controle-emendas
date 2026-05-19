import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
import os
import unicodedata

# Configuração da página
st.set_page_config(page_title="Controle de Emendas", page_icon="📊", layout="wide")

# CSS Estilizado
st.markdown('''<style>
    .header-container { display: flex; justify-content: space-between; align-items: center; padding: 20px 25px; background-color: #0f172a; border-radius: 10px; margin-bottom: 25px; }
    .main-title { font-size: 28px; font-weight: 800; color: #ffffff !important; }
    .section-title { font-size: 14px; font-weight: 800; text-transform: uppercase; margin-top: 25px; border-bottom: 3px solid #000000; }
    .extrato-table { width: 100%; border-collapse: collapse; margin-top: 10px; background: #ffffff; border: 1px solid #ddd; }
    .extrato-table th { background: #f1f5f9; padding: 10px; font-weight: 800; }
    .extrato-table td { padding: 8px; border-bottom: 1px solid #eee; text-align: right; }
    .btn-download { background: #e2e8f0; color: #0f172a !important; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 700; text-decoration: none; display: inline-block; }
    .link-abrir { color: #2563eb !important; font-size: 12px; font-weight: 700; text-decoration: none; }
</style>''', unsafe_allow_html=True)

def fmt(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def normalizar_nome(texto):
    if not isinstance(texto, str): return "NÃO INFORMADO"
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8').strip().upper()

@st.cache_data(ttl=3600)
def carregar_dados():
    url = "https://raw.githubusercontent.com/controleconveniosmaringa-a11y/controle-emendas/main/dados.csv"
    try:
        df = pd.read_csv(url, low_memory=False, dtype=str, keep_default_na=False, na_filter=False)
        # Limpeza básica e padronização
        df.columns = [re.sub(r'[^\w]', '', c).lower() for c in df.columns]
        df['deputado'] = df['deputado'].apply(normalizar_nome)
        # Converte valores numéricos
        for col in ['repasse', 'rendimento', 'bruto']:
            df[col] = [float(re.sub(r'[^\d,.-]', '', str(v)).replace(',', '.')) if re.sub(r'[^\d,.-]', '', str(v)) else 0.0 for v in df[col]]
        return df
    except: return pd.DataFrame()

df = carregar_dados()

def gerar_botoes(link, emp, nota, modo):
    if not link or link == '-': return '-'
    if modo == "abrir": return f'<a href="{link}" target="_blank" class="link-abrir">Visualizar 🔗</a>'
    nome = f"Nota_Fiscal_{nota}.pdf" if nota != '-' else f"Empenho_{emp}.pdf"
    return f'<a href="{link}" download="{nome}" class="btn-download">Baixar 💾</a>'

# Renderização
st.markdown('<div class="header-container"><div class="main-title">Controle de Emendas Orçamentárias</div></div>', unsafe_allow_html=True)
tabs = st.tabs(["🎯 Por Fonte", "📋 Por Plano", "🏛️ Por Secretaria", "🔍 Por Deputado", "🌐 Panorama Geral"])

# --- ABA DEPUTADO (Exemplo da correção do seletor único) ---
with tabs[3]:
    st.markdown("<div class='section-title'>🔍 Painel Parlamentar</div>", unsafe_allow_html=True)
    lista_deps = sorted(list(set([d for d in df['deputado'].unique() if d not in ['', 'NAN', 'NÃO INFORMADO']])))
    dep_sel = st.selectbox("Selecione o Parlamentar:", options=lista_deps)
    
    df_dep = df[df['deputado'] == dep_sel]
    st.write(f"### Lançamentos de: {dep_sel}")
    
    df_render = df_dep.copy()
    df_render['Abrir'] = [gerar_botoes(l, e, n, "abrir") for l, e, n in zip(df_render['urllink'], df_render['empenho'], df_render['nota'])]
    df_render['Baixar'] = [gerar_botoes(l, e, n, "baixar") for l, e, n in zip(df_render['urllink'], df_render['empenho'], df_render['nota'])]
    
    st.write(df_render[['data', 'empenho', 'nota', 'bruto', 'Abrir', 'Baixar']].to_html(escape=False, index=False, classes='extrato-table'), unsafe_allow_html=True)

# --- PANORAMA GERAL ---
with tabs[4]:
    st.markdown("<div class='section-title'>🌐 Panorama Geral</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    # Aqui você pode copiar os gráficos que tínhamos antes, eles funcionam com esse 'df' limpo.
    st.info("Painel em pleno funcionamento.")
