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
    nfkd_form = unicodedata.normalize('NFKD', texto_limpo)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

# 2. INTERFACE VISUAL (CSS)
st.markdown("""<style>
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
    .extrato-row-final { background-color: #f8fafc; font-weight: 800; border-top: 2px solid #000000; }
    .extrato-cell-label { padding: 10px 15px; font-size: 12px; font-weight: 700; color: #0f172a; text-align: left; }
    .extrato-cell-val { padding: 10px 15px; font-size: 13px; font-weight: 800; text-align: right; white-space: nowrap; }
    .btn-download-direto { background-color: #e2e8f0; color: #0f172a !important; text-decoration: none !important; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 700; border: 1px solid #cbd5e1; display: inline-block; transition: all 0.2s ease; text-transform: uppercase; }
    .btn-download-direto:hover { background-color: #cbd5e1; color: #000000 !important; border-color: #94a3b8; }
    .link-abrir-doc { color: #2563eb !important; text-decoration: none !important; font-size: 12px; font-weight: 700; }
    .link-abrir-doc:hover { text-decoration: underline !important; color: #1d4ed8 !important; }
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
        else:
            return pd.DataFrame(), "Indisponível"
            
    if df_raw.empty:
        return pd.DataFrame(), "Base Vazia"

    df = pd.DataFrame()
    col_orig = {re.sub(r'[^\w\s]', '', str(c).strip().lower()).replace('â', 'a').replace('ç', 'c').replace('ã', 'a').replace('ó', 'o'): c for c in df_raw.columns}
    
    def ext(chave):
        c_real = next((o for l, o in col_orig.items() if chave in l), None)
        if c_real:
            return [str(i).strip() if str(i).strip().lower() not in ['', 'nan'] else '' for i in df_raw[c_real]]
        return [''] * len(df_raw)
    
    df['fonte_clean'] = [str(f).split('.')[0].lower().replace('-', '').strip() for f in ext('fonte')]
    df['emenda_clean'] = [str(e).split('.')[0].strip() for e in ext('emenda')]
    df['plano_clean'] = [str(p).split('.')[0].upper().strip() for p in ext('plano')]
    df['EMPENHO_COL'] = [x if x != '' else '-' for x in ext('empenho')]
    df['NOTA_COL'] = [x if x != '' else '-' for x in ext('nota')]
    
    url_items = [''] * len(df_raw)
    for c in ['urllink', 'url', 'link', 'comprovante', 'pdf']:
        c_achada = next((o for l, o in col_orig.items() if c in l), None)
        if c_achada:
            url_items = [str(i).strip() for i in df_raw[c_achada]]
            break
            
    df['URL_REAL_LINK'] = [lk if re.match(r'^(http|https|www\.)', lk, re.IGNORECASE) else ("https://" + lk if '.' in lk and lk.lower() not in ['nan','','-'] else '') for lk in url_items]
    
    df['secretaria'] = [x if x != '' else 'Não Especificada' for x in ext('secretaria')]
    df['deputado'] = [x if x != '' else 'Não Informado' for x in ext('deputado')]
    df['desc_clean'] = [x if x != '' else 'Sem descrição informada' for x in ext('descricao')]
    df['conta corrente'] = [x if x != '' else 'Não Informada' for x in ext('conta')]
    df['ano_mov'] = [re.search(r'(20\d{2})', str(d)).group(1) if re.search(r'(20\d{2})', str(d)) else '2025' for d in ext('data')]
    df['DATA_LANCAMENTO'] = ext('data')
    
    def limpar_moeda(val):
        v_str = str(val).upper().replace('R$', '').strip()
        if not v_str or v_str == '-' or v_str == 'NAN': return 0.0
        if '.' in v_str and ',' in v_str: v_str = v_str.replace('.', '').replace(',', '.')
        elif ',' in v_str: v_str = v_str.replace(',', '.')
        try: return float(v_str)
        except ValueError: return 0.0

    for c in ['repasse', 'rendimento', 'bruto']:
        df[c] = [limpar_moeda(v) for v in ext(c)]
        
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
        else:
            return pd.DataFrame(), "Indisponível"
            
    if not d.empty:
        d.columns = [str(c).strip() for c in d.columns]
        if 'RESPONSÁVEL' in d.columns: 
            d['RESPONSÁVEL'] = d['RESPONSÁVEL'].apply(normalizar_texto)
    return d, att

df, att_emendas = obter_base_dados_global()
df_conv, att_convenios = obter_base_convenios()

def fmt(v): 
    val = float(v)
    if round(val, 2) == 0: 
        val = 0.0
    return f"R$ {val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def gerar_botoes_documento(url, emp, nota, tipo="abrir"):
    if not url or url == '': return '-'
    if tipo == "baixar" and "drive.google.com" in url and "/file/d/" in url: 
        url = f"https://drive.google.com/uc?export=download&id={url.split('/file/d/')[1].split('/')[0]}"
    if tipo == "abrir": 
        return f'<a href="{url}" target="_blank" class="link-abrir-doc">Visualizar 🔗</a>'
    nome = f"Nota_Fiscal_{nota}.pdf" if nota not in ['-',''] else (f"Empenho_{emp}.pdf" if emp not in ['-',''] else "documento.pdf")
    return f'<a href="{url}" download="{nome}" class="btn-download-direto">Baixar 💾</a>'

# ==============================================================================
# ROTEAMENTO DAS TELAS
# ==============================================================================

if st.session_state.pagina_atual == 'menu_principal':
    st.markdown("""<div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 70px 20px; border-radius: 16px; text-align: center; margin-top: 20px; margin-bottom: 50px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1); border-top: 5px solid #3b82f6;"><h1 style="font-size: 54px; font-weight: 900; color: #ffffff; margin: 0; letter-spacing: -1.5px; text-transform: uppercase;">Controle Convênios</h1></div>""", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3, gap="large")
    with c1:
        st.markdown(f"<div class='home-card'><span style='font-size: 50px;'>📊</span><div class='home-title'>Emendas Orçamentárias</div><div class='home-subtitle'>🔄 Atualizado em: {att_emendas}</div></div>", unsafe_allow_html=True)
        st.button("Acessar Módulo", key="btn_emendas", use_container_width=True, type="primary", on_click=mudar_pagina, args=('emendas',))
    with c2:
        st.markdown("<div class='home-card'><span style='font-size: 50px;'>🏦</span><div class='home-title'>Operações de Crédito</div><div class='home-subtitle'>⚙️ Módulo em Construção</div></div>", unsafe_allow_html=True)
        st.button("Acessar Módulo", key="btn_credito", use_container_width=True, type="primary", on_click=mudar_pagina, args=('credito',))
    with c3:
        st.markdown(f"<div class='home-card'><span style='font-size: 50px;'>🤝</span><div class='home-title'>Divisão Convênios</div><div class='home-subtitle'>🔄 Atualizado em: {att_convenios}</div></div>", unsafe_allow_html=True)
        st.button("Acessar Módulo", key="btn_convenios", use_container_width=True, type="primary", on_click=mudar_pagina, args=('convenios',))

# --- NOVO MENU DE OPERAÇÕES DE CRÉDITO ---
elif st.session_state.pagina_atual == 'credito':
    st.button("⬅️ Voltar ao Menu Principal", on_click=mudar_pagina, args=('menu_principal',))
    st.markdown('<div class="header-container"><div class="main-title">Controle das Operações de Crédito</div></div>', unsafe_allow_html=True)
    
    # Exibe os dois cards como se fossem o menu principal
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown("<div class='home-card'><span style='font-size: 50px;'>🏛️</span><div class='home-title'>Programa FINISA</div><div class='home-subtitle'>Controle de Financiamento</div></div>", unsafe_allow_html=True)
        st.button("Acessar FINISA", key="btn_finisa", use_container_width=True, type="primary", on_click=mudar_pagina, args=('finisa',))
    with c2:
        st.markdown("<div class='home-card'><span style='font-size: 50px;'>☀️</span><div class='home-title'>Usina Fotovoltaica</div><div class='home-subtitle'>Execução do Projeto</div></div>", unsafe_allow_html=True)
        st.button("Acessar Usina", key="btn_usina", use_container_width=True, type="primary", on_click=mudar_pagina, args=('fotovoltaica',))

# --- TELA FINISA ---
elif st.session_state.pagina_atual == 'finisa':
    st.button("⬅️ Voltar para Operações de Crédito", on_click=mudar_pagina, args=('credito',))
    st.markdown('<div class="header-container"><div class="main-title">🏦 Operação de Crédito: FINISA</div></div>', unsafe_allow_html=True)
    st.info("🚧 O painel de controle e monitoramento do FINISA está em fase de estruturação de dados.")

# --- TELA USINA FOTOVOLTAICA ---
elif st.session_state.pagina_atual == 'fotovoltaica':
    st.button("⬅️ Voltar para Operações de Crédito", on_click=mudar_pagina, args=('credito',))
    st.markdown('<div class="header-container"><div class="main-title">☀️ Operação de Crédito: Usina Fotovoltaica</div></div>', unsafe_allow_html=True)
    st.info("🚧 O painel de execução da Usina Fotovoltaica está em fase de estruturação de dados.")

elif st.session_state.pagina_atual == 'convenios':
    st.button("⬅️ Voltar ao Menu Principal", on_click=mudar_pagina, args=('menu_principal',))
    st.markdown('<div class="header-container"><div class="main-title">Divisão Controle Convênios</div></div>', unsafe_allow_html=True)
    
    if not df_conv.empty:
        df_conv_tela = df_conv.copy()
        
        # --- BUSCA GLOBAL INTELIGENTE ---
        st.markdown("<div class='section-title' style='color:#2563eb; border-bottom:3px solid #2563eb;'>🔍 Busca Inteligente Global</div>", unsafe_allow_html=True)
        busca_global = st.text_input("Digite qualquer termo para pesquisar na base inteira:", placeholder="Ex: Nome de um analista, número SEI, secretaria, fonte...")
        
        if busca_global:
            # Cria uma máscara varrendo todas as colunas
            mask = pd.Series(False, index=df_conv_tela.index)
            for col in df_conv_tela.columns:
                mask |= df_conv_tela[col].astype(str).str.contains(busca_global, case=False, na=False)
            
            df_conv_tela = df_conv_tela[mask]
            
            if df_conv_tela.empty:
                st.warning(f"⚠️ Nenhum registro encontrado contendo o termo: '{busca_global}'")
        
        # Só exibe as abas se houver dados após o filtro global
        if not df_conv_tela.empty:
            tab_conv_fonte, tab_conv_analista, tab_conv_busca, tab_conv_geral = st.tabs([
                "🎯 Por Fonte de Recurso", "👤 Por Analista", "🔍 Busca Detalhada", "📋 Base Completa"
            ])
            
            # --- ABA 1: POR FONTE DE RECURSO ---
            with tab_conv_fonte:
                st.markdown("<div class='section-title'>🔍 Painel Híbrido: Pesquisa e Seleção por Fonte de Recurso</div>", unsafe_allow_html=True)
                fontes_rec = sorted([str(f).strip() for f in df_conv_tela['FONTE DE RECURSO'].unique() if str(f).strip() not in ['', 'nan']])
                
                if fontes_rec:
                    ct1, cs1 = st.columns(2)
                    with ct1: f_dig = normalizar_texto(st.text_input("⌨️ Digite a Fonte de Recurso:", placeholder="Ex: 1000", key="txt_f_conv"))
                    with cs1: f_sel = st.selectbox("Ou escolha na lista:", options=fontes_rec, index=fontes_rec.index(f_dig) if f_dig in fontes_rec else 0, key="sel_f_conv")
                    
                    f_final = f_dig if f_dig in fontes_rec else f_sel
                    if f_final:
                        df_filtro = df_conv_tela[df_conv_tela['FONTE DE RECURSO'] == f_final]
                        if not df_filtro.empty:
                            resp = df_filtro['RESPONSÁVEL'].iloc[0] if 'RESPONSÁVEL' in df_filtro.columns and str(df_filtro['RESPONSÁVEL'].iloc[0]) != '' else "NÃO INFORMADO"
                            st.markdown(f'''<div class='kpi-row-container'><div class='kpi-card-head-blue'><div class='kpi-label'>👤 Analista / Responsável</div><div class='kpi-value' style='color: #0f172a; font-size: 26px;'>{resp}</div></div></div>''', unsafe_allow_html=True)
                            st.markdown("<div class='section-title'>📋 Dados do Convênio</div>", unsafe_allow_html=True)
                            st.dataframe(df_filtro, use_container_width=True, hide_index=True)
                        
            # --- ABA 2: POR ANALISTA ---
            with tab_conv_analista:
                st.markdown("<div class='section-title'>🔍 Painel Híbrido: Pesquisa e Seleção por Analista</div>", unsafe_allow_html=True)
                if 'RESPONSÁVEL' in df_conv_tela.columns:
                    analistas = sorted([str(a) for a in df_conv_tela['RESPONSÁVEL'].unique() if str(a) != ''])
                    
                    if analistas:
                        ca1, ca2 = st.columns(2)
                        with ca1: a_dig = normalizar_texto(st.text_input("⌨️ Digite o nome do Analista:", placeholder="Ex: JOAO", key="txt_a_conv"))
                        with ca2: a_sel = st.selectbox("Ou escolha na lista:", options=analistas, index=analistas.index(a_dig) if a_dig in analistas else 0, key="sel_a_conv")
                        
                        a_final = a_dig if a_dig in analistas else a_sel
                        if a_final:
                            df_filtro_a = df_conv_tela[df_conv_tela['RESPONSÁVEL'] == a_final]
                            qtd_conv = len(df_filtro_a)
                            
                            st.markdown(f'''<div class='kpi-row-container'>
                                <div class='kpi-card-head-blue'>
                                    <div class='kpi-label'>👤 Analista Selecionado</div>
                                    <div class='kpi-value' style='color: #0f172a; font-size: 26px;'>{a_final}</div>
                                </div>
                                <div class='kpi-card-head' style='border-left: 6px solid #059669;'>
                                    <div class='kpi-label'>📋 Total de Convênios</div>
                                    <div class='kpi-value'>{qtd_conv}</div>
                                </div>
                            </div>''', unsafe_allow_html=True)
                            
                            st.markdown("<div class='section-title'>📋 Convênios sob responsabilidade do Analista</div>", unsafe_allow_html=True)
                            st.dataframe(df_filtro_a, use_container_width=True, hide_index=True)
                    else:
                        st.info("ℹ️ Nenhum Analista encontrado na base para esta busca.")
                else:
                    st.error("A coluna 'RESPONSÁVEL' não foi encontrada na planilha.")

            # --- ABA 3: BUSCA DETALHADA ---
            with tab_conv_busca:
                st.markdown("<div class='section-title'>🔍 Resultados da Busca</div>", unsafe_allow_html=True)
                if busca_global:
                    st.success(f"🎯 Exibindo {len(df_conv_tela)} resultados para o termo: '{busca_global}'")
                else:
                    st.info("Utilize a barra de pesquisa inteligente acima para filtrar os resultados aqui.")
                st.dataframe(df_conv_tela, use_container_width=True, hide_index=True)

            # --- ABA 4: BASE COMPLETA (COM FILTROS INTERNOS) ---
            with tab_conv_geral:
                st.markdown("<div class='section-title'>📊 Base de Dados Completa</div>", unsafe_allow_html=True)
                st.info("💡 **Dica de Filtro Nativo:** Passe o mouse sobre o cabeçalho de qualquer coluna da tabela abaixo e clique no ícone da **lupa** ou das **linhas** para pesquisar e filtrar os dados livremente!")
                st.dataframe(df_conv_tela, use_container_width=True, hide_index=True)

    else: 
        st.warning("A base de dados de convênios (`Divisão Convenios - Divisao.csv`) não foi localizada ou está vazia.")

elif st.session_state.pagina_atual == 'emendas':
    st.button("⬅️ Voltar ao Menu Principal", on_click=mudar_pagina, args=('menu_principal',))
    if not df.empty:
        fontes = sorted([f for f in df['fonte_clean'].unique() if f not in ['', 'nan']])
        st.markdown('''<div class="header-container"><div class="header-left"><div class="main-title">Controle de Emendas Orçamentárias</div></div><div class="header-right"><div class="status-dot"></div><div class="status-text">Base Google Sheets Conectada</div></div></div>''', unsafe_allow_html=True)
        tab_ativa, tab_planos, tab_secretarias, tab_deputados, tab_geral = st.tabs(["🎯 Por Fonte", "📋 Por Plano", "🏛️ Por Secretaria", "🔍 Por Deputado", "🌐 Panorama Geral"])
        
        with tab_ativa:
            st.markdown("<div class='section-title'> 🎯 Painel Híbrido: Pesquisa e Seleção de Fonte</div>", unsafe_allow_html=True)
            if fontes:
                c_txt, c_sel = st.columns(2)
                with c_txt: f_dig = st.text_input("⌨️ Digite a Fonte:", placeholder="Ex: 1000", key="txt_f").strip().lower()
                with c_sel: f_sel = st.selectbox("🖱️ Ou selecione:", options=fontes, index=fontes.index(f_dig) if f_dig in fontes else 0, key="sel_f")
                fonte_final = f_dig if f_dig in fontes else f_sel
                
                if fonte_final:
                    d_fin = df[df['fonte_clean'] == fonte_final]
                    anos = ["Exibir Histórico Acumulado Completo"] + sorted(list(set([str(a) for a in d_fin['ano_mov'].unique() if a not in ['', 'nan']])))
                    ano_sel = st.selectbox("📅 Exercício Fiscal:", options=anos, key="ano_f")
                    if not d_fin.empty:
                        d_fluxo = d_fin if ano_sel == anos[0] else d_fin[d_fin['ano_mov'] == ano_sel]
                        d_saldo = d_fin if ano_sel == anos[0] else d_fin[d_fin['ano_mov'].astype(int) <= int(ano_sel)]
                        conta = d_fin['conta corrente'].iloc[0]
                        d_bc = df[df['conta corrente'] == conta] if conta != "Não Informada" else pd.DataFrame()
                        d_bc_fluxo = d_bc if ano_sel == anos[0] else (d_bc[d_bc['ano_mov'] == ano_sel] if not d_bc.empty else pd.DataFrame())
                        d_bc_saldo = d_bc if ano_sel == anos[0] else (d_bc[d_bc['ano_mov'].astype(int) <= int(ano_sel)] if not d_bc.empty else pd.DataFrame())
                        
                        sal_fonte = float(d_saldo['repasse'].sum() + d_saldo['rendimento'].sum()) - float(d_saldo['bruto'].sum())
                        sal_banco = float(d_bc_saldo['repasse'].sum() + d_bc_saldo['rendimento'].sum()) - float(d_bc_saldo['bruto'].sum()) if not d_bc_saldo.empty else sal_fonte
                        lbl = "Histórico Total" if ano_sel == anos[0] else f"Exercício {ano_sel}"
                        
                        st.markdown(f'''<div class='kpi-row-container'><div class='kpi-card-head'><div class='kpi-label'>🎯 Saldo Fonte ({lbl})</div><div class='kpi-value'>{fmt(sal_fonte)}</div></div><div class='kpi-card-head-blue'><div class='kpi-label' style='color:#1e40af;'>🏦 Saldo Conta: {conta} ({lbl})</div><div class='kpi-value' style='color:#2563eb;'>{fmt(sal_banco)}</div></div></div>''', unsafe_allow_html=True)
                        st.markdown(f'''<div style='margin-bottom:10px;'><div class='meta-tag'>👤 Deputado: {d_fin['deputado'].unique()[0]}</div><div class='meta-tag'>📄 Emenda: {d_fin['emenda_clean'].unique()[0]}</div><div class='meta-tag'>🎯 Plano: {d_fin['plano_clean'].unique()[0]}</div></div>''', unsafe_allow_html=True)
                        
                        secs = [s for s in d_fin['secretaria'].unique() if s != '']
                        if len(secs) > 1:
                            st.markdown(f"<div class='section-title'>🌍 RESUMO CONSOLIDADO DA FONTE — ({lbl})</div>", unsafe_allow_html=True)
                            st.markdown(f'''<table class='extrato-table'><tr class='extrato-row'><td class='extrato-cell-label'>(+) REPASSE ENTRADO NO PERÍODO</td><td class='extrato-cell-val' style='color:#059669;'>{fmt(float(d_fluxo['repasse'].sum()))}</td></tr><tr class='extrato-row'><td class='extrato-cell-label'>(+) RENDIMENTOS</td><td class='extrato-cell-val' style='color:#2563eb;'>{fmt(float(d_fluxo['rendimento'].sum()))}</td></tr><tr class='extrato-row'><td>(-) DESPESAS LIQUIDADAS</td><td class='extrato-cell-val' style='color:#dc2626;'>{fmt(float(d_fluxo['bruto'].sum()))}</td></tr><tr class='extrato-row-final' style='background-color:#ecf2ff;'><td class='extrato-cell-label'>(=) SALDO REAL</td><td class='extrato-cell-val' style='color:{"#059669" if sal_fonte >= 0 else "#dc2626"}; font-size:14px;'>{fmt(sal_fonte)}</td></tr></table>''', unsafe_allow_html=True)
                        
                        st.markdown(f"<div class='section-title'>🏢 Divisão por Secretaria — ({lbl})</div>", unsafe_allow_html=True)
                        for sec in secs:
                            ds_f, ds_s = d_fluxo[d_fluxo['secretaria'] == sec], d_saldo[d_saldo['secretaria'] == sec]
                            st.markdown(f"<div class='secretaria-header'>🏛️ {sec}</div>", unsafe_allow_html=True)
                            st.markdown(f'''<table class='extrato-table'><tr class='extrato-row'><td class='extrato-cell-label'>(+) REPASSE</td><td class='extrato-cell-val' style='color:#059669;'>{fmt(float(ds_f['repasse'].sum()))}</td></tr><tr class='extrato-row'><td class='extrato-cell-label'>(+) RENDIMENTOS</td><td class='extrato-cell-val' style='color:#2563eb;'>{fmt(float(ds_f['rendimento'].sum()))}</td></tr><tr class='extrato-row'><td class='extrato-cell-label'>(-) DESPESAS</td><td class='extrato-cell-val' style='color:#dc2626;'>{fmt(float(ds_f['bruto'].sum()))}</td></tr><tr class='extrato-row-final'><td class='extrato-cell-label'>(=) SALDO LIVRE</td><td class='extrato-cell-val' style='color:#059669;'>{fmt(float(ds_s['repasse'].sum() + ds_s['rendimento'].sum()) - float(ds_s['bruto'].sum()))}</td></tr></table>''', unsafe_allow_html=True)

                        if conta != "Não Informada" and not d_bc_saldo.empty:
                            st.markdown(f"<div class='section-title' style='color:#2563eb; border-bottom:3px solid #2563eb;'>⚖️ ABERTURA DE SALDOS — CONTA: {conta} ({lbl})</div>", unsafe_allow_html=True)
                            f_comp = sorted([fc for fc in d_bc_saldo['fonte_clean'].unique() if fc != ''])
                            l_bc = []
                            tr, trn, tg, ts = 0.0, 0.0, 0.0, 0.0
                            for fi in f_comp:
                                di_f = d_bc_fluxo[d_bc_fluxo['fonte_clean'] == fi] if not d_bc_fluxo.empty else pd.DataFrame()
                                fr, frn, fd = float(di_f['repasse'].sum() if not di_f.empty else 0), float(di_f['rendimento'].sum() if not di_f.empty else 0), float(di_f['bruto'].sum() if not di_f.empty else 0)
                                di_s = d_bc_saldo[d_bc_saldo['fonte_clean'] == fi]
                                fs = float(di_s['repasse'].sum() + di_s['rendimento'].sum() - di_s['bruto'].sum())
                                tr += fr; trn += frn; tg += fd; ts += fs
                                l_bc.append({'Fonte Orçamentária': fi.upper() + (" (Ativa)" if fi == fonte_final else ""), 'Repasses': fr, 'Rendimentos': frn, 'Despesas': fd, 'Saldo Real': fs})
                            l_bc.append({'Fonte Orçamentária': 'TOTAL CONTA 🏦', 'Repasses': tr, 'Rendimentos': trn, 'Despesas': tg, 'Saldo Real': ts})
                            df_bc = pd.DataFrame(l_bc)
                            st.dataframe(df_bc.style.apply(lambda r: ['background-color: #f1f5f9; font-weight: 800;' if 'TOTAL' in r['Fonte Orçamentária'] else ('background-color: #e0f2fe; font-weight: 700;' if '(ATIVA)' in r['Fonte Orçamentária'] else '') for _ in r], axis=1).format({'Repasses': fmt, 'Rendimentos': fmt, 'Despesas': fmt, 'Saldo Real': fmt}), use_container_width=True, hide_index=True)

                        st.markdown(f"<div class='section-title' style='color: #0f172a; border-bottom: 3px solid #0f172a;'>📋 Lançamentos do Período — ({lbl})</div>", unsafe_allow_html=True)
                        d_val = d_fluxo[d_fluxo['EMPENHO_COL'] != '-']
                        if not d_val.empty:
                            df_rnd = pd.DataFrame({'Data': d_val['DATA_LANCAMENTO'], 'Empenho': d_val['EMPENHO_COL'], 'NF': d_val['NOTA_COL'], 'Valor NF': d_val['bruto'], 'PDF': [gerar_botoes_documento(u, e, n, "abrir") for u, e, n in zip(d_val['URL_REAL_LINK'], d_val['EMPENHO_COL'], d_val['NOTA_COL'])], 'Download': [gerar_botoes_documento(u, e, n, "baixar") for u, e, n in zip(d_val['URL_REAL_LINK'], d_val['EMPENHO_COL'], d_val['NOTA_COL'])]})
                            st.write(df_rnd.style.format({'Valor NF': fmt}).to_html(escape=False, index=False, classes='extrato-table'), unsafe_allow_html=True)
                        else: st.info("ℹ️ Nenhum lançamento no período.")

        # 2. 📋 ABA POR PLANO
        with tab_planos:
            st.markdown("<div class='section-title'> 📋 Painel Híbrido: Pesquisa e Seleção de Plano</div>", unsafe_allow_html=True)
            planos = sorted([str(p).upper() for p in df['plano_clean'].unique() if str(p).strip() not in ['', 'nan']])
            if planos:
                c_txt, c_sel = st.columns(2)
                with c_txt: p_dig = re.sub(r'\D', '', st.text_input("⌨️ Digite o Plano (Apenas números):", placeholder="Ex: 1264", key="txt_p").strip())
                p_enc = next((p for p in planos if re.sub(r'\D', '', p) == p_dig), None) if p_dig else None
                with c_sel: p_sel = st.selectbox("🖱️ Ou escolha na lista:", options=planos, index=planos.index(p_enc) if p_enc else 0, key="sel_p")
                p_fin = p_enc if p_enc else p_sel
                
                dp = df[df['plano_clean'].str.upper() == p_fin]
                anos_p = ["Exibir Histórico Acumulado Completo"] + sorted(list(set([str(a) for a in dp['ano_mov'].unique() if a not in ['', 'nan']])))
                ano_p = st.selectbox("📅 Exercício Fiscal:", options=anos_p, key="ano_p")
                
                if not dp.empty:
                    lbl_p = "Histórico Total" if ano_p == anos_p[0] else f"Exercício {ano_p}"
                    dp_f = dp if ano_p == anos_p[0] else dp[dp['ano_mov'] == ano_p]
                    dp_s = dp if ano_p == anos_p[0] else dp[dp['ano_mov'].astype(int) <= int(ano_p)]
                    sal_p = float(dp_s['repasse'].sum() + dp_s['rendimento'].sum()) - float(dp_s['bruto'].sum())
                    
                    st.markdown(f'''<div class='kpi-row-container'><div class='kpi-card-head' style='border-left: 6px solid #2563eb;'><div class='kpi-label'>📋 Plano Ativo</div><div class='kpi-value' style='color:#0f172a;'>{p_fin}</div></div><div class='kpi-card-head' style='border-left: 6px solid #059669;'><div class='kpi-label'>💰 Saldo ({lbl_p})</div><div class='kpi-value'>{fmt(sal_p)}</div></div><div class='kpi-card-head-blue'><div class='kpi-label'>🏦 Conta</div><div class='kpi-value' style='color:#2563eb; font-size: 20px;'>{dp['conta corrente'].iloc[0]}</div></div></div>''', unsafe_allow_html=True)
                    st.markdown(f'''<div style='margin-bottom:15px;'><div class='meta-tag'>🎯 Fontes: {", ".join([f.upper() for f in sorted(dp['fonte_clean'].unique())])}</div><div class='meta-tag'>👤 Deputado: {dp['deputado'].unique()[0]}</div><div class='meta-tag'>📄 Emenda: {dp['emenda_clean'].unique()[0]}</div></div>''', unsafe_allow_html=True)
                    
                    secs_p = sorted([str(s) for s in dp['secretaria'].unique() if str(s).strip() not in ['', 'nan', 'NÃO ESPECIFICADA']]) or ['NÃO ESPECIFICADA']
                    html_p = f"<table class='extrato-table'><thead><tr><th>DESCRIÇÃO</th>" + "".join([f"<th style='text-align: right;'>{s}</th>" for s in secs_p]) + "<th style='text-align: right;'>TOTAL</th></tr></thead><tbody>"
                    html_p += "<tr class='extrato-row'><td class='extrato-cell-label'>(+) REPASSE</td>" + "".join([f"<td class='extrato-cell-val' style='color:#059669;'>{fmt(float(dp_f[dp_f['secretaria'] == s]['repasse'].sum()))}</td>" for s in secs_p]) + f"<td class='extrato-cell-val' style='color:#059669;'>{fmt(float(dp_f['repasse'].sum()))}</td></tr>"
                    html_p += "<tr class='extrato-row'><td class='extrato-cell-label'>(+) RENDIMENTOS</td>" + "".join([f"<td class='extrato-cell-val' style='color:#2563eb;'>{fmt(float(dp_f[dp_f['secretaria'] == s]['rendimento'].sum()))}</td>" for s in secs_p]) + f"<td class='extrato-cell-val' style='color:#2563eb;'>{fmt(float(dp_f['rendimento'].sum()))}</td></tr>"
                    html_p += "<tr class='extrato-row'><td class='extrato-cell-label'>(-) DESPESAS</td>" + "".join([f"<td class='extrato-cell-val' style='color:#dc2626;'>{fmt(float(dp_f[dp_f['secretaria'] == s]['bruto'].sum()))}</td>" for s in secs_p]) + f"<td class='extrato-cell-val' style='color:#dc2626;'>{fmt(float(dp_f['bruto'].sum()))}</td></tr>"
                    html_p += "<tr class='extrato-row-final'><td class='extrato-cell-label'>(=) SALDO DISPONÍVEL</td>" + "".join([f"<td class='extrato-cell-val' style='color:#059669;'>{fmt(float(dp_s[dp_s['secretaria'] == s]['repasse'].sum() + dp_s[dp_s['secretaria'] == s]['rendimento'].sum() - dp_s[dp_s['secretaria'] == s]['bruto'].sum()))}</td>" for s in secs_p]) + f"<td class='extrato-cell-val' style='color:#059669;'>{fmt(sal_p)}</td></tr></tbody></table>"
                    st.markdown(f"<div class='section-title'>🌍 Extrato do Plano — ({lbl_p})</div>{html_p}", unsafe_allow_html=True)
                    
                    st.markdown(f"<div class='section-title'>📋 Lançamentos do Plano — ({lbl_p})</div>", unsafe_allow_html=True)
                    dp_val = dp_f[dp_f['EMPENHO_COL'] != '-']
                    if not dp_val.empty:
                        df_rp = pd.DataFrame({'Data': dp_val['DATA_LANCAMENTO'], 'Empenho': dp_val['EMPENHO_COL'], 'NF': dp_val['NOTA_COL'], 'Secretaria': dp_val['secretaria'], 'Valor NF': dp_val['bruto'], 'PDF': [gerar_botoes_documento(u, e, n, "abrir") for u, e, n in zip(dp_val['URL_REAL_LINK'], dp_val['EMPENHO_COL'], dp_val['NOTA_COL'])], 'Download': [gerar_botoes_documento(u, e, n, "baixar") for u, e, n in zip(dp_val['URL_REAL_LINK'], dp_val['EMPENHO_COL'], dp_val['NOTA_COL'])]})
                        st.write(df_rp.style.format({'Valor NF': fmt}).to_html(escape=False, index=False, classes='extrato-table'), unsafe_allow_html=True)
                    else: st.info("ℹ️ Nenhum lançamento no período.")

        # 3. 🏛️ ABA POR SECRETARIA
        with tab_secretarias:
            st.markdown("<div class='section-title'>🏛️ Painel Gestor: Investigação por Secretaria</div>", unsafe_allow_html=True)
            secs = sorted([str(s) for s in df['secretaria'].unique() if str(s).strip() not in ['', 'nan', 'NÃO ESPECIFICADA']])
            if secs:
                c_txt, c_sel = st.columns(2)
                with c_txt: s_dig = normalizar_texto(st.text_input("⌨️ Digite a Secretaria:", placeholder="Ex: SEINFRA", key="txt_s"))
                s_enc = next((s for s in secs if s.upper() == s_dig.upper()), None) if s_dig else None
                with c_sel: s_sel = st.selectbox("🖱️ Ou selecione:", options=secs, index=secs.index(s_enc) if s_enc else 0, key="sel_s")
                s_fin = s_enc if s_enc else s_sel
                
                ds = df[df['secretaria'] == s_fin]
                anos_s = ["Exibir Histórico Acumulado Completo"] + sorted(list(set([str(a) for a in ds['ano_mov'].unique() if a not in ['', 'nan']])))
                ano_s = st.selectbox("📅 Exercício Fiscal:", options=anos_s, key="ano_s")
                
                if not ds.empty:
                    lbl_s = "Histórico Total" if ano_s == anos_s[0] else f"Exercício {ano_s}"
                    ds_f = ds if ano_s == anos_s[0] else ds[ds['ano_mov'] == ano_s]
                    ds_s = ds if ano_s == anos_s[0] else ds[ds['ano_mov'].astype(int) <= int(ano_s)]
                    sal_s = float(ds_s['repasse'].sum() + ds_s['rendimento'].sum()) - float(ds_s['bruto'].sum())
                    
                    st.markdown(f'''<div class='kpi-row-container'><div class='kpi-card-head' style='border-left: 6px solid #2563eb;'><div class='kpi-label'>🏛️ Secretaria</div><div class='kpi-value' style='color:#0f172a;'>{s_fin}</div></div><div class='kpi-card-head' style='border-left: 6px solid #059669;'><div class='kpi-label'>💰 Saldo ({lbl_s})</div><div class='kpi-value'>{fmt(sal_s)}</div></div><div class='kpi-card-head' style='border-left: 6px solid #0f172a;'><div class='kpi-label'>📊 Fontes</div><div class='kpi-value' style='color:#0f172a;'>{len(ds['fonte_clean'].unique())} Emenda(s)</div></div></div>''', unsafe_allow_html=True)
                    
                    st.markdown(f"<div class='section-title'>🌍 Extrato Consolidado da Pasta — ({lbl_s})</div>", unsafe_allow_html=True)
                    st.markdown(f'''<table class='extrato-table'><tr class='extrato-row'><td class='extrato-cell-label'>(+) REPASSES TOTAIS</td><td class='extrato-cell-val' style='color:#059669;'>{fmt(float(ds_f['repasse'].sum()))}</td></tr><tr class='extrato-row'><td class='extrato-cell-label'>(+) RENDIMENTOS TOTAIS</td><td class='extrato-cell-val' style='color:#2563eb;'>{fmt(float(ds_f['rendimento'].sum()))}</td></tr><tr class='extrato-row'><td>(-) DESPESAS TOTAIS</td><td class='extrato-cell-val' style='color:#dc2626;'>{fmt(float(ds_f['bruto'].sum()))}</td></tr><tr class='extrato-row-final'><td class='extrato-cell-label'>(=) SALDO LIVRE DA PASTA</td><td class='extrato-cell-val' style='color:#059669;'>{fmt(sal_s)}</td></tr></table>''', unsafe_allow_html=True)

                    st.markdown(f"<div class='section-title' style='color:#2563eb; border-bottom:3px solid #2563eb;'>⚖️ Detalhamento por Fonte de Recurso vinculada à {s_fin} — ({lbl_s})</div>", unsafe_allow_html=True)
                    fontes_da_secretaria = sorted([f for f in ds_s['fonte_clean'].unique() if f != ''])
                    linhas_fontes_sec = []
                    
                    for fi in fontes_da_secretaria:
                        df_i_fluxo = ds_f[ds_f['fonte_clean'] == fi]
                        df_i_saldo = ds_s[ds_s['fonte_clean'] == fi]
                        
                        f_rep = float(df_i_fluxo['repasse'].sum())
                        f_ren = float(df_i_fluxo['rendimento'].sum())
                        f_desp = float(df_i_fluxo['bruto'].sum())
                        f_saldo = float(df_i_saldo['repasse'].sum() + df_i_saldo['rendimento'].sum() - df_i_saldo['bruto'].sum())
                        
                        linhas_fontes_sec.append({
                            'Fonte Vinculada': fi.upper(),
                            'Repasses': f_rep,
                            'Rendimentos': f_ren,
                            'Despesas': f_desp,
                            'Saldo Livre da Fonte': f_saldo
                        })
                        
                    if linhas_fontes_sec:
                        df_tabela_sec = pd.DataFrame(linhas_fontes_sec)
                        st.dataframe(df_tabela_sec.style.format({
                            'Repasses': fmt, 'Rendimentos': fmt, 'Despesas': fmt, 'Saldo Livre da Fonte': fmt
                        }), use_container_width=True, hide_index=True)
                    else:
                        st.info("Nenhuma fonte movimentada para esta secretaria no período selecionado.")

        # 4. 🔍 ABA POR DEPUTADO
        with tab_deputados:
            st.markdown("<div class='section-title'>🔍 Painel Parlamentar</div>", unsafe_allow_html=True)
            deps = sorted([str(d) for d in df['deputado'].unique() if str(d).strip() not in ['', 'nan', 'NÃO INFORMADO']])
            if deps:
                c_txt, c_sel = st.columns(2)
                with c_txt: d_dig = normalizar_texto(st.text_input("⌨️ Digite o Deputado:", placeholder="Ex: DEPUTADO ABC", key="txt_d"))
                d_enc = next((d for d in deps if d.upper() == d_dig.upper()), None) if d_dig else None
                with c_sel: d_sel = st.selectbox("🖱️ Ou selecione:", options=deps, index=deps.index(d_enc) if d_enc else 0, key="sel_d")
                d_fin = d_enc if d_enc else d_sel
                
                dd = df[df['deputado'] == d_fin]
                anos_d = ["Exibir Histórico Acumulado Completo"] + sorted(list(set([str(a) for a in dd['ano_mov'].unique() if a not in ['', 'nan']])))
                ano_d = st.selectbox("📅 Exercício Fiscal:", options=anos_d, key="ano_d")
                
                if not dd.empty:
                    lbl_d = "Histórico Total" if ano_d == anos_d[0] else f"Exercício {ano_d}"
                    dd_f = dd if ano_d == anos_d[0] else dd[dd['ano_mov'] == ano_d]
                    dd_s = dd if ano_d == anos_d[0] else dd[dd['ano_mov'].astype(int) <= int(ano_d)]
                    sal_d = float(dd_s['repasse'].sum() + dd_s['rendimento'].sum()) - float(dd_s['bruto'].sum())
                    
                    st.markdown(f'''<div class='kpi-row-container'><div class='kpi-card-head' style='border-left: 6px solid #2563eb;'><div class='kpi-label'>👤 Parlamentar</div><div class='kpi-value' style='color:#0f172a;'>{d_fin}</div></div><div class='kpi-card-head' style='border-left: 6px solid #059669;'><div class='kpi-label'>💰 Saldo Consolidado ({lbl_d})</div><div class='kpi-value'>{fmt(sal_d)}</div></div></div>''', unsafe_allow_html=True)
                    
                    st.markdown(f"<div class='section-title'>🌍 Extrato Consolidado do Deputado — ({lbl_d})</div>", unsafe_allow_html=True)
                    st.markdown(f'''<table class='extrato-table'><tr class='extrato-row'><td class='extrato-cell-label'>(+) REPASSES TOTAIS</td><td class='extrato-cell-val' style='color:#059669;'>{fmt(float(dd_f['repasse'].sum()))}</td></tr><tr class='extrato-row'><td class='extrato-cell-label'>(+) RENDIMENTOS TOTAIS</td><td class='extrato-cell-val' style='color:#2563eb;'>{fmt(float(dd_f['rendimento'].sum()))}</td></tr><tr class='extrato-row'><td>(-) DESPESAS TOTAIS</td><td class='extrato-cell-val' style='color:#dc2626;'>{fmt(float(dd_f['bruto'].sum()))}</td></tr><tr class='extrato-row-final'><td class='extrato-cell-label'>(=) SALDO LÍQUIDO GERAL</td><td class='extrato-cell-val' style='color:#059669;'>{fmt(sal_d)}</td></tr></table>''', unsafe_allow_html=True)

                    st.markdown(f"<div class='section-title' style='color:#2563eb; border-bottom:3px solid #2563eb;'>⚖️ Detalhamento: Onde o recurso foi aplicado (Por Fonte e Secretaria) — ({lbl_d})</div>", unsafe_allow_html=True)
                    
                    grupo_deputado = dd_s.groupby(['fonte_clean', 'secretaria'])
                    linhas_detalhe_dep = []
                    
                    for (fi, sec), df_grupo_saldo in grupo_deputado:
                        if fi == '': continue
                        df_grupo_fluxo = dd_f[(dd_f['fonte_clean'] == fi) & (dd_f['secretaria'] == sec)]
                        
                        d_rep = float(df_grupo_fluxo['repasse'].sum())
                        d_ren = float(df_grupo_fluxo['rendimento'].sum())
                        d_desp = float(df_grupo_fluxo['bruto'].sum())
                        d_saldo = float(df_grupo_saldo['repasse'].sum() + df_grupo_saldo['rendimento'].sum() - df_grupo_saldo['bruto'].sum())
                        
                        linhas_detalhe_dep.append({
                            'Fonte Vinculada': fi.upper(),
                            'Secretaria Contemplada': sec.upper(),
                            'Repasses': d_rep,
                            'Rendimentos': d_ren,
                            'Despesas': d_desp,
                            'Saldo Específico': d_saldo
                        })
                    
                    if linhas_detalhe_dep:
                        df_tabela_dep = pd.DataFrame(linhas_detalhe_dep)
                        st.dataframe(df_tabela_dep.style.format({
                            'Repasses': fmt, 'Rendimentos': fmt, 'Despesas': fmt, 'Saldo Específico': fmt
                        }), use_container_width=True, hide_index=True)
                    else:
                        st.info("Nenhuma destinação detalhada localizada para este parlamentar no período.")

        # 5. 🌐 ABA PANORAMA
        with tab_geral:
            st.markdown("<div class='section-title'>📊 BALANÇOS CONSOLIDADOS</div>", unsafe_allow_html=True)
            df_g_sec = df[df['secretaria'] != 'NÃO ESPECIFICADA'].groupby('secretaria').agg({'repasse':'sum', 'rendimento':'sum', 'bruto':'sum'}).reset_index()
            df_g_sec['saldo'] = df_g_sec['repasse'] + df_g_sec['rendimento'] - df_g_sec['bruto']
            df_g_dep = df[df['deputado'] != 'NÃO INFORMADO'].groupby('deputado').agg({'repasse':'sum', 'rendimento':'sum', 'bruto':'sum'}).reset_index()
            df_g_dep['saldo'] = df_g_dep['repasse'] + df_g_dep['rendimento'] - df_g_dep['bruto']
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("<b>🏛️ SALDO POR SECRETARIA:</b>", unsafe_allow_html=True)
                fig1 = go.Figure(go.Bar(x=df_g_sec['secretaria'], y=df_g_sec['saldo'], marker_color='#2563eb', text=[fmt(v) for v in df_g_sec['saldo']], textposition='auto'))
                fig1.update_layout(height=300, margin=dict(l=10,r=10,t=30,b=10))
                st.plotly_chart(fig1, use_container_width=True)
            with c2:
                st.markdown("<b>👤 SALDO POR DEPUTADO:</b>", unsafe_allow_html=True)
                fig2 = go.Figure(go.Bar(x=df_g_dep['deputado'], y=df_g_dep['saldo'], marker_color='#7c3aed', text=[fmt(v) for v in df_g_dep['saldo']], textposition='auto'))
                fig2.update_layout(height=300, margin=dict(l=10,r=10,t=30,b=10))
                st.plotly_chart(fig2, use_container_width=True)
