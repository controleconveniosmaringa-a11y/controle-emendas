import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
import os

# 1. CONFIGURAÇÃO ESTRUTURAL DA PÁGINA (Executada em nível de Kernel)
st.set_page_config(page_title="Controle de Emendas", page_icon="📊", layout="wide")

# Funções auxiliares de vetorização matemática de alta velocidade
def _limpar_fonte(df_serie):
    return df_serie.fillna('').astype(str).str.strip().str.split('.').str[0].str.lower().str.replace('nan', '', regex=False).str.replace('-', '', regex=False)

def _limpar_numerico(df_serie):
    return pd.to_numeric(df_serie.fillna(0).astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip(), errors='coerce').fillna(0.0)

# 2. CARREGAMENTO DE DADOS COM PRÉ-PROCESSAMENTO CENTRALIZADO (CACHE REAL DE NÍVEL 1)
@st.cache_data(ttl=3600, show_spinner="Otimizando índices de alta velocidade...")
def carregar_e_indexar_base():
    if not os.path.exists("dados.csv"):
        return pd.DataFrame()
        
    df_raw = pd.read_csv("dados.csv", low_memory=False)
    df = pd.DataFrame()
    colunas_mapeadas = {}
    
    for c in df_raw.columns:
        c_clean = str(c).strip().lower()
        c_clean = re.sub(r'[^\w\s]', '', c_clean).strip()
        c_clean = c_clean.replace('â', 'a').replace('ç', 'c').replace('ã', 'a').replace('ó', 'o')
        colunas_mapeadas[c_clean] = df_raw[c]
        
    def pegar_serie(nome, padrao=''):
        for c_limpa, dados in colunas_mapeadas.items():
            if nome in c_limpa:
                return dados
        return pd.Series([padrao] * len(df_raw))

    df['fonte_clean'] = _limpar_fonte(pegar_serie('fonte'))
    df['emenda_clean'] = pegar_serie('emenda').fillna('-').astype(str).str.strip().str.split('.').str[0]
    df['plano_clean'] = pegar_serie('plano').fillna('-').astype(str).str.strip().str.split('.').str[0]
    
    df['EMPENHO_COL'] = pegar_serie('empenho').fillna('-').astype(str).str.strip()
    df['NOTA_COL'] = pegar_serie('nota').fillna('-').astype(str).str.strip()
    df['PDF_GERAL'] = pegar_serie('pdf').fillna('-').astype(str).str.strip()
    
    df['secretaria'] = pegar_serie('secretaria').fillna('Não Especificada').astype(str).str.strip().str.replace('^$', 'Não Especificada', regex=True)
    df['deputado'] = pegar_serie('deputado').fillna('Não Informado').astype(str).str.strip().str.replace('^$', 'Não Informado', regex=True)
    df['desc_clean'] = pegar_serie('descricao').fillna('Sem descrição informada').astype(str).str.strip()
    df['conta corrente'] = pegar_serie('conta').fillna('Não Informada').astype(str).str.strip().str.replace('^$', 'Não Informada', regex=True)

    coluna_data = next((c for c in colunas_mapeadas if 'data' in c and 'venc' not in c and 'nota' not in c), None)
    df['DATA_LANCAMENTO'] = colunas_mapeadas[coluna_data].fillna('-').astype(str).str.strip() if coluna_data else pegar_serie('data', '-')
    df['ano_mov'] = df['DATA_LANCAMENTO'].str.extract(r'(20\d{2})').fillna('2025')

    df['Receitas / Repasses'] = _limpar_numerico(pegar_serie('repasse'))
    df['rendimentos'] = _limpar_numerico(pegar_serie('rendimento'))
    df['Valor Bruto da NF'] = _limpar_numerico(pegar_serie('bruto'))
    
    return df

# 3. INTERFACE E MODELAGEM VISUAL CSS
st.markdown('''<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght=400;500;600;700;800&display=swap');
    html, body, [class*="css"], [data-testid="stAppViewContainer"] { font-family: 'Inter', sans-serif; background-color: #ffffff !important; color: #000000 !important; }
    [data-testid="stSidebar"], [data-testid="stSidebarUserContent"] { background-color: #ffffff !important; border-right: 2px solid #cbd5e1 !important; }
    [data-testid="stSidebar"] div[data-testid="stSelectbox"] { background-color: #f1f5f9 !important; padding: 2px; border-radius: 6px; }
    .main-title { font-size: 34px; font-weight: 800; color: #0f172a; letter-spacing: -1.2px; margin-bottom: 5px; }
    .kpi-row-container { display: flex; gap: 15px; margin-top: 10px; margin-bottom: 5px; }
    .kpi-card-head { flex: 1; background-color: #ffffff; border: 2px solid #000000; border-radius: 8px; padding: 14px 20px; }
    .kpi-card-head-blue { flex: 1; background-color: #f8fafc; border: 2px solid #2563eb; border-radius: 8px; padding: 14px 20px; border-left: 6px solid #2563eb; }
    .kpi-label { font-size: 12px; font-weight: 700; color: #475569; text-transform: uppercase; }
    .kpi-value { font-size: 24px; font-weight: 800; color: #059669; }
    .section-title { font-size: 14px; font-weight: 800; text-transform: uppercase; color: #000000; margin-top: 25px; margin-bottom: 10px; padding-bottom: 6px; border-bottom: 3px solid #000000; }
    .meta-tag { background-color: #f1f5f9; color: #000000; padding: 5px 12px; border-radius: 6px; font-weight: 700; font-size: 12px; border: 1px solid #cbd5e1; margin-right: 6px; display: inline-block; }
    .secretaria-header { font-size: 16px; font-weight: 800; color: #000000; margin-top: 15px; padding-left: 6px; border-left: 5px solid #000000; }
    .metric-container { background-color: #ffffff; border: 2px solid #000000; border-radius: 8px; padding: 18px; display: flex; flex-direction: column; justify-content: center; min-height: 100px; }
    .extrato-table { width: 100%; border-collapse: collapse; margin-top: 8px; background-color: #ffffff; border: 2px solid #000000; border-radius: 6px; overflow: hidden; }
    .extrato-row { border-bottom: 1px solid #cbd5e1; }
    .extrato-row-final { background-color: #f8fafc; font-weight: 800; border-top: 2px solid #000000; }
    .extrato-cell-label { padding: 10px 15px; font-size: 12px; font-weight: 700; color: #0f172a; text-align: left; }
    .extrato-cell-val { padding: 10px 15px; font-size: 13px; font-weight: 800; text-align: right; white-space: nowrap; }
    .grid-header { background-color: #2563eb; color: #ffffff; padding: 10px; font-weight: 800; font-size: 12px; text-align: center; border: 1px solid #1e40af; }
    .grid-row-active { background-color: #f8fafc; padding: 10px; font-weight: 700; border-bottom: 1px solid #cbd5e1; font-size: 12px; }
    .grid-row-normal { padding: 10px; border-bottom: 1px solid #cbd5e1; font-size: 12px; }
    .grid-total { background-color: #eff6ff; padding: 12px; font-weight: 800; font-size: 12px; color: #1e3a8a; border-top: 2px solid #2563eb; }
</style>''', unsafe_allow_html=True)

try:
    df = carregar_e_indexar_base()
    
    if not df.empty:
        def fmt(v):
            return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        fontes_disponiveis = sorted(df['fonte_clean'].unique())
        fontes = [f for f in fontes_disponiveis if f not in ['', 'nan']]
        
        st.sidebar.markdown("<h3 style='margin-top:0; font-size:16px; color:#000000;'>Filtro Principal</h3>", unsafe_allow_html=True)
        fonte_sel = st.sidebar.selectbox("Selecione a Fonte Orçamentária:", options=fontes, index=0)
        
        tab_ativa, tab_geral, tab_deputados, tab_secretarias = st.tabs([
            f"🎯 Fonte Ativa: {fonte_sel}", "🌐 Panorama Geral", "🔍 Por Deputado", "🏛️ Por Secretaria"
        ])
        
        # ABA 1: OPERAÇÃO COMPLETA COM CONCILIAÇÃO BANCÁRIA REATIVADA
        with tab_ativa:
            if fonte_sel:
                df_final = df[df['fonte_clean'] == fonte_sel]
                
                if not df_final.empty:
                    dep_vinculo = df_final['deputado'].unique()[0]
                    eme_vinculo = df_final['emenda_clean'].unique()[0]
                    pln_vinculo = df_final['plano_clean'].unique()[0]
                    conta_vinculada = df_final['conta corrente'].iloc[0]
                    
                    sum_repasse = float(df_final['Receitas / Repasses'].sum())
                    sum_rendimento = float(df_final['rendimentos'].sum())
                    sum_gasto = float(df_final['Valor Bruto da NF'].sum())
                    saldo_exclusivo_fonte = (sum_repasse + sum_rendimento) - sum_gasto
                    
                    df_conta_total_banco = df[df['conta corrente'] == conta_vinculada] if conta_vinculada != "Não Informada" else pd.DataFrame()
                    saldo_real_banco_total = float(df_conta_total_banco['Receitas / Repasses'].sum() + df_conta_total_banco['rendimentos'].sum()) - float(df_conta_total_banco['Valor Bruto da NF'].sum()) if not df_conta_total_banco.empty else saldo_exclusivo_fonte

                    st.markdown(f"<div class='main-title'>Controle de Emendas — Fonte: {fonte_sel}</div>", unsafe_allow_html=True)
                    st.markdown(f'''<div class='kpi-row-container'>
                        <div class='kpi-card-head'>
                            <div class='kpi-label'>🎯 Saldo Isolado do Recurso</div>
                            <div class='kpi-value'>{fmt(saldo_exclusivo_fonte)}</div>
                        </div>
                        <div class='kpi-card-head-blue'>
                            <div class='kpi-label' style='color:#1e40af;'>🏦 Conta Corrente Vinculada: {conta_vinculada}</div>
                            <div class='kpi-value' style='color:#2563eb;'>{fmt(saldo_real_banco_total)}</div>
                        </div>
                    </div>''', unsafe_allow_html=True)
                    
                    st.markdown(f'''<div style='margin-bottom:10px;'>
                        <div class='meta-tag'>👤 Deputado: {dep_vinculo}</div>
                        <div class='meta-tag'>📄 Número Emenda: {eme_vinculo}</div>
                        <div class='meta-tag'>🎯 Plano de Ação: {pln_vinculo}</div>
                    </div>''', unsafe_allow_html=True)
                    
                    secretarias = [s for s in df_final['secretaria'].unique() if s != '']
                    
                    # RETORNO DO EXTRATO CONSOLIDADO MÃE (MÚLTIPLAS SECRETARIAS)
                    if len(secretarias) > 1:
                        st.markdown("<div class='section-title' style='color:#1e3a8a; border-bottom: 3px solid #1e3a8a;'>🌍 RESUMO GERAL CONSOLIDADO (TODAS AS SECRETARIAS)</div>", unsafe_allow_html=True)
                        st.markdown(f'''<table class='extrato-table'>
                            <tr class='extrato-row'><td class='extrato-cell-label'>(+) REPASSE TOTAL ENTRADO NA FONTE (MÃE)</td><td class='extrato-cell-val' style='color:#059669;'>{fmt(sum_repasse)}</td></tr>
                            <tr class='extrato-row'><td class='extrato-cell-label'>(+) RENDIMENTOS DE APLICAÇÃO GLOBAIS</td><td class='extrato-cell-val' style='color:#2563eb;'>{fmt(sum_rendimento)}</td></tr>
                            <tr class='extrato-row'><td>(-) DESPESAS CONTRATADAS TOTAIS (TODAS AS SECRETARIAS)</td><td class='extrato-cell-val' style='color:#dc2626;'>{fmt(sum_gasto)}</td></tr>
                            <tr class='extrato-row-final' style='background-color:#ecf2ff;'><td class='extrato-cell-label'>(=) SALDO REAL ACUMULADO DISPONÍVEL NA EMENDA</td><td class='extrato-cell-val' style='color:{"#059669" if saldo_exclusivo_fonte >= 0 else "#dc2626"}; font-size:14px;'>{fmt(saldo_exclusivo_fonte)}</td></tr>
                        </table>''', unsafe_allow_html=True)

                    st.markdown("<div class='section-title'>🏢 Divisão de Recursos por Secretaria Detalhada</div>", unsafe_allow_html=True)
                    for sec in secretarias:
                        df_sec = df_final[df_final['secretaria'] == sec]
                        sec_repasse = float(df_sec['Receitas / Repasses'].sum())
                        sec_rendimento = float(df_sec['rendimentos'].sum())
                        sec_despesa_bruta = float(df_sec['Valor Bruto da NF'].sum())
                        sec_saldo = (sec_repasse + sec_rendimento) - sec_despesa_bruta
                        
                        st.markdown(f"<div class='secretaria-header'>🏛️ {sec.upper()}</div>", unsafe_allow_html=True)
                        st.markdown(f'''<table class='extrato-table'>
                            <tr class='extrato-row'><td class='extrato-cell-label'>(+) REPASSE DESTINADO PARA {sec.upper()}</td><td class='extrato-cell-val' style='color:#059669;'>{fmt(sec_repasse)}</td></tr>
                            <tr class='extrato-row'><td class='extrato-cell-label'>(+) RENDIMENTOS DA CONTA DE {sec.upper()}</td><td class='extrato-cell-val' style='color:#2563eb;'>{fmt(sec_rendimento)}</td></tr>
                            <tr class='extrato-row'><td class='extrato-cell-label'>(-) DESPESAS LIQUIDADAS POR {sec.upper()} (NF BRUTA)</td><td class='extrato-cell-val' style='color:#dc2626;'>{fmt(sec_despesa_bruta)}</td></tr>
                            <tr class='extrato-row-final'><td class='extrato-cell-label'>(=) SALDO ATUAL LIVRE — {sec.upper()}</td><td class='extrato-cell-val' style='color:#059669;'>{fmt(sec_saldo)}</td></tr>
                        </table>''', unsafe_allow_html=True)

                    # RETORNO COMPLETO DA CONCILIAÇÃO BANCÁRIA COMPARTILHADA POR EXERCÍCIO
                    if conta_vinculada != "Não Informada" and not df_conta_total_banco.empty:
                        st.markdown(f"<div class='section-title' style='color:#2563eb; border-bottom:3px solid #2563eb;'>⚖️ ABERTURA DE SALDOS — CONTA CORRENTE: {conta_vinculada}</div>", unsafe_allow_html=True)
                        
                        anos_bancarios = sorted(list(set([str(a) for a in df_conta_total_banco['ano_mov'] if a not in ['None', 'nan']])))
                        ano_banco_sel = st.selectbox("📅 Selecione o Exercício para Conciliação Bancária:", ["Exibir Saldo Histórico Acumulado"] + anos_bancarios, key="filtro_ano_banco")
                        
                        df_banco_proc = df_conta_total_banco if ano_banco_sel == "Exibir Saldo Histórico Acumulado" else df_conta_total_banco[df_conta_total_banco['ano_mov'] == ano_banco_sel]
                        rotulo_tabela = "SALDO HISTÓRICO ACUMULADO GERAL" if ano_banco_sel == "Exibir Saldo Histórico Acumulado" else f"EXERCÍCIO FISCAL DE {ano_banco_sel}"
                        
                        fontes_compartilhadas = sorted([fc for fc in df_banco_proc['fonte_clean'].unique() if fc != ''])
                        
                        c_head1, c_head2, c_head3, c_head4, c_head5 = st.columns([2.5, 1.5, 1.5, 1.5, 2])
                        c_head1.markdown(f"<div class='grid-header' style='text-align:left;'>ORIGEM DO RECURSO ({rotulo_tabela})</div>", unsafe_allow_html=True)
                        c_head2.markdown("<div class='grid-header' style='background-color:#059669; border-color:#047857;'>(+) REPASSES</div>", unsafe_allow_html=True)
                        c_head3.markdown("<div class='grid-header' style='background-color:#2563eb; border-color:#1d4ed8;'>(+) RENDIMENTOS</div>", unsafe_allow_html=True)
                        c_head4.markdown("<div class='grid-header' style='background-color:#dc2626; border-color:#b91c1c;'>(-) DESPESAS</div>", unsafe_allow_html=True)
                        c_head5.markdown("<div class='grid-header' style='background-color:#1e293b; border-color:#0f172a;'>(=) SALDO BANCO</div>", unsafe_allow_html=True)
                        
                        b_rec, b_ren, b_des, b_sal_tot = 0.0, 0.0, 0.0, 0.0
                        
                        for f_item in fontes_compartilhadas:
                            df_item = df_banco_proc[df_banco_proc['fonte_clean'] == f_item]
                            f_rep = float(df_item['Receitas / Repasses'].sum())
                            f_ren = float(df_item['rendimentos'].sum())
                            f_des = float(df_item['Valor Bruto da NF'].sum())
                            f_sal = (f_rep + f_ren) - f_des
                            
                            b_rec += f_rep
                            b_ren += f_ren
                            b_des += f_des
                            b_sal_tot += f_sal
                            
                            classe = "grid-row-active" if f_item == fonte_sel else "grid-row-normal"
                            marcador = " 👈 (Ativa)" if f_item == fonte_sel else ""
                            
                            c_row1, c_row2, c_row3, c_row4, c_row5 = st.columns([2.5, 1.5, 1.5, 1.5, 2])
                            c_row1.markdown(f"<div class='{classe}'>📍 Fonte Orçamentária: <b>{f_item}</b>{marcador}</div>", unsafe_allow_html=True)
                            c_row2.markdown(f"<div class='{classe}' style='text-align:right; color:#059669;'>{fmt(f_rep)}</div>", unsafe_allow_html=True)
                            c_row3.markdown(f"<div class='{classe}' style='text-align:right; color:#2563eb;'>{fmt(f_ren)}</div>", unsafe_allow_html=True)
                            c_row4.markdown(f"<div class='{classe}' style='text-align:right; color:#dc2626;'>{fmt(f_des)}</div>", unsafe_allow_html=True)
                            c_row5.markdown(f"<div class='{classe}' style='text-align:right; font-weight:800; color:{"#059669" if f_sal >= 0 else "#dc2626"};'>{fmt(f_sal)}</div>", unsafe_allow_html=True)
                            
                        c_tot1, c_tot2, c_tot3, c_tot4, c_tot5 = st.columns([2.5, 1.5, 1.5, 1.5, 2])
                        c_tot1.markdown(f"<div class='grid-total'>💰 VALOR DISPONÍVEL TOTAL NA CONTA (SALDO DO BANCO)</div>", unsafe_allow_html=True)
                        c_tot2.markdown(f"<div class='grid-total' style='text-align:right; color:#475569;'>{fmt(b_rec)}</div>", unsafe_allow_html=True)
                        c_tot3.markdown(f"<div class='grid-total' style='text-align:right; color:#475569;'>{fmt(b_ren)}</div>", unsafe_allow_html=True)
                        c_tot4.markdown(f"<div class='grid-total' style='text-align:right; color:#dc2626;'>{fmt(b_des)}</div>", unsafe_allow_html=True)
                        c_tot5.markdown(f"<div class='grid-total' style='text-align:right; font-size:14px; color:#1e3a8a; background-color:#dbeafe; border:2px solid #2563eb;'><b>{fmt(b_sal_tot)}</b></div>", unsafe_allow_html=True)

                    # Tabela detalhada de lançamentos
                    st.markdown("<div class='section-title'>📋 Detalhamento dos Lançamentos</div>", unsafe_allow_html=True)
                    df_validos = df_final[df_final['EMPENHO_COL'] != '-']
                    if not df_validos.empty:
                        df_render = pd.DataFrame({
                            'DATA': df_validos['DATA_LANCAMENTO'],
                            'EMPENHO': df_validos['EMPENHO_COL'],
                            'NOTA': df_validos['NOTA_COL'],
                            'VALOR BRUTO': df_validos['Valor Bruto da NF'].apply(fmt),
                            'PDF': df_validos['PDF_GERAL']
                        })
                        st.dataframe(df_render, use_container_width=True, hide_index=True)

        # ABA 2: PANORAMA GLOBAL MUNICIPAL HISTÓRICO
        with tab_geral:
            st.markdown("<div class='section-title' style='color:#1e3a8a; border-bottom:3px solid #1e3a8a;'>🌐 Balanço Consolidado de Recursos</div>", unsafe_allow_html=True)
            g_rep, g_ren, g_gas = float(df['Receitas / Repasses'].sum()), float(df['rendimentos'].sum()), float(df['Valor Bruto da NF'].sum())
            
            col_l1, col_l2 = st.columns(2)
            col_l1.markdown(f'''<div class='metric-container' style='background-color:#f8fafc; border-color:#2563eb; border-left:6px solid #2563eb;'><div>💰 Total Entradas Recebidas (Histórico)</div><div style="font-size:22px; font-weight:800; color:#059669;">{fmt(g_rep + g_ren)}</div></div>''', unsafe_allow_html=True)
            col_l2.markdown(f'''<div class='metric-container' style='border-color:#dc2626; border-left: 6px solid #dc2626;'><div>💸 Total Saídas Liquidadas (Histórico)</div><div style="font-size:22px; font-weight:800; color:#dc2626;">{fmt(g_gas)}</div></div>''', unsafe_allow_html=True)

            df_cronologico = df.groupby('ano_mov').agg({'Receitas / Repasses':'sum', 'rendimentos':'sum', 'Valor Bruto da NF':'sum'}).reset_index().sort_values('ano_mov')
            df_cronologico['Saldo_Acumulado'] = ((df_cronologico['Receitas / Repasses'] + df_cronologico['rendimentos']) - df_cronologico['Valor Bruto da NF']).cumsum()
            
            fig = go.Figure(go.Scatter(x=df_cronologico['ano_mov'], y=df_cronologico['Saldo_Acumulado'], mode='lines+markers+text', line=dict(color='#059669', width=4), text=[fmt(v) for v in df_cronologico['Saldo_Acumulado']], textposition="top center"))
            fig.update_layout(plot_bgcolor='#ffffff', paper_bgcolor='#ffffff', height=240, margin=dict(l=5,r=5,t=30,b=5), xaxis=dict(type='category'), yaxis=dict(showgrid=True, gridcolor='#e2e8f0'))
            st.plotly_chart(fig, use_container_width=True)

        # ABA 3: RANKING DE DEPUTADOS PARLAMENTARES
        with tab_deputados:
            st.markdown("<div class='section-title'>📊 Repasses por Parlamentar</div>", unsafe_allow_html=True)
            df_dep = df.groupby(['deputado', 'fonte_clean']).agg({'Receitas / Repasses': 'sum', 'Valor Bruto da NF': 'sum', 'desc_clean': 'first'}).reset_index()
            df_dep = df_dep[df_dep['deputado'] != 'Não Informado']
            df_dep['Saldo'] = df_dep['Receitas / Repasses'] - df_dep['Valor Bruto da NF']
            
            df_dep['Receitas / Repasses'] = df_dep['Receitas / Repasses'].apply(fmt)
            df_dep['Valor Bruto da NF'] = df_dep['Valor Bruto da NF'].apply(fmt)
            df_dep['Saldo'] = df_dep['Saldo'].apply(fmt)
            df_dep.columns = ['Parlamentar / Deputado', 'Fonte', '(+) Repasses', '(-) Gastos', '(=) Saldo Livre', 'Descrição']
            st.dataframe(df_dep, use_container_width=True, hide_index=True)

        # ABA 4: MAPA DE DIRECIONAMENTO POR SECRETARIAS
        with tab_secretarias:
            st.markdown("<div class='section-title'>🏛️ Recursos Direcionados por Secretaria</div>", unsafe_allow_html=True)
            df_sec = df.groupby(['secretaria', 'fonte_clean']).agg({'Receitas / Repasses': 'sum', 'Valor Bruto da NF': 'sum'}).reset_index()
            df_sec = df_sec[df_sec['secretaria'] != 'Não Especificada']
            df_sec['Saldo'] = df_sec['Receitas / Repasses'] - df_sec['Valor Bruto da NF']
            
            df_sec['Receitas / Repasses'] = df_sec['Receitas / Repasses'].apply(fmt)
            df_sec['Valor Bruto da NF'] = df_sec['Valor Bruto da NF'].apply(fmt)
            df_sec['Saldo'] = df_sec['Saldo'].apply(fmt)
            df_sec.columns = ['Secretaria / Pasta', 'Fonte Orçamentária', '(+) Repasses', '(-) Gastos', '(=) Saldo Real']
            st.dataframe(df_sec, use_container_width=True, hide_index=True)
            
except Exception as e:
    st.error(f"Erro no processamento completo: {e}")
