import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
import os
import unicodedata
import datetime
import urllib.parse

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
    nfkd_form = unicodedata.normalize('NFKD', texto_limpo)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

# 2. INTERFACE VISUAL (CSS CORPORATIVO E PROFISSIONAL)
st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"], [data-testid="stAppViewContainer"] { font-family: 'Inter', sans-serif; background-color: #f8fafc !important; color: #0f172a !important; }
    [data-testid="stSidebar"], [data-testid="stSidebarUserContent"] { display: none !important; }
    .header-container { display: flex; justify-content: space-between; align-items: center; padding: 20px 25px; background: #0f172a; border-radius: 8px; margin-bottom: 25px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border-bottom: 4px solid #3b82f6; }
    .header-left { display: flex; align-items: center; }
    .main-title { font-size: 26px; font-weight: 800; color: #ffffff !important; letter-spacing: -0.5px; margin: 0; padding: 0; }
    .header-right { display: flex; align-items: center; background-color: #1e293b; padding: 8px 16px; border-radius: 6px; }
    .status-dot { width: 8px; height: 8px; background-color: #10b981; border-radius: 50%; margin-right: 8px; box-shadow: 0 0 8px #10b981; }
    .status-text { font-size: 11px; font-weight: 700; color: #f8fafc !important; text-transform: uppercase; letter-spacing: 0.5px; }
    
    /* CARDS CORPORATIVOS E CLEAN */
    .home-card { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 35px 20px; text-align: center; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); transition: all 0.2s ease; border-top: 4px solid #cbd5e1; }
    .home-card:hover { transform: translateY(-3px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05); border-color: #94a3b8; }
    .home-title { font-size: 18px; font-weight: 800; color: #1e293b; margin-top: 15px; margin-bottom: 5px; text-transform: uppercase; }
    .home-subtitle { font-size: 12px; font-weight: 600; color: #64748b; margin-bottom: 20px; }
    
    /* CARD DE BUSCA DESTAQUE */
    .search-box-highlight { background-color: #f0f9ff; border: 1px solid #bae6fd; border-left: 6px solid #0284c7; padding: 22px; border-radius: 8px; margin-top: 10px; margin-bottom: 25px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02); }
    
    .kpi-row-container { display: flex; gap: 15px; margin-top: 10px; margin-bottom: 5px; }
    .kpi-card-head { flex: 1; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 18px 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
    .kpi-card-head-blue { flex: 1; background-color: #f8fafc; border: 1px solid #bfdbfe; border-radius: 8px; padding: 18px 20px; border-left: 5px solid #2563eb; }
    .kpi-label { font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }
    .kpi-value { font-size: 24px; font-weight: 800; color: #059669; margin-top: 4px; }
    .section-title { font-size: 14px; font-weight: 800; text-transform: uppercase; color: #0f172a; margin-top: 30px; margin-bottom: 15px; padding-bottom: 8px; border-bottom: 2px solid #e2e8f0; }
    .meta-tag { background-color: #f1f5f9; color: #334155; padding: 6px 12px; border-radius: 6px; font-weight: 700; font-size: 11px; border: 1px solid #cbd5e1; margin-right: 6px; display: inline-block; }
    .secretaria-header { font-size: 15px; font-weight: 800; color: #0f172a; margin-top: 20px; padding-left: 8px; border-left: 4px solid #3b82f6; background-color: #f8fafc; padding-top: 6px; padding-bottom: 6px; border-radius: 0 6px 6px 0; }
    
    /* TABELAS SÓBRIAS GERAIS */
    .extrato-table { width: 100%; border-collapse: separate; border-spacing: 0; margin-top: 10px; margin-bottom: 20px; background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
    .extrato-table th { background-color: #1e293b; color: #f8fafc; padding: 12px 15px; font-size: 12px; font-weight: 700; text-align: left; text-transform: uppercase; letter-spacing: 0.5px; }
    .extrato-row { transition: all 0.2s ease; background-color: #ffffff; }
    .extrato-row:nth-child(even) { background-color: #f8fafc; }
    .extrato-row:hover { background-color: #f1f5f9; }
    .extrato-row td { border-bottom: 1px solid #e2e8f0; }
    .extrato-row-final { background-color: #ecfdf5; font-weight: 800; }
    .extrato-row-final td { color: #065f46 !important; border-top: 2px solid #10b981; }
    .extrato-cell-label { padding: 12px 15px; font-size: 12px; font-weight: 600; color: #334155; text-align: left; border-right: 1px dashed #e2e8f0; }
    .extrato-cell-val { padding: 12px 15px; font-size: 13px; font-weight: 800; text-align: right; white-space: nowrap; }
    
    .btn-download-direto { background-color: #f1f5f9; color: #0f172a !important; text-decoration: none !important; padding: 6px 12px; border-radius: 4px; font-size: 11px; font-weight: 700; border: 1px solid #cbd5e1; display: inline-block; transition: all 0.2s ease; text-transform: uppercase; }
    .btn-download-direto:hover { background-color: #e2e8f0; color: #000000 !important; border-color: #94a3b8; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .link-abrir-doc { color: #2563eb !important; text-decoration: none !important; font-size: 12px; font-weight: 700; background-color: #eff6ff; padding: 6px 12px; border-radius: 4px; display: inline-block; border: 1px solid #bfdbfe; transition: 0.2s; }
    .link-abrir-doc:hover { background-color: #dbeafe; color: #1d4ed8 !important; }
</style>""", unsafe_allow_html=True)

# 3. CARREGAMENTO DOS BANCOS DE DADOS
@st.cache_data(ttl=3600)
def obter_base_dados_global():
    agora = datetime.datetime.utcnow() - datetime.timedelta(hours=3)
    att = agora.strftime("%d/%m/%Y às %H:%M")
    url = "https://raw.githubusercontent.com/controleconveniosmaringa-a11y/controle-emendas/main/dados.csv"
    try:
        df_raw = pd.read_csv(url, low_memory=False, dtype=str, keep_default_na=False, na_filter=False)
    except Exception:
        if os.path.exists("dados.csv"):
            df_raw = pd.read_csv("dados.csv", low_memory=False, dtype=str, keep_default_na=False, na_filter=False)
            timestamp = os.path.getmtime("dados.csv")
            att = datetime.datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y às %H:%M")
        else: return pd.DataFrame(), "Indisponível"
    if df_raw.empty: return pd.DataFrame(), "Base Vazia"
    df = pd.DataFrame()
    col_orig = {re.sub(r'[^\w\s]', '', str(c).strip().lower()).replace('â', 'a').replace('ç', 'c').replace('ã', 'a').replace('ó', 'o'): c for c in df_raw.columns}
    def ext(chave):
        c_real = next((o for l, o in col_orig.items() if chave in l), None)
        if c_real: return [str(i).strip() if str(i).strip().lower() not in ['', 'nan'] else '' for i in df_raw[c_real]]
        return [''] * len(df_raw)
    df['fonte_clean'] = [str(f).split('.')[0].lower().replace('-', '').strip() for f in ext('fonte')]
    df['emenda_clean'] = [str(e).split('.')[0].strip() for e in ext('emenda')]
    df['plano_clean'] = [str(p).split('.')[0].upper().strip() for p in ext('plano')]
    df['EMPENHO_COL'] = [x if x != '' else '-' for x in ext('empenho')]
    df['NOTA_COL'] = [x if x != '' else '-' for x in ext('nota')]
    url_items = [''] * len(df_raw)
    for c in ['urllink', 'url', 'link', 'comprovante', 'pdf']:
        c_achada = next((o for l, o in col_orig.items() if c in l), None)
        if c_achada: url_items = [str(i).strip() for i in df_raw[c_achada]]; break
    df['URL_REAL_LINK'] = [lk if re.match(r'^(http|https|www\.)', lk, re.IGNORECASE) else ("https://" + lk if '.' in lk and lk.lower() not in ['nan','','-'] else '') for lk in url_items]
    df['secretaria'] = [x if x != '' else 'Não Especificada' for x in ext('secretaria')]
    df['deputado'] = [x if x != '' else 'Não Informado' for x in ext('deputado')]
    df['desc_clean'] = [x if x != '' else 'Sem descrição informada' for x in ext('descricao')]
    df['conta corrente'] = [x if x != '' else 'Não Informada' for x in ext('conta')]
    df['ano_mov'] = [re.search(r'(20\d{2})', str(d)).group(1) if re.search(r'(20\d{2})', str(d)) else '2025' for d in ext('data')]
    df['DATA_LANCAMENTO'] = ext('data')
    def limpar_moeda(val):
        v_str = str(val).upper().replace('R$', '').strip()
        v_str = re.sub(r'[^\d.,-]', '', v_str)
        if not v_str or v_str == '-': return 0.0
        if ',' in v_str and '.' in v_str:
            if v_str.rfind(',') > v_str.rfind('.'): v_str = v_str.replace('.', '').replace(',', '.')
            else: v_str = v_str.replace(',', '')
        elif ',' in v_str: v_str = v_str.replace(',', '.')
        try: return float(v_str)
        except ValueError: return 0.0
    for c in ['repasse', 'rendimento', 'bruto']: df[c] = [limpar_moeda(v) for v in ext(c)]
    return df, att

@st.cache_data(ttl=3600)
def obter_base_convenios():
    agora = datetime.datetime.utcnow() - datetime.timedelta(hours=3)
    att = agora.strftime("%d/%m/%Y às %H:%M")
    url = "https://raw.githubusercontent.com/controleconveniosmaringa-a11y/controle-emendas/main/Divis%C3%A3o%20Convenios%20-%20Divisao.csv"
    try:
        d = pd.read_csv(url, low_memory=False, dtype=str, keep_default_na=False, na_filter=False)
    except Exception:
        if os.path.exists("Divisão Convenios - Divisao.csv"):
            d = pd.read_csv("Divisão Convenios - Divisao.csv", low_memory=False, dtype=str, keep_default_na=False, na_filter=False)
            timestamp = os.path.getmtime("Divisão Convenios - Divisao.csv")
            att = datetime.datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y às %H:%M")
        else: return pd.DataFrame(), "Indisponível"
    if not d.empty:
        d.columns = [str(c).strip() for c in d.columns]
        if 'RESPONSÁVEL' in d.columns: d['RESPONSÁVEL'] = d['RESPONSÁVEL'].apply(normalizar_texto)
    return d, att

@st.cache_data(ttl=3600)
def obter_base_credito():
    agora = datetime.datetime.utcnow() - datetime.timedelta(hours=3)
    att = agora.strftime("%d/%m/%Y às %H:%M")
    nome_arquivo = "operacoes_credito.csv"
    url = f"https://raw.githubusercontent.com/controleconveniosmaringa-a11y/controle-emendas/main/{nome_arquivo}"
    try:
        df_raw = pd.read_csv(url, low_memory=False, dtype=str, keep_default_na=False, na_filter=False)
    except Exception:
        if os.path.exists(nome_arquivo):
            df_raw = pd.read_csv(nome_arquivo, low_memory=False, dtype=str, keep_default_na=False, na_filter=False)
            timestamp = os.path.getmtime(nome_arquivo)
            att = datetime.datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y às %H:%M")
        else: return pd.DataFrame(), "Aguardando envio pelo Google Sheets"
    if df_raw.empty: return pd.DataFrame(), "Base Vazia"
    
    col_orig = {re.sub(r'[^\w\s]', '', str(c).strip().lower()).replace('â', 'a').replace('ç', 'c').replace('ã', 'a').replace('ó', 'o'): c for c in df_raw.columns}
    def ext_c(chave_exata, chave_parcial):
        for limpo, orig in list(col_orig.items()):
            if chave_exata in limpo:
                del col_orig[limpo]; return [str(i).strip() if str(i).strip().lower() not in ['', 'nan'] else '' for i in df_raw[orig]]
        for limpo, orig in list(col_orig.items()):
            if chave_parcial in limpo:
                del col_orig[limpo]; return [str(i).strip() if str(i).strip().lower() not in ['', 'nan'] else '' for i in df_raw[orig]]
        return [''] * len(df_raw)
        
    df = pd.DataFrame()
    if ext_c('programa', 'programa') == [''] * len(df_raw): df['PROGRAMA'] = ['NÃO ESPECIFICADO'] * len(df_raw)
    else: df['PROGRAMA'] = [str(i).upper().strip() if str(i).strip().lower() not in ['', 'nan'] else 'NÃO ESPECIFICADO' for i in df_raw['PROGRAMA'] ] if 'PROGRAMA' in df_raw.columns else ['NÃO ESPECIFICADO'] * len(df_raw)
    df['EMPENHO'] = ext_c('empenho', 'empenho')
    df['FORNECEDOR'] = ext_c('fornecedor', 'fornecedor')
    df['TIPO DE DOCUMENTO'] = ext_c('tipodedoc', 'tipo')
    df['Nº DOCUMENTO'] = ext_c('ndoc', 'documento')
    df['DESCRIÇÃO'] = ext_c('descricao', 'descri')
    df['REF VALOR REPASSADO'] = [str(x).upper() if str(x) != '' else 'NÃO ESPECIFICADO' for x in ext_c('refvalor', 'ref')]
    df['LINK DOCUMENTO'] = ext_c('link', 'url')
    def limpar_moeda(val):
        v_str = str(val).upper().replace('R$', '').strip()
        v_str = re.sub(r'[^\d.,-]', '', v_str)
        if not v_str or v_str == '-': return 0.0
        if ',' in v_str and '.' in v_str:
            if v_str.rfind(',') > v_str.rfind('.'): v_str = v_str.replace('.', '').replace(',', '.')
            else: v_str = v_str.replace(',', '')
        elif ',' in v_str: v_str = v_str.replace(',', '.')
        try: return float(v_str)
        except ValueError: return 0.0
    df['REPASSE'] = [limpar_moeda(v) for v in ext_c('repasse', 'repass')]
    df['VALOR DESPESA'] = [limpar_moeda(v) for v in ext_c('valordespesa', 'despesa')]
    return df, att

df, att_emendas = obter_base_dados_global()
df_conv, att_convenios = obter_base_convenios()
df_cred_completo, att_cred = obter_base_credito()

if not df_cred_completo.empty and 'PROGRAMA' in df_cred_completo.columns:
    df_finisa = df_cred_completo[df_cred_completo['PROGRAMA'] == 'FINISA']
    df_usina = df_cred_completo[df_cred_completo['PROGRAMA'] == 'USINA FOTOVOLTAICA']
else:
    df_finisa = pd.DataFrame()
    df_usina = pd.DataFrame()

def fmt(v): 
    val = float(v)
    if round(val, 2) == 0: val = 0.0
    return f"R$ {val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def gerar_botoes_documento(url, emp, nota, tipo="abrir"):
    if not url or url == '': return '-'
    if tipo == "baixar" and "drive.google.com" in url and "/file/d/" in url: 
        url = f"https://drive.google.com/uc?export=download&id={url.split('/file/d/')[1].split('/')[0]}"
    if tipo == "abrir": return f'<a href="{url}" target="_blank" class="link-abrir-doc">Visualizar 🔗</a>'
    nome = f"Doc_{nota}.pdf" if nota not in ['-',''] else (f"Empenho_{emp}.pdf" if emp not in ['-',''] else "documento.pdf")
    return f'<a href="{url}" download="{nome}" class="btn-download-direto">Baixar 💾</a>'

def processar_saldos_acumulados(df_programa):
    if not df_programa.empty:
        abas = sorted([aba for aba in df_programa['REF VALOR REPASSADO'].unique() if aba != 'NÃO ESPECIFICADO'])
        saldo_anterior = 0.0
        dados_finais = {}
        for aba_nome in abas:
            df_aba = df_programa[df_programa['REF VALOR REPASSADO'] == aba_nome]
            repasse_puro_atual = df_aba['REPASSE'].sum()
            despesas_atuais = df_aba['VALOR DESPESA'].sum()
            recurso_disponivel_total = repasse_puro_atual + saldo_anterior
            saldo_remanescente_final = recurso_disponivel_total - despesas_atuais
            dados_finais[aba_nome] = {
                'repasse_atual': repasse_puro_atual, 'saldo_anterior': saldo_anterior, 'total_disponivel': recurso_disponivel_total,
                'total_despesa': despesas_atuais, 'saldo_final': saldo_remanescente_final, 'df_filtrado': df_aba
            }
            saldo_anterior = saldo_remanescente_final
        return dados_finais, abas
    return {}, []

# --- FUNÇÕES PANDAS STYLER (CORES NAS TABELAS) ---
def highlight_saldo_verde(col): return ['background-color: #f0fdf4; color: #065f46; font-weight: 800;' if v != '' else '' for v in col]
def highlight_total_azul(col): return ['background-color: #eff6ff; color: #1e3a8a; font-weight: 800;' if v != '' else '' for v in col]
def style_row_warning(row): return ['background-color: #fffbeb; color: #92400e; font-weight: 600;'] * len(row)
def style_abertura_banco(row):
    if 'TOTAL' in str(row['Fonte Orçamentária']): return ['background-color: #0f172a; color: #ffffff; font-weight: 800;'] * len(row)
    elif '(ATIVA)' in str(row['Fonte Orçamentária']): return ['background-color: #e0f2fe; color: #0369a1; font-weight: 700;'] * len(row)
    return [''] * len(row)

# ==============================================================================
# ROTEAMENTO DAS TELAS
# ==============================================================================

if st.session_state.pagina_atual == 'menu_principal':
    
    tz_br = datetime.timezone(datetime.timedelta(hours=-3))
    agora_br = datetime.datetime.now(tz_br)
    hora_str = agora_br.strftime("%H:%M")
    data_str = agora_br.strftime("%d/%m/%Y")
    
    # Renderização do Banner Executivo Sóbrio
    st.markdown(f"<div style='background: #0f172a; padding: 45px 20px; border-radius: 12px; text-align: center; margin-top: 10px; margin-bottom: 30px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); position: relative; border-bottom: 4px solid #3b82f6;'><div style='position: absolute; top: 15px; right: 20px; font-size: 12px; color: #94a3b8; font-weight: 600; display: flex; gap: 15px; align-items: center; background: #1e293b; padding: 6px 14px; border-radius: 6px; border: 1px solid #334155;'><span style='display:flex; align-items:center; gap:5px;'>📍 Maringá, PR</span><span style='display:flex; align-items:center; gap:5px;'>📅 {data_str}</span><span style='display:flex; align-items:center; gap:5px;'>🕒 {hora_str}</span></div><h1 style='font-size: 42px; font-weight: 800; color: #f8fafc; margin: 0; margin-top: 15px; letter-spacing: -1px; text-transform: uppercase;'>Controle Convênios</h1><p style='color: #cbd5e1; font-size: 16px; font-weight: 500; margin-top: 5px; letter-spacing: 0.5px;'>Painel de Gestão e Monitoramento Orçamentário</p></div>", unsafe_allow_html=True)
    
    # 3 Módulos - Clean e Profissional
    c1, c2, c3 = st.columns(3, gap="large")
    with c1:
        st.markdown(f"<div class='home-card' style='border-top-color: #3b82f6;'><span style='font-size: 48px; display:block; margin-bottom:10px;'>📊</span><div class='home-title'>Emendas Orçamentárias</div><div class='home-subtitle'>Última Atualização: {att_emendas}</div></div>", unsafe_allow_html=True)
        st.button("Acessar Emendas", key="btn_emendas", use_container_width=True, type="primary", on_click=mudar_pagina, args=('emendas',))
        
    with c2:
        st.markdown(f"<div class='home-card' style='border-top-color: #10b981;'><span style='font-size: 50px; display:block; margin-bottom:10px;'>🏦</span><div class='home-title'>Operações de Crédito</div><div class='home-subtitle'>Status: Monitoramento Ativo</div></div>", unsafe_allow_html=True)
        st.button("Acessar Crédito", key="btn_credito", use_container_width=True, type="primary", on_click=mudar_pagina, args=('credito',))
        
    with c3:
        st.markdown(f"<div class='home-card' style='border-top-color: #f59e0b;'><span style='font-size: 48px; display:block; margin-bottom:10px;'>🤝</span><div class='home-title'>Divisão Convênios</div><div class='home-subtitle'>Última Atualização: {att_convenios}</div></div>", unsafe_allow_html=True)
        st.button("Acessar Convênios", key="btn_convenios", use_container_width=True, type="primary", on_click=mudar_pagina, args=('convenios',))

    st.markdown("---")
    
    # --- 🔍 FILTRO / BUSCA RÁPIDA DE CONVÊNIOS DESTAQUE PREMIUM ---
    st.markdown("<div class='search-box-highlight'>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 14px; font-weight: 800; color: #0369a1; margin-top:0; margin-bottom:10px; text-transform: uppercase; letter-spacing:0.5px;'>🔍 Identificação Pronta de Analista</p>", unsafe_allow_html=True)
    busca_conv_home = st.text_input("Busque por número da fonte, do convênio ou da emenda:", key="busca_conv_home", placeholder="Digite o termo ou código da pesquisa aqui...")
    
    if busca_conv_home:
        if not df_conv.empty:
            mask_home = pd.Series(False, index=df_conv.index)
            for col in df_conv.columns:
                mask_home |= df_conv[col].astype(str).str.contains(busca_conv_home, case=False, na=False)
            df_encontrado_home = df_conv[mask_home]
            
            if not df_encontrado_home.empty:
                if 'RESPONSÁVEL' in df_encontrado_home.columns:
                    analistas_unicos = [a for a in df_encontrado_home['RESPONSÁVEL'].unique() if str(a).strip() != ""]
                    if analistas_unicos:
                        for analista in analistas_unicos:
                            st.markdown(f"<div style='background-color:#ffffff; border-left:4px solid #10b981; padding:12px 18px; border-radius:4px; margin-top:10px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); font-size:14px; color:#1e293b;'><b>Analista responsável:</b> <span style='color:#059669; font-weight:700;'>{analista}</span></div>", unsafe_allow_html=True)
                    else: st.markdown("<p style='font-size:13px; color:#64748b; margin-top:5px;'>⚠️ Registro localizado, mas sem analista associado.</p>", unsafe_allow_html=True)
                else: st.markdown("<p style='font-size:13px; color:#dc2626; margin-top:5px;'>⚠️ Coluna de responsabilidade ausente.</p>", unsafe_allow_html=True)
            else: st.markdown("<p style='font-size:13px; color:#dc2626; margin-top:5px;'>❌ Nenhum registro de convênio localizado com esse termo.</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # --- MÓDULO: ÚLTIMAS MOVIMENTAÇÕES ---
    st.markdown("<div class='section-title'>🕒 Últimas Movimentações Registradas</div>", unsafe_allow_html=True)
    c_ult_1, c_ult_2 = st.columns(2, gap="large")
    
    with c_ult_1:
        st.markdown("<p style='font-size: 14px; font-weight: 700; color: #1e293b; margin-bottom: 5px;'>📉 Emendas Orçamentárias</p>", unsafe_allow_html=True)
        if not df.empty:
            df_em_mov = df[(df['bruto'] > 0) | (df['repasse'] > 0)].copy()
            if not df_em_mov.empty:
                ultimas_emendas = df_em_mov.tail(5)[::-1]
                disp_emendas = pd.DataFrame({
                    'Data': ultimas_emendas['DATA_LANCAMENTO'],
                    'Fonte': ultimas_emendas['fonte_clean'].str.upper(),
                    'Doc/Empenho': [f"NF: {n}" if n != '-' else (f"Emp: {e}" if e != '-' else "-") for e, n in zip(ultimas_emendas['EMPENHO_COL'], ultimas_emendas['NOTA_COL'])],
                    'Tipo': ['Despesa' if b > 0 else 'Repasse' for b in ultimas_emendas['bruto']],
                    'Valor': [b if b > 0 else r for b, r in zip(ultimas_emendas['bruto'], ultimas_emendas['repasse'])]
                })
                st.dataframe(disp_emendas.style.set_table_styles([
                    {'selector': 'th', 'props': [('background-color', '#1e40af'), ('color', 'white'), ('font-weight', 'bold'), ('text-transform', 'uppercase'), ('font-size', '11px')]}
                ]).format({'Valor': fmt}), use_container_width=True, hide_index=True)
            else: st.info("Nenhuma movimentação financeira encontrada.")
        else: st.info("Base de emendas vazia.")
            
    with c_ult_2:
        st.markdown("<p style='font-size: 14px; font-weight: 700; color: #1e293b; margin-bottom: 5px;'>📉 Operações de Crédito</p>", unsafe_allow_html=True)
        if not df_cred_completo.empty:
            df_cr_mov = df_cred_completo[df_cred_completo['VALOR DESPESA'] > 0].copy()
            if not df_cr_mov.empty:
                ultimas_cred = df_cr_mov.tail(5)[::-1]
                disp_cred = pd.DataFrame({
                    'Programa': ultimas_cred['PROGRAMA'],
                    'Empenho/Doc': ultimas_cred['EMPENHO'] + " / " + ultimas_cred['Nº DOCUMENTO'],
                    'Fornecedor': ultimas_cred['FORNECEDOR'],
                    'Valor Gasto': ultimas_cred['VALOR DESPESA']
                })
                st.dataframe(disp_cred.style.set_table_styles([
                    {'selector': 'th', 'props': [('background-color', '#065f46'), ('color', 'white'), ('font-weight', 'bold'), ('text-transform', 'uppercase'), ('font-size', '11px')]}
                ]).format({'Valor Gasto': fmt}), use_container_width=True, hide_index=True)
            else: st.info("Nenhuma despesa de crédito registrada.")
        else: st.info("Base de crédito vazia.")

elif st.session_state.pagina_atual == 'credito':
    st.button("⬅️ Voltar ao Menu Principal", on_click=mudar_pagina, args=('menu_principal',))
    st.markdown('<div class="header-container"><div class="main-title">Controle das Operações de Crédito</div></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="large")
    with c1:
        status_credito = att_cred if "Aguardando" not in att_cred else "Pendente de Conexão com Google Sheets"
        st.markdown(f"<div class='home-card' style='border-top-color: #3b82f6;'><span style='font-size: 50px; display:block; margin-bottom:10px;'>🏛️</span><div class='home-title'>Programa FINISA</div><div class='home-subtitle'>Info: {status_credito}</div></div>", unsafe_allow_html=True)
        st.button("Acessar FINISA", key="btn_finisa", use_container_width=True, type="primary", on_click=mudar_pagina, args=('finisa',))
    with c2:
        st.markdown(f"<div class='home-card' style='border-top-color: #10b981;'><span style='font-size: 50px; display:block; margin-bottom:10px;'>☀️</span><div class='home-title'>Usina Fotovoltaica</div><div class='home-subtitle'>Info: {status_credito}</div></div>", unsafe_allow_html=True)
        st.button("Acessar Usina", key="btn_usina", use_container_width=True, type="primary", on_click=mudar_pagina, args=('fotovoltaica',))

elif st.session_state.pagina_atual == 'finisa':
    st.button("⬅️ Voltar para Operações de Crédito", on_click=mudar_pagina, args=('credito',))
    st.markdown('<div class="header-container"><div class="main-title">🏦 Operação de Crédito: FINISA</div></div>', unsafe_allow_html=True)
    dados_abas, abas_disponiveis = processar_saldos_acumulados(df_finisa)
    if abas_disponiveis:
        abas_exibicao = list(reversed(abas_disponiveis))
        tabs_cred = st.tabs([f"📥 {aba}" for aba in abas_exibicao])
        for i, aba_nome in enumerate(abas_exibicao):
            with tabs_cred[i]:
                info = dados_abas[aba_nome]
                pct_gasta = (info['total_despesa'] / info['total_disponivel'] * 100) if info['total_disponivel'] > 0 else 0.0
                st.markdown(f"""<div class='kpi-row-container'><div class='kpi-card-head' style='border-left: 5px solid #059669;'><div class='kpi-label'>Recurso Disponível</div><div class='kpi-value'>{fmt(info['total_disponivel'])}</div><div style='font-size:11px; color:#64748b; margin-top:4px;'>Aporte Atual: {fmt(info['repasse_atual'])}<br>Saldo Anterior Remanescente: {fmt(info['saldo_anterior'])}</div></div><div class='kpi-card-head' style='border-left: 6px solid #dc2626;'><div class='kpi-label'>Total Despesas</div><div class='kpi-value' style='color:#dc2626;'>{fmt(info['total_despesa'])}</div></div><div class='kpi-card-head-blue'><div class='kpi-label'>Saldo Remanescente Atual</div><div class='w-value' style='font-size:24px; font-weight:800; color:#1e40af; margin-top:4px;'>{fmt(info['saldo_final'])}</div></div><div class='kpi-card-head' style='border-left: 5px solid #6366f1;'><div class='kpi-label'>% Utilizado do Saldo</div><div class='kpi-value' style='color:#6366f1;'>{pct_gasta:.2f}%</div></div></div>""", unsafe_allow_html=True)
                cg1, cg2 = st.columns(2)
                with cg1:
                    st.markdown("<div class='section-title' style='margin-top:0;'>📊 COMPOSIÇÃO DO SALDO DO PERÍODO</div>", unsafe_allow_html=True)
                    fig_rosca = go.Figure(data=[go.Pie(labels=['Gasto Liquidado', 'Saldo Disponível'], values=[info['total_despesa'], max(0.0, info['saldo_final'])], hole=.6, marker=dict(colors=['#ef4444', '#10b981']))])
                    fig_rosca.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), showlegend=True, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_rosca, use_container_width=True)
                with cg2:
                    st.markdown("<div class='section-title' style='margin-top:0;'>📊 DESPESAS POR DESCRIÇÃO</div>", unsafe_allow_html=True)
                    df_desc = info['df_filtrado'][info['df_filtrado']['VALOR DESPESA'] > 0].groupby('DESCRIÇÃO')['VALOR DESPESA'].sum().reset_index()
                    if not df_desc.empty:
                        fig_bar_desc = go.Figure(go.Bar(x=df_desc['VALOR DESPESA'], y=df_desc['DESCRIÇÃO'], orientation='h', marker_color='#3b82f6', text=[fmt(v) for v in df_desc['VALOR DESPESA']], textposition='auto'))
                        fig_bar_desc.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig_bar_desc, use_container_width=True)
                    else: st.info("Sem despesas registradas.")
                st.markdown("<div class='section-title'>📋 Detalhes Fiscais das Despesas Liquidadas</div>", unsafe_allow_html=True)
                df_exibicao = pd.DataFrame({'Empenho': info['df_filtrado']['EMPENHO'], 'Fornecedor': info['df_filtrado']['FORNECEDOR'], 'Tipo Doc': info['df_filtrado']['TIPO DE DOCUMENTO'], 'Nº Doc': info['df_filtrado']['Nº DOCUMENTO'], 'Descrição': info['df_filtrado']['DESCRIÇÃO'], 'Valor Despesa': info['df_filtrado']['VALOR DESPESA'], 'Visualizar': [gerar_botoes_documento(u, e, n, "abrir") for u, e, n in zip(info['df_filtrado']['LINK DOCUMENTO'], info['df_filtrado']['EMPENHO'], info['df_filtrado']['Nº DOCUMENTO'])], 'Download': [gerar_botoes_documento(u, e, n, "baixar") for u, e, n in zip(info['df_filtrado']['LINK DOCUMENTO'], info['df_filtrado']['EMPENHO'], info['df_filtrado']['Nº DOCUMENTO'])]})
                df_exibicao = df_exibicao[df_exibicao['Valor Despesa'] > 0]
                if not df_exibicao.empty: st.write(df_exibicao.style.format({'Valor Despesa': fmt}).to_html(escape=False, index=False, classes='extrato-table'), unsafe_allow_html=True)
                else: st.info("ℹ️ Nenhum gasto liquidado neste lote de recursos.")
    else: st.info("ℹ️ Você precisa ir na planilha e clicar em 'Sincronizar Créditos com GitHub' para criar os dados desta aba.")

elif st.session_state.pagina_atual == 'fotovoltaica':
    st.button("⬅️ Voltar para Operações de Crédito", on_click=mudar_pagina, args=('credito',))
    st.markdown('<div class="header-container"><div class="main-title">☀️ Operação de Crédito: Usina Fotovoltaica</div></div>', unsafe_allow_html=True)
    dados_abas, abas_disponiveis = processar_saldos_acumulados(df_usina)
    if abas_disponiveis:
        abas_exibicao = list(reversed(abas_disponiveis))
        tabs_cred = st.tabs([f"📥 {aba}" for aba in abas_exibicao])
        for i, aba_nome in enumerate(abas_exibicao):
            with tabs_cred[i]:
                info = dados_abas[aba_nome]
                pct_gasta = (info['total_despesa'] / info['total_disponivel'] * 100) if info['total_disponivel'] > 0 else 0.0
                st.markdown(f"""<div class='kpi-row-container'><div class='kpi-card-head' style='border-left: 5px solid #059669;'><div class='kpi-label'>Recurso Disponível</div><div class='kpi-value'>{fmt(info['total_disponivel'])}</div><div style='font-size:11px; color:#64748b; margin-top:4px;'>Aporte Atual: {fmt(info['repasse_atual'])}<br><b>Saldo Anterior Remanescente:</b> {fmt(info['saldo_anterior'])}</div></div><div class='kpi-card-head' style='border-left: 5px solid #dc2626;'><div class='kpi-label'>Total Despesas</div><div class='kpi-value' style='color:#dc2626;'>{fmt(info['total_despesa'])}</div></div><div class='kpi-card-head-blue'><div class='kpi-label'>Saldo Remanescente Atual</div><div class='w-value' style='font-size:24px; font-weight:800; color:#1e40af; margin-top:4px;'>{fmt(info['saldo_final'])}</div></div><div class='kpi-card-head' style='border-left: 5px solid #6366f1;'><div class='kpi-label'>% Utilizado do Saldo</div><div class='kpi-value' style='color:#6366f1;'>{pct_gasta:.2f}%</div></div></div>""", unsafe_allow_html=True)
                cg1, cg2 = st.columns(2)
                with cg1:
                    st.markdown("<div class='section-title' style='margin-top:0;'>📊 COMPOSIÇÃO DO SALDO DO PERÍODO</div>", unsafe_allow_html=True)
                    fig_rosca = go.Figure(data=[go.Pie(labels=['Gasto Liquidado', 'Saldo Disponível'], values=[info['total_despesa'], max(0.0, info['saldo_final'])], hole=.6, marker=dict(colors=['#ef4444', '#10b981']))])
                    fig_rosca.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), showlegend=True, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_rosca, use_container_width=True)
                with cg2:
                    st.markdown("<div class='section-title' style='margin-top:0;'>📊 DESPESAS POR DESCRIÇÃO</div>", unsafe_allow_html=True)
                    df_desc = info['df_filtrado'][info['df_filtrado']['VALOR DESPESA'] > 0].groupby('DESCRIÇÃO')['VALOR DESPESA'].sum().reset_index()
                    if not df_desc.empty:
                        fig_bar_desc = go.Figure(go.Bar(x=df_desc['VALOR DESPESA'], y=df_desc['DESCRIÇÃO'], orientation='h', marker_color='#3b82f6', text=[fmt(v) for v in df_desc['VALOR DESPESA']], textposition='auto'))
                        fig_bar_desc.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig_bar_desc, use_container_width=True)
                    else: st.info("Sem despesas registradas.")
                st.markdown("<div class='section-title'>📋 Detalhes Fiscais das Despesas Liquidadas</div>", unsafe_allow_html=True)
                df_exibicao = pd.DataFrame({'Empenho': info['df_filtrado']['EMPENHO'], 'Fornecedor': info['df_filtrado']['FORNECEDOR'], 'Tipo Doc': info['df_filtrado']['TIPO DE DOCUMENTO'], 'Nº Doc': info['df_filtrado']['Nº DOCUMENTO'], 'Descrição': info['df_filtrado']['DESCRIÇÃO'], 'Valor Despesa': info['df_filtrado']['VALOR DESPESA'], 'Visualizar': [gerar_botoes_documento(u, e, n, "abrir") for u, e, n in zip(info['df_filtrado']['LINK DOCUMENTO'], info['df_filtrado']['EMPENHO'], info['df_filtrado']['Nº DOCUMENTO'])], 'Download': [gerar_botoes_documento(u, e, n, "baixar") for u, e, n in zip(info['df_filtrado']['LINK DOCUMENTO'], info['df_filtrado']['EMPENHO'], info['df_filtrado']['Nº DOCUMENTO'])]})
                df_exibicao = df_exibicao[df_exibicao['Valor Despesa'] > 0]
                if not df_exibicao.empty: st.write(df_exibicao.style.format({'Valor Despesa': fmt}).to_html(escape=False, index=False, classes='extrato-table'), unsafe_allow_html=True)
                else: st.info("ℹ️ Nenhum gasto liquidado neste lote de recursos.")
    else: st.info("ℹ️ Você precisa ir na planilha e clicar em 'Sincronizar Créditos com GitHub' para criar os dados desta aba.")

elif st.session_state.pagina_atual == 'convenios':
    st.button("⬅️ Voltar ao Menu Principal", on_click=mudar_pagina, args=('menu_principal',))
    st.markdown('<div class="header-container"><div class="main-title">Divisão Controle Convênios</div></div>', unsafe_allow_html=True)
    if not df_conv.empty:
        df_conv_tela = df_conv.copy()
        st.markdown("<div class='section-title'>🔍 Busca Inteligente Global</div>", unsafe_allow_html=True)
        busca_global = st.text_input("Digite qualquer termo para pesquisar na base inteira:", placeholder="Ex: Nome de um analista, número SEI, secretaria, fonte...")
        if busca_global:
            mask = pd.Series(False, index=df_conv_tela.index)
            for col in df_conv_tela.columns: mask |= df_conv_tela[col].astype(str).str.contains(busca_global, case=False, na=False)
            df_conv_tela = df_conv_tela[mask]
            if df_conv_tela.empty: st.warning(f"⚠️ Nenhum registro encontrado contendo o termo: '{busca_global}'")
        if not df_conv_tela.empty:
            tab_conv_fonte, tab_conv_analista, tab_conv_busca, tab_conv_geral = st.tabs(["🎯 Por Fonte de Recurso", "👤 Por Analista", "🔍 Busca Detalhada", "📋 Base Completa"])
            with tab_conv_fonte:
                st.markdown("<div class='section-title'>🔍 Painel de Pesquisa por Fonte</div>", unsafe_allow_html=True)
                fontes_rec = sorted([str(f).strip() for f in df_conv_tela['FONTE DE RECURSO'].unique() if str(f).strip() not in ['', 'nan']])
                if fontes_rec:
                    # 💡 BARRA UNIFICADA DE FONTE EM CONVÊNIOS
                    f_final = st.selectbox("🎯 Escolha ou Digite a Fonte de Recurso:", options=fontes_rec, key="sel_f_conv")
                    if f_final:
                        df_filtro = df_conv_tela[df_conv_tela['FONTE DE RECURSO'] == f_final]
                        if not df_filtro.empty:
                            resp = df_filtro['RESPONSÁVEL'].iloc[0] if 'RESPONSÁVEL' in df_filtro.columns and str(df_filtro['RESPONSÁVEL'].iloc[0]) != '' else "NÃO INFORMADO"
                            st.markdown(f'''<div class='kpi-row-container'><div class='kpi-card-head-blue'><div class='kpi-label'>👤 Analista / Responsável</div><div class='kpi-value' style='color: #0f172a;'>{resp}</div></div></div>''', unsafe_allow_html=True)
                            st.dataframe(df_filtro, use_container_width=True, hide_index=True)
            with tab_conv_analista:
                st.markdown("<div class='section-title'>🔍 Painel de Pesquisa por Analista</div>", unsafe_allow_html=True)
                if 'RESPONSÁVEL' in df_conv_tela.columns:
                    analistas = sorted([str(a) for a in df_conv_tela['RESPONSÁVEL'].unique() if str(a) != ''])
                    if analistas:
                        # 💡 BARRA UNIFICADA DE ANALISTA EM CONVÊNIOS
                        a_final = st.selectbox("👤 Escolha ou Digite o Analista Responsável:", options=analistas, key="sel_a_conv")
                        if a_final:
                            df_filtro_a = df_conv_tela[df_conv_tela['RESPONSÁVEL'] == a_final]
                            st.markdown(f'''<div class='kpi-row-container'><div class='kpi-card-head-blue'><div class='kpi-label'>👤 Analista</div><div class='kpi-value' style='color: #0f172a;'>{a_final}</div></div><div class='kpi-card-head' style='border-left: 5px solid #059669;'><div class='kpi-label'>📋 Total Convênios</div><div class='kpi-value'>{len(df_filtro_a)}</div></div></div>''', unsafe_allow_html=True)
                            st.dataframe(df_filtro_a, use_container_width=True, hide_index=True)
            with tab_conv_busca:
                st.markdown("<div class='section-title'>🔍 Resultados da Busca</div>", unsafe_allow_html=True)
                st.dataframe(df_conv_tela, use_container_width=True, hide_index=True)
            with tab_conv_geral:
                st.markdown("<div class='section-title'>📊 Base de Dados Completa</div>", unsafe_allow_html=True)
                st.dataframe(df_conv_tela, use_container_width=True, hide_index=True)
    else: st.warning("A base de dados de convênios não foi localizada ou está vazia.")

elif st.session_state.pagina_atual == 'emendas':
    st.button("⬅️ Voltar ao Menu Principal", on_click=mudar_pagina, args=('menu_principal',))
    if not df.empty:
        fontes = sorted([f for f in df['fonte_clean'].unique() if f not in ['', 'nan']])
        st.markdown('''<div class="header-container"><div class="header-left"><div class="main-title">Controle de Emendas Orçamentárias</div></div><div class="header-right"><div class="status-dot"></div><div class="status-text">Base Google Sheets Conectada</div></div></div>''', unsafe_allow_html=True)
        
        tab_resumo, tab_ativa, tab_planos, tab_secretarias, tab_deputados, tab_geral = st.tabs([
            "🚀 Resumo Executivo", "🎯 Por Fonte", "📋 Por Plano", "🏛️ Por Secretaria", "🔍 Por Deputado", "🌐 Panorama Geral"
        ])
        
        with tab_resumo:
            st.markdown("<div class='section-title' style='font-size:18px;'>🚀 Painel de Desempenho das Emendas</div>", unsafe_allow_html=True)
            df_fontes = df.groupby('fonte_clean').agg({'repasse': 'sum', 'rendimento': 'sum', 'bruto': 'sum', 'deputado': 'first', 'secretaria': 'first'}).reset_index()
            df_fontes['saldo'] = df_fontes['repasse'] + df_fontes['rendimento'] - df_fontes['bruto']
            df_fontes['saldo_round'] = df_fontes['saldo'].round(2)
            
            df_top5 = df_fontes[df_fontes['saldo_round'] > 0].sort_values(by='saldo', ascending=False).head(5)
            df_aguardando = df_fontes[(df_fontes['repasse'] == 0) & (df_fontes['bruto'] == 0)]
            df_finalizadas = df_fontes[(df_fontes['saldo_round'] == 0) & ((df_fontes['repasse'] > 0) | (df_fontes['bruto'] > 0))]
            
            c_ag, c_fin = st.columns(2, gap="large")
            with c_ag:
                st.markdown(f'''<div class='kpi-card-head' style='border-left: 5px solid #f59e0b; margin-bottom: 15px;'><div class='kpi-label'>⏳ Aguardando Recursos (Zeradas)</div><div class='kpi-value' style='color:#f59e0b;'>{len(df_aguardando)} Emenda(s)</div></div>''', unsafe_allow_html=True)
                if not df_aguardando.empty:
                    df_ag_show = df_aguardando[['fonte_clean', 'deputado', 'secretaria']].rename(columns={'fonte_clean': 'FONTE', 'deputado': 'DEPUTADO', 'secretaria': 'SECRETARIA'})
                    df_ag_show['FONTE'] = df_ag_show['FONTE'].str.upper()
                    st.dataframe(df_ag_show.style.apply(style_row_warning, axis=1), use_container_width=True, hide_index=True, height=250)
                else: st.info("Nenhuma fonte aguardando recursos.")

            with c_fin:
                st.markdown(f'''<div class='kpi-card-head' style='border-left: 5px solid #3b82f6; margin-bottom: 15px;'><div class='kpi-label'>✅ Emendas Finalizadas</div><div class='kpi-value' style='color:#3b82f6;'>{len(df_finalizadas)} Emenda(s)</div></div>''', unsafe_allow_html=True)
                if not df_finalizadas.empty:
                    df_fin_show = df_finalizadas[['fonte_clean', 'deputado', 'bruto']].rename(columns={'fonte_clean': 'FONTE', 'deputado': 'DEPUTADO', 'bruto': 'TOTAL EXECUTADO'})
                    df_fin_show['FONTE'] = df_fin_show['FONTE'].str.upper()
                    st.dataframe(df_fin_show.style.format({'TOTAL EXECUTADO': fmt}).apply(highlight_total_azul, subset=['TOTAL EXECUTADO']), use_container_width=True, hide_index=True, height=250)
                else: st.info("Nenhuma fonte 100% executada no momento.")
            
            st.markdown("<div class='section-title'>🍩 Top 5 Fontes (Maior Saldo Disponível)</div>", unsafe_allow_html=True)
            if not df_top5.empty:
                cols = st.columns(len(df_top5))
                for i, (_, row) in enumerate(df_top5.iterrows()):
                    with cols[i]:
                        fig = go.Figure(data=[go.Pie(labels=['Gasto Liquidado', 'Saldo Disponível'], values=[row['bruto'], max(0, row['saldo'])], hole=0.6, marker=dict(colors=['#ef4444', '#10b981']), textinfo='none')])
                        fig.update_layout(title_text=f"Fonte: {str(row['fonte_clean']).upper()}", title_x=0.5, title_font_size=13, height=240, margin=dict(l=10, r=10, t=30, b=10), showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', annotations=[dict(text=f"<b style='color:#065f46;'>{fmt(row['saldo'])}</b>", x=0.5, y=0.5, showarrow=False, font=dict(size=12))])
                        st.plotly_chart(fig, use_container_width=True)
            else: st.info("Nenhuma fonte disponível.")

            st.markdown("<div class='section-title'>📋 Todas as Fontes Ativas (Ordem Decrescente de Saldo)</div>", unsafe_allow_html=True)
            df_todas = df_fontes.sort_values(by='saldo', ascending=False)
            df_todas_show = df_todas[['fonte_clean', 'secretaria', 'saldo']].rename(columns={'fonte_clean': 'FONTE', 'secretaria': 'SECRETARIA', 'saldo': 'SALDO DISPONÍVEL'})
            df_todas_show['FONTE'] = df_todas_show['FONTE'].str.upper()
            st.dataframe(df_todas_show.style.format({'SALDO DISPONÍVEL': fmt}).apply(highlight_saldo_verde, subset=['SALDO DISPONÍVEL']), use_container_width=True, hide_index=True, height=450)
                    
        with tab_ativa:
            st.markdown("<div class='section-title'>🎯 Seleção Unificada de Fonte</div>", unsafe_allow_html=True)
            if fontes:
                # 💡 BARRA UNIFICADA: POR FONTE
                fonte_final = st.selectbox("🎯 Selecione ou Digite o Número da Fonte Orçamentária:", options=fontes, key="sel_f")
                
                if fonte_final:
                    d_fin = df[df['fonte_clean'] == fonte_final]
                    anos = ["Exibir Histórico Acumulado Completo"] + sorted(list(set([str(a) for a in d_fin['ano_mov'].unique() if a not in ['', 'nan']])))
                    ano_sel = st.selectbox("📅 Exercício Fiscal:", options=anos, key="ano_f")
                    if not d_fin.empty:
                        d_fluxo = d_fin if  ano_sel == anos[0] else d_fin[d_fin['ano_mov'] ==  ano_sel]
                        d_saldo = d_fin if  ano_sel == anos[0] else d_fin[d_fin['ano_mov'].astype(int) <= int( ano_sel)]
                        conta = d_fin['conta corrente'].iloc[0]
                        d_bc = df[df['conta corrente'] == conta] if conta != "Não Informada" else pd.DataFrame()
                        d_bc_fluxo = d_bc if  ano_sel == anos[0] else (d_bc[d_bc['ano_mov'] ==  ano_sel] if not d_bc.empty else pd.DataFrame())
                        d_bc_saldo = d_bc if  ano_sel == anos[0] else (d_bc[d_bc['ano_mov'].astype(int) <= int( ano_sel)] if not d_bc.empty else pd.DataFrame())
                        
                        tot_ent = float(d_saldo['repasse'].sum() + d_saldo['rendimento'].sum())
                        tot_sai = float(d_saldo['bruto'].sum())
                        sal_fonte = tot_ent - tot_sai
                        pct_disp = (sal_fonte / tot_ent * 100) if tot_ent > 0 else 0.0
                        sal_banco = float(d_bc_saldo['repasse'].sum() + d_bc_saldo['rendimento'].sum()) - float(d_bc_saldo['bruto'].sum()) if not d_bc_saldo.empty else sal_fonte
                        lbl = "Histórico Total" if  ano_sel == anos[0] else f"Exercício {ano_sel}"
                        
                        st.markdown(f'''<div class='kpi-row-container'><div class='kpi-card-head' style='border-left: 5px solid #059669;'><div class='kpi-label'>🎯 Saldo Fonte</div><div class='kpi-value'>{fmt(sal_fonte)}</div></div><div class='kpi-card-head-blue'><div class='kpi-label'>🏦 Saldo Conta: {conta}</div><div class='kpi-value' style='color:#1e40af;'>{fmt(sal_banco)}</div></div><div class='kpi-card-head' style='border-left: 5px solid #6366f1;'><div class='kpi-label'>% Disponível</div><div class='kpi-value' style='color:#6366f1;'>{pct_disp:.2f}%</div></div></div>''', unsafe_allow_html=True)
                        st.markdown(f'''<div style='margin-bottom:10px;'><div class='meta-tag'>👤 Deputado: {d_fin['deputado'].unique()[0]}</div><div class='meta-tag'>📄 Emenda: {d_fin['emenda_clean'].unique()[0]}</div><div class='meta-tag'>🎯 Plano: {d_fin['plano_clean'].unique()[0]}</div></div>''', unsafe_allow_html=True)
                        
                        c_graf, c_tab = st.columns([1, 1])
                        with c_graf:
                            st.markdown("<div class='section-title' style='margin-top:0;'>📊 DESPESAS VS SALDO</div>", unsafe_allow_html=True)
                            fig_rosca_f = go.Figure(data=[go.Pie(labels=['Gasto Liquidado', 'Saldo Disponível'], values=[tot_sai, max(0.0, sal_fonte)], hole=.6, marker=dict(colors=['#ef4444', '#10b981']))])
                            fig_rosca_f.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), showlegend=True, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                            st.plotly_chart(fig_rosca_f, use_container_width=True)
                        
                        with c_tab:
                            st.markdown(f"<div class='section-title' style='margin-top:0;'>🌍 RESUMO ({lbl})</div>", unsafe_allow_html=True)
                            st.markdown(f'''<table class='extrato-table'><tr class='extrato-row'><td class='extrato-cell-label'>(+) REPASSE</td><td class='extrato-cell-val' style='color:#059669;'>{fmt(float(d_fluxo['repasse'].sum()))}</td></tr><tr class='extrato-row'><td class='extrato-cell-label'>(+) RENDIMENTOS</td><td class='extrato-cell-val' style='color:#2563eb;'>{fmt(float(d_fluxo['rendimento'].sum()))}</td></tr><tr class='extrato-row'><td>(-) DESPESAS</td><td class='extrato-cell-val' style='color:#dc2626;'>{fmt(float(d_fluxo['bruto'].sum()))}</td></tr><tr class='extrato-row-final'><td class='extrato-cell-label'>(=) SALDO REAL</td><td class='extrato-cell-val'>{fmt(sal_fonte)}</td></tr></table>''', unsafe_allow_html=True)
                        
                        secs = [s for s in d_fin['secretaria'].unique() if s != '']
                        if len(secs) > 1:
                            st.markdown(f"<div class='section-title'>🏢 Divisão por Secretaria</div>", unsafe_allow_html=True)
                            for sec in secs:
                                ds_f, ds_s = d_fluxo[d_fluxo['secretaria'] == sec], d_saldo[d_saldo['secretaria'] == sec]
                                st.markdown(f"<div class='secretaria-header'>🏛️ {sec}</div>", unsafe_allow_html=True)
                                st.markdown(f'''<table class='extrato-table'><tr class='extrato-row'><td class='extrato-cell-label'>(+) REPASSE</td><td class='extrato-cell-val' style='color:#059669;'>{fmt(float(ds_f['repasse'].sum()))}</td></tr><tr class='extrato-row'><td class='extrato-cell-label'>(+) RENDIMENTOS</td><td class='extrato-cell-val' style='color:#2563eb;'>{fmt(float(ds_f['rendimento'].sum()))}</td></tr><tr class='extrato-row'><td class='extrato-cell-label'>(-) DESPESAS</td><td class='extrato-cell-val' style='color:#dc2626;'>{fmt(float(ds_f['bruto'].sum()))}</td></tr><tr class='extrato-row-final'><td class='extrato-cell-label'>(=) SALDO LIVRE</td><td class='extrato-cell-val'>{fmt(float(ds_s['repasse'].sum() + ds_s['rendimento'].sum()) - float(ds_s['bruto'].sum()))}</td></tr></table>''', unsafe_allow_html=True)

                        if conta != "Não Informada" and not d_bc_saldo.empty:
                            st.markdown(f"<div class='section-title'>⚖️ ABERTURA DE SALDOS — CONTA: {conta}</div>", unsafe_allow_html=True)
                            f_comp = sorted([fc for fc in d_bc_saldo['fonte_clean'].unique() if fc != '']); l_bc = []; tr, trn, tg, ts = 0.0, 0.0, 0.0, 0.0
                            for fi in f_comp:
                                di_f = d_bc_fluxo[d_bc_fluxo['fonte_clean'] == fi] if not d_bc_fluxo.empty else pd.DataFrame()
                                fr, frn, fd = float(di_f['repasse'].sum() if not di_f.empty else 0), float(di_f['rendimento'].sum() if not di_f.empty else 0), float(di_f['bruto'].sum() if not di_f.empty else 0)
                                di_s = d_bc_saldo[d_bc_saldo['fonte_clean'] == fi]; fs = float(di_s['repasse'].sum() + di_s['rendimento'].sum() - di_s['bruto'].sum()); tr += fr; trn += frn; tg += fd; ts += fs
                                l_bc.append({'Fonte Orçamentária': fi.upper() + (" (Ativa)" if fi == fonte_final else ""), 'Repasses': fr, 'Rendimentos': frn, 'Despesas': fd, 'Saldo Real': fs})
                            l_bc.append({'Fonte Orçamentária': 'TOTAL CONTA 🏦', 'Repasses': tr, 'Rendimentos': trn, 'Despesas': tg, 'Saldo Real': ts})
                            st.dataframe(pd.DataFrame(l_bc).style.apply(style_abertura_banco, axis=1).format({'Repasses': fmt, 'Rendimentos': fmt, 'Despesas': fmt, 'Saldo Real': fmt}), use_container_width=True, hide_index=True)
                        
                        st.markdown(f"<div class='section-title'>📋 Lançamentos do Período</div>", unsafe_allow_html=True)
                        d_val = d_fluxo[d_fluxo['EMPENHO_COL'] != '-']
                        if not d_val.empty:
                            df_rnd = pd.DataFrame({'Data': d_val['DATA_LANCAMENTO'], 'Empenho': d_val['EMPENHO_COL'], 'NF': d_val['NOTA_COL'], 'Valor NF': d_val['bruto'], 'PDF': [gerar_botoes_documento(u, e, n, "abrir") for u, e, n in zip(d_val['URL_REAL_LINK'], d_val['EMPENHO_COL'], d_val['NOTA_COL'])], 'Download': [gerar_botoes_documento(u, e, n, "baixar") for u, e, n in zip(d_val['URL_REAL_LINK'], d_val['EMPENHO_COL'], d_val['NOTA_COL'])]})
                            st.write(df_rnd.style.format({'Valor NF': fmt}).to_html(escape=False, index=False, classes='extrato-table'), unsafe_allow_html=True)
                        else: st.info("Nenhum lançamento no período.")

        with tab_planos:
            st.markdown("<div class='section-title'>📋 Seleção Unificada de Plano</div>", unsafe_allow_html=True)
            planos = sorted([str(p).upper() for p in df['plano_clean'].unique() if str(p).strip() not in ['', 'nan']])
            if planos:
                # 💡 BARRA UNIFICADA: POR PLANO
                p_fin = st.selectbox("📋 Selecione ou Digite o Número do Plano:", options=planos, key="sel_p")
                
                if p_fin:
                    dp = df[df['plano_clean'].str.upper() == p_fin]
                    anos_p = ["Exibir Histórico Acumulado Completo"] + sorted(list(set([str(a) for a in dp['ano_mov'].unique() if a not in ['', 'nan'] ])))
                    ano_p = st.selectbox("📅 Exercício Fiscal:", options=anos_p, key="ano_p")
                    if not dp.empty:
                        lbl_p = "Histórico Total" if  ano_p ==  anos_p[0] else f"Exercício {ano_p}"
                        dp_f = dp if  ano_p ==  anos_p[0] else dp[dp['ano_mov'] ==  ano_p]; dp_s = dp if  ano_p ==  anos_p[0] else dp[dp['ano_mov'].astype(int) <= int( ano_p)]
                        tot_ent_p = float(dp_s['repasse'].sum() + dp_s['rendimento'].sum()); tot_sai_p = float(dp_s['bruto'].sum()); sal_p = tot_ent_p - tot_sai_p
                        pct_disp_p = (sal_p / tot_ent_p * 100) if tot_ent_p > 0 else 0.0

                        st.markdown(f'''<div class='kpi-row-container'><div class='kpi-card-head-blue'><div class='kpi-label'>📋 Plano Ativo</div><div class='kpi-value' style='color:#1e40af;'>{p_fin}</div></div><div class='kpi-card-head' style='border-left: 5px solid #059669;'><div class='kpi-label'>💰 Saldo</div><div class='kpi-value'>{fmt(sal_p)}</div></div><div class='kpi-card-head' style='border-left: 5px solid #6366f1;'><div class='kpi-label'>% Disponível</div><div class='kpi-value' style='color:#6366f1;'>{pct_disp_p:.2f}%</div></div></div>''', unsafe_allow_html=True)
                        st.markdown(f'''<div style='margin-bottom:15px;'><div class='meta-tag'>🎯 Fontes: {", ".join([f.upper() for f in sorted(dp['fonte_clean'].unique())])}</div><div class='meta-tag'>👤 Deputado: {dp['deputado'].unique()[0]}</div><div class='meta-tag'>🏦 Conta: {dp['conta corrente'].iloc[0]}</div></div>''', unsafe_allow_html=True)
                        
                        c_graf_p, c_tab_p = st.columns([1, 1])
                        with c_graf_p:
                            st.markdown("<div class='section-title' style='margin-top:0;'>📊 DESPESAS VS SALDO</div>", unsafe_allow_html=True)
                            fig_rosca_p = go.Figure(data=[go.Pie(labels=['Gasto Liquidado', 'Saldo Disponível'], values=[tot_sai_p, max(0.0, sal_p)], hole=.6, marker=dict(colors=['#ef4444', '#10b981']))])
                            fig_rosca_p.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), showlegend=True, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                            st.plotly_chart(fig_rosca_p, use_container_width=True)

                        with c_tab_p:
                            st.markdown(f"<div class='section-title' style='margin-top:0;'>🌍 RESUMO ({lbl_p})</div>", unsafe_allow_html=True)
                            secs_p = sorted([str(s) for s in dp['secretaria'].unique() if str(s).strip() not in ['', 'nan', 'NÃO ESPECIFICADA']]) or ['NÃO ESPECIFICADA']
                            html_p = f"<table class='extrato-table'><thead><tr><th>DESCRIÇÃO</th>" + "".join([f"<th style='text-align: right;'>{s}</th>" for s in secs_p]) + "<th style='text-align: right;'>TOTAL</th></tr></thead><tbody>"
                            html_p += "<tr class='extrato-row'><td class='extrato-cell-label'>(+) REPASSE</td>" + "".join([f"<td class='extrato-cell-val' style='color:#059669;'>{fmt(float(dp_f[dp_f['secretaria'] == s]['repasse'].sum()))}</td>" for s in secs_p]) + f"<td class='extrato-cell-val' style='color:#059669;'>{fmt(float(dp_f['repasse'].sum()))}</td></tr>"
                            html_p += "<tr class='extrato-row'><td class='extrato-cell-label'>(+) RENDIMENTOS</td>" + "".join([f"<td class='extrato-cell-val' style='color:#2563eb;'>{fmt(float(dp_f[dp_f['secretaria'] == s]['rendimento'].sum()))}</td>" for s in secs_p]) + f"<td class='extrato-cell-val' style='color:#2563eb;'>{fmt(float(dp_f['rendimento'].sum()))}</td></tr>"
                            html_p += "<tr class='extrato-row'><td class='extrato-cell-label'>(-) DESPESAS</td>" + "".join([f"<td class='extrato-cell-val' style='color:#dc2626;'>{fmt(float(dp_f[dp_f['secretaria'] == s]['bruto'].sum()))}</td>" for s in secs_p]) + f"<td class='extrato-cell-val' style='color:#dc2626;'>{fmt(float(dp_f['bruto'].sum()))}</td></tr>"
                            html_p += "<tr class='extrato-row-final'><td class='extrato-cell-label'>(=) SALDO DISPONÍVEL</td>" + "".join([f"<td class='extrato-cell-val'>{fmt(float(dp_s[dp_s['secretaria'] == s]['repasse'].sum() + dp_s[dp_s['secretaria'] == s]['rendimento'].sum() - dp_s[dp_s['secretaria'] == s]['bruto'].sum()))}</td>" for s in secs_p]) + f"<td class='extrato-cell-val' style='font-size:15px;'>{fmt(sal_p)}</td></tr></tbody></table>"
                            st.markdown(html_p, unsafe_allow_html=True)
                        
                        st.markdown(f"<div class='section-title'>📋 Lançamentos do Plano</div>", unsafe_allow_html=True)
                        dp_val = dp_f[dp_f['EMPENHO_COL'] != '-']
                        if not dp_val.empty:
                            df_rp = pd.DataFrame({'Data': dp_val['DATA_LANCAMENTO'], 'Empenho': dp_val['EMPENHO_COL'], 'NF': dp_val['NOTA_COL'], 'Secretaria': dp_val['secretaria'], 'Valor NF': dp_val['bruto'], 'PDF': [gerar_botoes_documento(u, e, n, "abrir") for u, e, n in zip(dp_val['URL_REAL_LINK'], dp_val['EMPENHO_COL'], dp_val['NOTA_COL'])], 'Download': [gerar_botoes_documento(u, e, n, "baixar") for u, e, n in zip(dp_val['URL_REAL_LINK'], dp_val['EMPENHO_COL'], dp_val['NOTA_COL'])]})
                            st.write(df_rp.style.format({'Valor NF': fmt}).to_html(escape=False, index=False, classes='extrato-table'), unsafe_allow_html=True)
                        else: st.info("Nenhum lançamento no período.")

        with tab_secretarias:
            st.markdown("<div class='section-title'>🏛️ Seleção Unificada de Secretaria</div>", unsafe_allow_html=True)
            secs = sorted([str(s) for s in df['secretaria'].unique() if str(s).strip() not in ['', 'nan', 'NÃO ESPECIFICADA']])
            if secs:
                # 💡 BARRA UNIFICADA: POR SECRETARIA
                s_fin = st.selectbox("🏛️ Selecione ou Digite o Nome da Secretaria Executiva:", options=secs, key="sel_s")
                
                if s_fin:
                    ds = df[df['secretaria'] == s_fin]
                    anos_s = ["Exibir Histórico Acumulado Completo"] + sorted(list(set([str(a) for a in ds['ano_mov'].unique() if a not in ['', 'nan'] ])))
                    ano_s = st.selectbox("📅 Exercício Fiscal:", options=anos_s, key="ano_s")
                    if not ds.empty:
                        lbl_s = "Histórico Total" if  ano_s ==  anos_s[0] else f"Exercício {ano_s}"
                        ds_f = ds if  ano_s ==  anos_s[0] else ds[ds['ano_mov'] ==  ano_s]; ds_s = ds if  ano_s ==  anos_s[0] else ds[ds['ano_mov'].astype(int) <= int( ano_s)]
                        tot_ent_s = float(ds_s['repasse'].sum() + ds_s['rendimento'].sum()); tot_sai_s = float(ds_s['bruto'].sum()); sal_s = tot_ent_s - tot_sai_s
                        pct_disp_s = (sal_s / tot_ent_s * 100) if tot_ent_s > 0 else 0.0
                        
                        st.markdown(f'''<div class='kpi-row-container'><div class='kpi-card-head-blue'><div class='kpi-label'>🏛️ Secretaria</div><div class='kpi-value' style='color:#1e40af;'>{s_fin}</div></div><div class='kpi-card-head' style='border-left: 5px solid #059669;'><div class='kpi-label'>💰 Saldo</div><div class='kpi-value'>{fmt(sal_s)}</div></div><div class='kpi-card-head' style='border-left: 5px solid #6366f1;'><div class='kpi-label'>% Disponível</div><div class='kpi-value' style='color:#6366f1;'>{pct_disp_s:.2f}%</div></div></div>''', unsafe_allow_html=True)

                        c_graf_s, c_tab_s = st.columns([1, 1])
                        with c_graf_s:
                            st.markdown("<div class='section-title' style='margin-top:0;'>📊 DESPESAS VS SALDO</div>", unsafe_allow_html=True)
                            fig_rosca_s = go.Figure(data=[go.Pie(labels=['Gasto Liquidado', 'Saldo Disponível'], values=[tot_sai_s, max(0.0, sal_s)], hole=.6, marker=dict(colors=['#ef4444', '#10b981']))])
                            fig_rosca_s.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), showlegend=True, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                            st.plotly_chart(fig_rosca_s, use_container_width=True)

                        with c_tab_s:
                            st.markdown(f"<div class='section-title' style='margin-top:0;'>🌍 EXTRATO DA PASTA ({lbl_s})</div>", unsafe_allow_html=True)
                            st.markdown(f'''<table class='extrato-table'><tr class='extrato-row'><td class='extrato-cell-label'>(+) REPASSES TOTAIS</td><td class='extrato-cell-val' style='color:#059669;'>{fmt(float(ds_f['repasse'].sum()))}</td></tr><tr class='extrato-row'><td class='extrato-cell-label'>(+) RENDIMENTOS TOTAIS</td><td class='extrato-cell-val' style='color:#2563eb;'>{fmt(float(ds_f['rendimento'].sum()))}</td></tr><tr class='extrato-row'><td>(-) DESPESAS TOTAIS</td><td class='extrato-cell-val' style='color:#dc2626;'>{fmt(float(ds_f['bruto'].sum()))}</td></tr><tr class='extrato-row-final'><td class='extrato-cell-label'>(=) SALDO LIVRE DA PASTA</td><td class='extrato-cell-val' style='font-size:15px;'>{fmt(sal_s)}</td></tr></table>''', unsafe_allow_html=True)

                        st.markdown(f"<div class='section-title'>⚖️ Detalhamento por Fonte de Recurso</div>", unsafe_allow_html=True)
                        fontes_da_secretaria = sorted([f for f in ds_s['fonte_clean'].unique() if f != '']); linhas_fontes_sec = []
                        for fi in fontes_da_secretaria:
                            df_i_fluxo = ds_f[ds_f['fonte_clean'] == fi]; df_i_saldo = ds_s[ds_s['fonte_clean'] == fi]
                            linhas_fontes_sec.append({'Fonte Vinculada': fi.upper(), 'Repasses': float(df_i_fluxo['repasse'].sum()), 'Rendimentos': float(df_i_fluxo['rendimento'].sum()), 'Despesas': float(df_i_fluxo['bruto'].sum()), 'Saldo Livre': float(df_i_saldo['repasse'].sum() + df_i_saldo['rendimento'].sum() - df_i_saldo['bruto'].sum())})
                        if linhas_fontes_sec:
                            st.dataframe(pd.DataFrame(linhas_fontes_sec).style.format({'Repasses': fmt, 'Rendimentos': fmt, 'Despesas': fmt, 'Saldo Livre': fmt}).apply(highlight_saldo_verde, subset=['Saldo Livre']), use_container_width=True, hide_index=True)
        
        with tab_deputados:
            st.markdown("<div class='section-title'>🔍 Seleção Unificada de Parlamentar</div>", unsafe_allow_html=True)
            deps = sorted([str(d) for d in df['deputado'].unique() if str(d).strip() not in ['', 'nan', 'NÃO INFORMADO']])
            if deps:
                # 💡 BARRA UNIFICADA: POR DEPUTADO
                d_fin = st.selectbox("👤 Selecione ou Digite o Nome do Deputado/Parlamentar:", options=deps, key="sel_d")
                
                if d_fin:
                    dd = df[df['deputado'] == d_fin]
                    anos_d = ["Exibir Histórico Acumulado Completo"] + sorted(list(set([str(a) for a in dd['ano_mov'].unique() if a not in ['', 'nan'] ])))
                    ano_d = st.selectbox("📅 Exercício Fiscal:", options=anos_d, key="ano_d")
                    if not dd.empty:
                        lbl_d = "Histórico Total" if   ano_d ==  anos_d[0] else f"Exercício {ano_d}"
                        dd_f = dd if   ano_d ==  anos_d[0] else dd[dd['ano_mov'] ==   ano_d]; dd_s = dd if   ano_d ==  anos_d[0] else dd[dd['ano_mov'].astype(int) <= int(  ano_d)]
                        tot_ent_d = float(dd_s['repasse'].sum() + dd_s['rendimento'].sum()); tot_sai_d = float(dd_s['bruto'].sum()); sal_d = tot_ent_d - tot_sai_d
                        pct_disp_d = (sal_d / tot_ent_d * 100) if tot_ent_d > 0 else 0.0

                        st.markdown(f'''<div class='kpi-row-container'><div class='kpi-card-head-blue'><div class='kpi-label'>👤 Parlamentar</div><div class='kpi-value' style='color:#1e40af;'>{d_fin}</div></div><div class='kpi-card-head' style='border-left: 5px solid #059669;'><div class='kpi-label'>💰 Saldo Consolidado</div><div class='kpi-value'>{fmt(sal_d)}</div></div><div class='kpi-card-head' style='border-left: 5px solid #6366f1;'><div class='kpi-label'>% Disponível</div><div class='kpi-value' style='color:#6366f1;'>{pct_disp_d:.2f}%</div></div></div>''', unsafe_allow_html=True)
                        
                        c_graf_d, c_tab_d = st.columns([1, 1])
                        with c_graf_d:
                            st.markdown("<div class='section-title' style='margin-top:0;'>📊 DESPESAS VS SALDO</div>", unsafe_allow_html=True)
                            fig_rosca_d = go.Figure(data=[go.Pie(labels=['Gasto Liquidado', 'Saldo Disponível'], values=[tot_sai_d, max(0.0, sal_d)], hole=.6, marker=dict(colors=['#ef4444', '#10b981']))])
                            fig_rosca_d.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), showlegend=True, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                            st.plotly_chart(fig_rosca_d, use_container_width=True)

                        with c_tab_d:
                            st.markdown(f"<div class='section-title' style='margin-top:0;'>🌍 EXTRATO CONSOLIDADO</div>", unsafe_allow_html=True)
                            st.markdown(f'''<table class='extrato-table'><tr class='extrato-row'><td class='extrato-cell-label'>(+) REPASSES TOTAIS</td><td class='extrato-cell-val' style='color:#059669;'>{fmt(float(dd_f['repasse'].sum()))}</td></tr><tr class='extrato-row'><td class='extrato-cell-label'>(+) RENDIMENTOS TOTAIS</td><td class='extrato-cell-val' style='color:#2563eb;'>{fmt(float(dd_f['rendimento'].sum()))}</td></tr><tr class='extrato-row'><td>(-) DESPESAS TOTAIS</td><td class='extrato-cell-val' style='color:#dc2626;'>{fmt(float(dd_f['bruto'].sum()))}</td></tr><tr class='extrato-row-final'><td class='extrato-cell-label'>(=) SALDO LÍQUIDO GERAL</td><td class='extrato-cell-val' style='font-size:15px;'>{fmt(sal_d)}</td></tr></table>''', unsafe_allow_html=True)
                        
                        st.markdown(f"<div class='section-title'>⚖️ Onde o recurso foi aplicado</div>", unsafe_allow_html=True)
                        grupo_deputado = dd_s.groupby(['fonte_clean', 'secretaria']); linhas_detalhe_dep = []
                        for (fi, sec), df_grupo_saldo in grupo_deputado:
                            if fi == '': continue
                            df_grupo_fluxo = dd_f[(dd_f['fonte_clean'] == fi) & (dd_f['secretaria'] == sec)]
                            linhas_detalhe_dep.append({'Fonte Vinculada': fi.upper(), 'Secretaria': sec.upper(), 'Repasses': float(df_grupo_fluxo['repasse'].sum()), 'Rendimentos': float(df_grupo_fluxo['rendimento'].sum()), 'Despesas': float(df_grupo_fluxo['bruto'].sum()), 'Saldo Específico': float(df_grupo_saldo['repasse'].sum() + df_grupo_saldo['rendimento'].sum() - df_grupo_saldo['bruto'].sum())})
                        if linhas_detalhe_dep: 
                            st.dataframe(pd.DataFrame(linhas_detalhe_dep).style.format({'Repasses': fmt, 'Rendimentos': fmt, 'Despesas': fmt, 'Saldo Específico': fmt}).apply(highlight_saldo_verde, subset=['Saldo Específico']), use_container_width=True, hide_index=True)
        
        with tab_geral:
            st.markdown("<div class='section-title'>📊 BALANÇOS CONSOLIDADOS</div>", unsafe_allow_html=True)
            df_g_sec = df[df['secretaria'] != 'NÃO ESPECIFICADA'].groupby('secretaria').agg({'repasse':'sum', 'rendimento':'sum', 'bruto':'sum'}).reset_index()
            df_g_sec['saldo'] = df_g_sec['repasse'] + df_g_sec['rendimento'] - df_g_sec['bruto']
            df_g_dep = df[df['deputado'] != 'NÃO INFORMADO'].groupby('deputado').agg({'repasse':'sum', 'rendimento':'sum', 'bruto':'sum'}).reset_index()
            df_g_dep['saldo'] = df_g_dep['repasse'] + df_g_dep['rendimento'] - df_g_dep['bruto']
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("<b>🏛️ SALDO POR SECRETARIA:</b>", unsafe_allow_html=True)
                fig1 = go.Figure(go.Bar(x=df_g_sec['secretaria'], y=df_g_sec['saldo'], marker_color='#3b82f6', text=[fmt(v) for v in df_g_sec['saldo']], textposition='auto'))
                fig1.update_layout(height=300, margin=dict(l=10,r=10,t=30,b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig1, use_container_width=True)
            with c2:
                st.markdown("<b>👤 SALDO POR DEPUTADO:</b>", unsafe_allow_html=True)
                fig2 = go.Figure(go.Bar(x=df_g_dep['deputado'], y=df_g_dep['saldo'], marker_color='#8b5cf6', text=[fmt(v) for v in df_g_dep['saldo']], textposition='auto'))
                fig2.update_layout(height=300, margin=dict(l=10,r=10,t=30,b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig2, use_container_width=True)
