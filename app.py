import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
import os

# 1. Configuração estrutural da página corporativa (Deve ser o primeiro comando)
st.set_page_config(page_title="Controle de Emendas", page_icon="📊", layout="wide")

# Otimização de performance: Carregamento centralizado e cache de longa duração (60 minutos)
@st.cache_data(ttl=3600, show_spinner="Carregando base de dados otimizada...")
def carregar_dados_locais():
    if not os.path.exists("dados.csv"):
        return pd.DataFrame()
        
    df_raw = pd.read_csv("dados.csv")
    df = pd.DataFrame()
    colunas_mapeadas_limpas = {}
    
    # Padronização de colunas ultra-rápida em vetor
    for c in df_raw.columns:
        c_clean = str(c).strip().lower()
        c_clean = re.sub(r'[^\w\s]', '', c_clean).strip()
        c_clean = c_clean.replace('â', 'a').replace('ç', 'c').replace('ã', 'a').replace('ó', 'o')
        colunas_mapeadas_limpas[c_clean] = df_raw[c]
        
    def buscar_coluna_original(nome_procurado, padrao_vazio=''):
        for c_limpa, serie_dados in colunas_mapeadas_limpas.items():
            if nome_procurado in c_limpa:
                return serie_dados.fillna(padrao_vazio).astype(str).str.strip()
        return pd.Series([padrao_vazio] * len(df_raw)).astype(str)

    df['fonte_clean'] = buscar_coluna_original('fonte', '').apply(lambda x: str(x).split('.')[0].lower().replace('nan', '').replace('-', '').strip())
    df['emenda_clean'] = buscar_coluna_original('emenda', '').apply(lambda x: str(x).split('.')[0].strip())
    df['plano_clean'] = buscar_coluna_original('plano', '').apply(lambda x: str(x).split('.')[0].strip())
    
    df['EMPENHO_COL'] = buscar_coluna_original('empenho', '-')
    df['NOTA_COL'] = buscar_coluna_original('nota', '-')
    df['PDF_GERAL'] = buscar_coluna_original('pdf', '-')
    
    df['secretaria'] = buscar_coluna_original('secretaria', '').replace('', 'Não Especificada')
    df['deputado'] = buscar_coluna_original('deputado', '').replace('', 'Não Informado')
    df['desc_clean'] = buscar_coluna_original('descricao', '').replace('', 'Sem descrição informada')
    df['conta corrente'] = buscar_coluna_original('conta', '').replace('', 'Não Informada')

    coluna_data_real = next((c for c in colunas_mapeadas_limpas if 'data' in c and 'venc' not in c and 'nota' not in c), None)
    df['DATA_LANCAMENTO'] = colunas_mapeadas_limpas[coluna_data_real].fillna('-').astype(str).str.strip() if coluna_data_real else buscar_coluna_original('data', '-')

    def extrair_numerico_coluna(nome_chave):
        for c_limpa, serie_dados in colunas_mapeadas_limpas.items():
            if nome_chave in c_limpa:
                return serie_dados.astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip().replace(['nan', '-', ''], '0').astype(float)
        return pd.Series([0.0] * len(df_raw))

    df['Receitas / Repasses'] = extrair_numerico_coluna('repasse')
    df['rendimentos'] = extrair_numerico_coluna('rendimento')
    df['Valor Bruto da NF'] = extrair_numerico_coluna('bruto')
    
    # Extração de ano otimizada com vetorização string nativa
    df['ano_mov'] = df['DATA_LANCAMENTO'].str.extract(r'(20\d{2})').fillna('2025')
    return df

# Execução e estilização CSS
HEX_TEXT_BLACK, HEX_CARD_BG, HEX_BOX_BG, HEX_NAV_BORDER = "#000000", "#ffffff", "#f1f5f9", "#cbd5e1"
st.markdown(f'''<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght=400;500;600;700;800&display=swap');
    html, body, [class*="css"], [data-testid="stAppViewContainer"] {{ font-family: 'Inter', sans-serif; background-color: #ffffff !important; color: {HEX_TEXT_BLACK} !important; }}
    [data-testid="stSidebar"], [data-testid="stSidebarUserContent"] {{ background-color: {HEX_CARD_BG} !important; border-right: 2px solid {HEX_NAV_BORDER} !important; }}
    [data-testid="stSidebar"] div[data-testid="stSelectbox"] {{ background-color: {HEX_BOX_BG} !important; padding: 12px; border-radius: 8px; border: 1px solid {HEX_NAV_BORDER}; }}
    .main-title {{ font-size: 38px; font-weight: 800; color: #0f172a; letter-spacing: -1.5px; margin-bottom: 5px; }}
    .kpi-row-container {{ display: flex; gap: 20px; margin-top: 15px; margin-bottom: 10px; }}
    .kpi-card-head {{ flex: 1; background-color: #ffffff; border: 2px solid #000000; border-radius: 10px; padding: 16px 22px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02); }}
    .kpi-card-head-blue {{ flex: 1; background-color: #f8fafc; border: 2px solid #2563eb; border-radius: 10px; padding: 16px 22px; border-left: 6px solid #2563eb; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02); }}
    .kpi-label {{ font-size: 13px; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px; }}
    .kpi-value {{ font-size: 25px; font-weight: 800; color: #059669; letter-spacing: -0.5px; }}
    .section-title {{ font-size: 15px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; color: {HEX_TEXT_BLACK}; margin-top: 30px; margin-bottom: 20px; padding-bottom: 8px; border-bottom: 3px solid #000000; }}
    .meta-tag {{ background-color: #f1f5f9; color: {HEX_TEXT_BLACK}; padding: 6px 14px; border-radius: 6px; font-weight: 700; font-size: 13px; border: 1px solid #cbd5e1; margin-right: 8px; display: inline-block; }}
    .secretaria-header {{ font-size: 18px; font-weight: 800; color: {HEX_TEXT_BLACK}; margin-top: 25px; margin-bottom: 5px; padding-left: 8px; border-left: 6px solid #000000; }}
    .metric-container {{ background-color: {HEX_CARD_BG}; border: 2px solid #000000; border-radius: 12px; padding: 22px; margin-bottom: 15px; display: flex; flex-direction: column; justify-content: center; min-height: 140px; }}
    .extrato-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; margin-bottom: 15px; background-color: #ffffff; border: 2px solid #000000; border-radius: 8px; overflow: hidden; }}
    .extrato-row {{ border-bottom: 1px solid #cbd5e1; }}
    .extrato-row-final {{ border-bottom: none; background-color: #f8fafc; font-weight: 800; border-top: 2px solid #000000; }}
    .extrato-cell-label {{ padding: 14px 20px; font-size: 13px; font-weight: 700; color: #0f172a; text-align: left; width: 65%; }}
    .extrato-cell-val {{ padding: 14px 20px; font-size: 14px; font-weight: 800; text-align: right; width: 35%; white-space: nowrap; }}
    .grid-header {{ background-color: #2563eb; color: #ffffff; padding: 12px; font-weight: 800; font-size: 14px; text-align: center; border: 1px solid #1e40af; }}
    .grid-row-active {{ background-color: #f8fafc; padding: 12px; font-weight: 700; border-bottom: 1px solid #cbd5e1; font-size: 13px; }}
    .grid-row-normal {{ padding: 12px; border-bottom: 1px solid #cbd5e1; font-size: 13px; }}
    .grid-total {{ background-color: #eff6ff; padding: 16px; font-weight: 800; font-size: 14px; color: #1e3a8a; border-top: 2px solid #2563eb; }}
</style>''', unsafe_allow_html=True)

try:
    df = carregar_dados_locales()
    
    if not df.empty:
        def fmt(valor):
            return f"R$ {float(valor):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        fontes = sorted(list(set([str(f).strip() for f in df['fonte_clean'].unique() if str(f).strip() != ''])))
        
        st.sidebar.markdown("<h3 style='margin-top:0; font-size:20px; color:#000000;'>Filtro Principal</h3>", unsafe_allow_html=True)
        st.sidebar.markdown("---")
        
        if len(fontes) == 0:
            st.sidebar.error("⚠️ Nenhuma fonte orçamentária localizada.")
            fonte_sel = ""
        else:
            fonte_sel = st.sidebar.selectbox("Selecione a Fonte Orçamentária:", options=fontes, index=0)
            
        st.sidebar.markdown("---")
        st.sidebar.markdown("<h3 style='margin-size:0; font-size:16px; color:#000000;'>Mapeamento Geral</h3>", unsafe_allow_html=True)
        
        # Uso de state para evitar re-renderização fantasma pesada de gráficos e poupar memória
        if st.sidebar.button("🌐 Consultar Panorama Geral Municipal", use_container_width=True):
            st.markdown("<div class='section-title' style='color:#1e3a8a; border-bottom:3px solid #1e3a8a;'>🌐 Panorama Consolidado Histórico — Geral por Fontes Orçamentárias</div>", unsafe_allow_html=True)
            tot_global_repasse = float(df['Receitas / Repasses'].sum())
            tot_global_rendimento = float(df['rendimentos'].sum())
            tot_global_gasto = float(df['Valor Bruto da NF'].sum())
            
            g1, g2 = st.columns(2)
            g1.markdown(f'''<div class='metric-container' style='background-color:#f8fafc; border-color:#2563eb; border-left:6px solid #2563eb;'><div>💰 Total de Receitas Municipais (Global)</div><div style="font-size:17px; font-weight:700; color:#059669;">Repasses: {fmt(tot_global_repasse)}</div><div style="font-size:17px; font-weight:700; color:#2563eb;">Rendimentos: {fmt(tot_global_rendimento)}</div></div>''', unsafe_allow_html=True)
            g2.markdown(f'''<div class='metric-container' style='border-color:#dc2626; border-left: 6px solid #dc2626;'><div>💸 Total Já Liquidado Municipal (Gasto Bruto)</div><div style="font-size:24px; font-weight:800; color:#dc2626;">{fmt(tot_global_gasto)}</div></div>''', unsafe_allow_html=True)

            df_cronologico = df.groupby('ano_mov').agg({'Receitas / Repasses':'sum', 'rendimentos':'sum', 'Valor Bruto da NF':'sum'}).reset_index().sort_values('ano_mov')
            df_cronologico['Saldo_Acumulado_Real'] = ((df_cronologico['Receitas / Repasses'] + df_cronologico['rendimentos']) - df_cronologico['Valor Bruto da NF']).cumsum()
            
            fig_tempo = go.Figure(go.Scatter(x=df_cronologico['ano_mov'], y=df_cronologico['Saldo_Acumulado_Real'], mode='lines+markers+text', name='Caixa', line=dict(color='#059669', width=4), text=[f"<b>{fmt(v)}</b>" for v in df_cronologico['Saldo_Acumulado_Real']], textposition="top center"))
            fig_tempo.update_layout(title="<b>Evolução Cronológica do Saldo Disponível Real em Caixa (Cumulativo)</b>", plot_bgcolor='#ffffff', paper_bgcolor='#ffffff', height=280, margin=dict(l=10,r=10,t=40,b=10), xaxis=dict(type='category'), yaxis=dict(showgrid=True, gridcolor='#e2e8f0'))
            st.plotly_chart(fig_tempo, use_container_width=True)

        if st.sidebar.button("🔍 Consultar Fontes por Deputado", use_container_width=True):
            df_dep = df.groupby(['deputado', 'fonte_clean']).agg({'Receitas / Repasses': 'sum', 'Valor Bruto da NF': 'sum', 'desc_clean': 'first'}).reset_index()
            df_dep = df_dep[(df_dep['deputado'] != 'Não Informado') & (df_dep['deputado'] != '')]
            df_dep['Saldo'] = df_dep['Receitas / Repasses'] - df_dep['Valor Bruto da NF']
            df_dep['Receitas / Repasses'], df_dep['Valor Bruto da NF'], df_dep['Saldo'] = df_dep['Receitas / Repasses'].apply(fmt), df_dep['Valor Bruto da NF'].apply(fmt), df_dep['Saldo'].apply(fmt)
            df_dep.columns = ['Parlamentar / Deputado', 'Fonte', '(+) Valor Repasse', '(-) Total Já Gasto', '(=) Saldo Disponível', 'Descrição do Objeto / Convênio']
            st.dataframe(df_dep, use_container_width=True, hide_index=True)

        if st.sidebar.button("🏛️ Consultar Fontes por Secretaria", use_container_width=True):
            df_sec = df.groupby(['secretaria', 'fonte_clean']).agg({'Receitas / Repasses': 'sum', 'Valor Bruto da NF': 'sum'}).reset_index()
            df_sec = df_sec[df_sec['secretaria'] != 'Não Especificada']
            df_sec['Saldo'] = df_sec['Receitas / Repasses'] - df_sec['Valor Bruto da NF']
            df_sec['Receitas / Repasses'], df_sec['Valor Bruto da NF'], df_sec['Saldo'] = df_sec['Receitas / Repasses'].apply(fmt), df_sec['Valor Bruto da NF'].apply(fmt), df_sec['Saldo'].apply(fmt)
            df_sec.columns = ['Secretaria / Pasta', 'Fonte Orçamentária', '(+) Repasses Destinados', '(-) Valores Gastos', '(=) Saldo Disponível Real']
            st.dataframe(df_sec, use_container_width=True, hide_index=True)

        if fonte_sel != "":
            df_final = df[df['fonte_clean'] == fonte_sel]
            if not df_final.empty:
                dep_vinculo = ", ".join([d for d in df_final['deputado'].unique() if d != ''])
                eme_vinculo = ", ".join([e for e in df_final['emenda_clean'].unique() if e != ''])
                pln_vinculo = ", ".join([p for p in df_final['plano_clean'].unique() if p != ''])
                conta_vinculada = str(df_final['conta corrente'].iloc[0]).strip()
                
                saldo_exclusivo_fonte = float(df_final['Receitas / Repasses'].sum() + df_final['rendimentos'].sum()) - float(df_final['Valor Bruto da NF'].sum())
                df_conta_total_banco = df[df['conta corrente'] == conta_vinculada] if conta_vinculada != "Não Informada" else pd.DataFrame()
                saldo_real_banco_total = float(df_conta_total_banco['Receitas / Repasses'].sum() + df_conta_total_banco['rendimentos'].sum()) - float(df_conta_total_banco['Valor Bruto da NF'].sum()) if not df_conta_total_banco.empty else saldo_exclusivo_fonte

                st.markdown(f"<div class='main-title'>Controle de Emendas — Fonte: {fonte_sel}</div>", unsafe_allow_html=True)
                st.markdown(f'''<div class='kpi-row-container'>
                    <div class='kpi-card-head'>
                        <div class='kpi-label'>🎯 Saldo Isolado do Recurso</div>
                        <div class='kpi-value'>{fmt(saldo_exclusivo_fonte)} <span style="font-size:12px; font-weight:600; color:#475569;">Disponível na Fonte {fonte_sel}</span></div>
                    </div>
                    <div class='kpi-card-head-blue'>
                        <div class='kpi-label' style='color:#1e40af;'>🏦 Conta Corrente Vinculada: {conta_vinculada}</div>
                        <div class='kpi-value' style='color:#2563eb;'>{fmt(saldo_real_banco_total)} <span style="font-size:12px; font-weight:600; color:#475569;">Saldo Real no Banco</span></div>
                    </div>
                </div>''', unsafe_allow_html=True)
                
                st.markdown(f'''<div style="margin-top:10px; margin-bottom:15px;">
                    <div class='meta-tag'>👤 Deputado: {dep_vinculo}</div>
                    <div class='meta-tag'>📄 Número Emenda: {eme_vinculo}</div>
                    <div class='meta-tag'>🎯 Plano de Ação: {pln_vinculo}</div>
                </div>''', unsafe_allow_html=True)
                st.markdown("---")
                
                secretarias = [s for s in df_final['secretaria'].unique() if s != '']
                if len(secretarias) > 1:
                    st.markdown("<div class='section-title' style='color:#1e3a8a; border-bottom: 3px solid #1e3a8a;'>🌍 RESUMO GERAL CONSOLIDADO (TODAS AS SECRETARIAS)</div>", unsafe_allow_html=True)
                    global_repasse, global_rendimento, global_despesa_bruta = float(df_final['Receitas / Repasses'].sum()), float(df_final['rendimentos'].sum()), float(df_final['Valor Bruto da NF'].sum())
                    global_saldo = (global_repasse + global_rendimento) - global_despesa_bruta
                    
                    st.markdown(f'''<table class='extrato-table'>
                        <tr class='extrato-row'><td class='extrato-cell-label'>(+) REPASSE TOTAL ENTRADO NA FONTE (MÃE)</td><td class='extrato-cell-val' style='color:#059669;'>{fmt(global_repasse)}</td></tr>
                        <tr class='extrato-row'><td class='extrato-cell-label'>(+) RENDIMENTOS DE APLICAÇÃO GLOBAIS</td><td class='extrato-cell-val' style='color:#2563eb;'>{fmt(global_rendimento)}</td></tr>
                        <tr class='extrato-row'><td>(-) DESPESAS CONTRATADAS TOTAIS (TODAS AS SECRETARIAS)</td><td class='extrato-cell-val' style='color:#dc2626;'>{fmt(global_despesa_bruta)}</td></tr>
                        <tr class='extrato-row-final' style='background-color:#ecf2ff;'><td class='extrato-cell-label'>(=) SALDO REAL ACUMULADO DISPONÍVEL NA EMENDA</td><td class='extrato-cell-val' style='color:{"#059669" if global_saldo >= 0 else "#dc2626"}; font-size:15px;'>{fmt(global_saldo)}</td></tr>
                    </table>''', unsafe_allow_html=True)

                st.markdown("<div class='section-title'>🏢 Divisão de Recursos por Secretaria Detalhada</div>", unsafe_allow_html=True)
                for sec in secretarias:
                    df_sec = df_final[df_final['secretaria'] == sec]
                    sec_repasse, sec_rendimento, sec_despesa_bruta = float(df_sec['Receitas / Repasses'].sum()), float(df_sec['rendimentos'].sum()), float(df_sec['Valor Bruto da NF'].sum())
                    sec_saldo = (sec_repasse + sec_rendimento) - sec_despesa_bruta
                    
                    st.markdown(f"<div class='secretaria-header'>🏛️ {sec.upper()}</div>", unsafe_allow_html=True)
                    st.markdown(f'''<table class='extrato-table'>
                        <tr class='extrato-row'><td class='extrato-cell-label'>(+) REPASSE DESTINADO PARA {sec.upper()}</td><td class='extrato-cell-val' style='color:#059669;'>{fmt(sec_repasse)}</td></tr>
                        <tr class='extrato-row'><td class='extrato-cell-label'>(+) RENDIMENTOS DA CONTA DE {sec.upper()}</td><td class='extrato-cell-val' style='color:#2563eb;'>{fmt(sec_rendimento)}</td></tr>
                        <tr class='extrato-row'><td class='extrato-cell-label'>(-) DESPESAS LIQUIDADAS POR {sec.upper()} (NF BRUTA)</td><td class='extrato-cell-val' style='color:#dc2626;'>{fmt(sec_despesa_bruta)}</td></tr>
                        <tr class='extrato-row-final'><td class='extrato-cell-label'>(=) SALDO ATUAL LIVRE — {sec.upper()}</td><td class='extrato-cell-val' style='color:#059669;'>{fmt(sec_saldo)}</td></tr>
                    </table>''', unsafe_allow_html=True)

                # Detalhamento de Lançamentos enxuto
                st.markdown("<div class='section-title'>📋 Detalhamento dos Lançamentos</div>", unsafe_allow_html=True)
                df_exibicao = df_final[df_final['EMPENHO_COL'].astype(str).str.strip().replace(['nan','-','None'], None).notna()]
                if not df_exibicao.empty:
                    df_tab = pd.DataFrame({'DATA': df_exibicao['DATA_LANCAMENTO'], 'EMPENHO': df_exibicao['EMPENHO_COL'], 'NOTA': df_exibicao['NOTA_COL'], 'VALOR BRUTO NF': df_exibicao['Valor Bruto da NF'].apply(fmt), 'Links/PDF': df_exibicao['PDF_GERAL']})
                    st.dataframe(df_tab, use_container_width=True, hide_index=True)
except Exception as e:
    st.error(f"Erro de carregamento: {e}")
