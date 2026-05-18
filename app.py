import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
import os

# 1. CONFIGURAÇÃO ESTRUTURAL DE NÍVEL DE KERNEL (Deve ser o primeiro comando)
st.set_page_config(page_title="Controle de Emendas", page_icon="📊", layout="wide")

# Interface Visual Enxuta via CSS de Alta Performance
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
    .extrato-table { width: 100%; border-collapse: collapse; margin-top: 8px; background-color: #ffffff; border: 2px solid #000000; border-radius: 6px; overflow: hidden; }
    .extrato-row { border-bottom: 1px solid #cbd5e1; }
    .extrato-row-final { background-color: #f8fafc; font-weight: 800; border-top: 2px solid #000000; }
    .extrato-cell-label { padding: 10px 15px; font-size: 12px; font-weight: 700; color: #0f172a; text-align: left; }
    .extrato-cell-val { padding: 10px 15px; font-size: 13px; font-weight: 800; text-align: right; white-space: nowrap; }
</style>''', unsafe_allow_html=True)

# 2. MOTOR DE LEITURA COMPARTILHADO ULTRA RÁPIDO (RAM DIRECTA)
@st.cache_resource
def obter_base_dados_global():
    if not os.path.exists("dados.csv"):
        return pd.DataFrame()
        
    df_raw = pd.read_csv("dados.csv", low_memory=False, dtype=str).fillna('')
    df = pd.DataFrame()
    
    colunas_originais = {re.sub(r'[^\w\s]', '', str(c).strip().lower()).replace('â', 'a').replace('ç', 'c').replace('ã', 'a').replace('ó', 'o'): c for c in df_raw.columns}
    
    def extrair(nome_chave):
        col_real = next((orig for limpa, orig in colunas_originais.items() if nome_chave in limpa), None)
        return df_raw[col_real].str.strip() if col_real else pd.Series([''] * len(df_raw))

    df['fonte_clean'] = extrair('fonte').str.split('.').str[0].str.lower().str.replace('-', '', regex=False)
    df['emenda_clean'] = extrair('emenda').str.split('.').str[0]
    df['plano_clean'] = extrair('plano').str.split('.').str[0]
    
    df['EMPENHO_COL'] = extrair('empenho').replace('', '-')
    df['NOTA_COL'] = extrair('nota').replace('', '-')
    df['PDF_GERAL'] = extrair('pdf').replace('', '-')
    
    df['secretaria'] = extrair('secretaria').replace('', 'Não Especificada')
    df['deputado'] = extrair('deputado').replace('', 'Não Informado')
    df['desc_clean'] = extrair('descricao').replace('', 'Sem descrição informada')
    df['conta corrente'] = extrair('conta').replace('', 'Não Informada')

    coluna_data = next((limpa for limpa in colunas_originais if 'data' in limpa and 'venc' not in limpa and 'nota' not in limpa), None)
    df['DATA_LANCAMENTO'] = df_raw[colunas_originais[coluna_data]].str.strip() if coluna_data else extrair('data')
    df['ano_mov'] = df['DATA_LANCAMENTO'].str.extract(r'(20\d{2})').fillna('2025')

    for col_num in ['repasse', 'rendimento', 'bruto']:
        serie_num = extrair(col_num).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df[col_num] = pd.to_numeric(serie_num, errors='coerce').fillna(0.0)
        
    return df

try:
    df = obter_base_dados_global()
    
    if not df.empty:
        def fmt(v):
            return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        fontes = sorted([f for f in df['fonte_clean'].unique() if f not in ['', 'nan']])
        
        st.sidebar.markdown("<h3 style='margin-top:0; font-size:16px; color:#000000;'>Filtro Principal</h3>", unsafe_allow_html=True)
        fonte_sel = st.sidebar.selectbox("Selecione a Fonte Orçamentária:", options=fontes, index=0)
        
        tab_ativa, tab_geral, tab_deputados, tab_secretarias = st.tabs([
            f"🎯 Fonte Ativa: {fonte_sel}", "🌐 Panorama Geral", "🔍 Por Deputado", "🏛️ Por Secretaria"
        ])
        
        with tab_ativa:
            if fonte_sel:
                df_final = df[df['fonte_clean'] == fonte_sel]
                
                if not df_final.empty:
                    dep_vinculo = df_final['deputado'].unique()[0]
                    eme_vinculo = df_final['emenda_clean'].unique()[0]
                    pln_vinculo = df_final['plano_clean'].unique()[0]
                    conta_vinculada = df_final['conta corrente'].iloc[0]
                    
                    st.markdown(f"<div class='main-title'>Controle de Emendas — Fonte: {fonte_sel}</div>", unsafe_allow_html=True)
                    
                    # 📅 1. SELETOR DE ANO CENTRAL UNIFICADO PARA TODA A FONTE ATIVA
                    anos_disponiveis = sorted(list(set([str(a) for a in df['ano_mov'].unique() if a not in ['', 'nan']])))
                    ano_selecionado = st.selectbox("📅 Selecione o Exercício Fiscal para Filtrar o Painel:", ["Exibir Histórico Acumulado Completo"] + anos_disponiveis, key="filtro_ano_global")
                    
                    # Definição dos escopos temporais para fluxo e para saldo (acumulativo)
                    if ano_selecionado == "Exibir Histórico Acumulado Completo":
                        df_fonte_fluxo = df_final
                        df_fonte_saldo = df_final
                        df_banco_fluxo = df[df['conta corrente'] == conta_vinculada] if conta_vinculada != "Não Informada" else pd.DataFrame()
                        df_banco_saldo = df_banco_fluxo
                    else:
                        df_fonte_fluxo = df_final[df_final['ano_mov'] == ano_selecionado]
                        df_fonte_saldo = df_final[df_final['ano_mov'].astype(int) <= int(ano_selecionado)]
                        
                        df_banco_base = df[df['conta corrente'] == conta_vinculada] if conta_vinculada != "Não Informada" else pd.DataFrame()
                        df_banco_fluxo = df_banco_base[df_banco_base['ano_mov'] == ano_selecionado] if not df_banco_base.empty else pd.DataFrame()
                        df_banco_saldo = df_banco_base[df_banco_base['ano_mov'].astype(int) <= int(ano_selecionado)] if not df_banco_base.empty else pd.DataFrame()

                    # Cálculos das métricas dos blocos superiores (Considerando os saldos acumulados)
                    saldo_exclusivo_fonte = float(df_fonte_saldo['repasse'].sum() + df_fonte_saldo['rendimento'].sum()) - float(df_fonte_saldo['bruto'].sum())
                    saldo_real_banco_total = float(df_banco_saldo['repasse'].sum() + df_banco_saldo['rendimento'].sum()) - float(df_banco_saldo['bruto'].sum()) if not df_banco_saldo.empty else saldo_exclusivo_fonte

                    st.markdown(f'''<div class='kpi-row-container'>
                        <div class='kpi-card-head'>
                            <div class='kpi-label'>🎯 Saldo Acumulado Disponível da Fonte ({ano_selecionado})</div>
                            <div class='kpi-value'>{fmt(saldo_exclusivo_fonte)}</div>
                        </div>
                        <div class='kpi-card-head-blue'>
                            <div class='kpi-label' style='color:#1e40af;'>🏦 Saldo Acumulado na Conta: {conta_vinculada} ({ano_selecionado})</div>
                            <div class='kpi-value' style='color:#2563eb;'>{fmt(saldo_real_banco_total)}</div>
                        </div>
                    </div>''', unsafe_allow_html=True)
                    
                    st.markdown(f'''<div style='margin-bottom:10px;'>
                        <div class='meta-tag'>👤 Deputado: {dep_vinculo}</div>
                        <div class='meta-tag'>📄 Número Emenda: {eme_vinculo}</div>
                        <div class='meta-tag'>🎯 Plano de Ação: {pln_vinculo}</div>
                    </div>''', unsafe_allow_html=True)
                    
                    secretarias = [s for s in df_final['secretaria'].unique() if s != '']
                    
                    # 🌍 RESUMO CONSOLIDADO MÃE (Sincronizado por Ano)
                    if len(secretarias) > 1:
                        st.markdown(f"<div class='section-title'>🌍 RESUMO CONSOLIDADO DA FONTE — ANO FILTRADO: {ano_selecionado}</div>", unsafe_allow_html=True)
                        sum_rep_mãe = float(df_fonte_fluxo['repasse'].sum())
                        sum_ren_mãe = float(df_fonte_fluxo['rendimento'].sum())
                        sum_gas_mãe = float(df_fonte_fluxo['bruto'].sum())
                        
                        st.markdown(f'''<table class='extrato-table'>
                            <tr class='extrato-row'><td class='extrato-cell-label'>(+) REPASSE ENTRADO NO ANO</td><td class='extrato-cell-val' style='color:#059669;'>{fmt(sum_rep_mãe)}</td></tr>
                            <tr class='extrato-row'><td class='extrato-cell-label'>(+) RENDIMENTOS DE APLICAÇÃO DO ANO</td><td class='extrato-cell-val' style='color:#2563eb;'>{fmt(sum_ren_mãe)}</td></tr>
                            <tr class='extrato-row'><td>(-) DESPESAS LIQUIDADAS NO ANO (TODAS AS SECRETARIAS)</td><td class='extrato-cell-val' style='color:#dc2626;'>{fmt(sum_gas_mãe)}</td></tr>
                            <tr class='extrato-row-final' style='background-color:#ecf2ff;'><td class='extrato-cell-label'>(=) SALDO REAL ACUMULADO DISPONÍVEL (COM ANOS ANTERIORES)</td><td class='extrato-cell-val' style='color:{"#059669" if saldo_exclusivo_fonte >= 0 else "#dc2626"}; font-size:14px;'>{fmt(saldo_exclusivo_fonte)}</td></tr>
                        </table>''', unsafe_allow_html=True)

                    # 🏢 DIVISÃO DETALHADA POR SECRETARIA (Sincronizada por Ano com acúmulo de saldos passados!)
                    st.markdown(f"<div class='section-title'>🏢 Divisão de Recursos por Secretaria — Ano Filtrado: {ano_selecionado}</div>", unsafe_allow_html=True)
                    for sec in secretarias:
                        # Isolamento de Fluxo do Ano para a secretaria
                        df_sec_fluxo = df_fonte_fluxo[df_fonte_fluxo['secretaria'] == sec]
                        sec_rep_ano = float(df_sec_fluxo['repasse'].sum())
                        sec_ren_ano = float(df_sec_fluxo['rendimento'].sum())
                        sec_gas_ano = float(df_sec_fluxo['bruto'].sum())
                        
                        # Isolamento do histórico acumulado para a secretaria (Soma com os anos passados)
                        df_sec_saldo = df_fonte_saldo[df_fonte_saldo['secretaria'] == sec]
                        sec_saldo_acumulado = float(df_sec_saldo['repasse'].sum() + df_sec_saldo['rendimento'].sum()) - float(df_sec_saldo['bruto'].sum())
                        
                        st.markdown(f"<div class='secretaria-header'>🏛️ {sec.upper()}</div>", unsafe_allow_html=True)
                        st.markdown(f'''<table class='extrato-table'>
                            <tr class='extrato-row'><td class='extrato-cell-label'>(+) REPASSE DESTINADO NO ANO PARA {sec.upper()}</td><td class='extrato-cell-val' style='color:#059669;'>{fmt(sec_rep_ano)}</td></tr>
                            <tr class='extrato-row'><td class='extrato-cell-label'>(+) RENDIMENTOS DA CONTA NO ANO PARA {sec.upper()}</td><td class='extrato-cell-val' style='color:#2563eb;'>{fmt(sec_ren_ano)}</td></tr>
                            <tr class='extrato-row'><td class='extrato-cell-label'>(-) DESPESAS LIQUIDADAS NO ANO POR {sec.upper()} (NF BRUTA)</td><td class='extrato-cell-val' style='color:#dc2626;'>{fmt(sec_gas_ano)}</td></tr>
                            <tr class='extrato-row-final'><td class='extrato-cell-label'>(=) SALDO REAL LIVRE ATUAL — {sec.upper()} (COM SALDO ANTERIOR)</td><td class='extrato-cell-val' style='color:#059669;'>{fmt(sec_saldo_acumulado)}</td></tr>
                        </table>''', unsafe_allow_html=True)

                    # ⚖️ CONCILIAÇÃO BANCÁRIA (Sincronizada automaticamente pelo mesmo seletor)
                    if conta_vinculada != "Não Informada" and not df_banco_saldo.empty:
                        st.markdown(f"<div class='section-title' style='color:#2563eb; border-bottom:3px solid #2563eb;'>⚖️ ABERTURA DE SALDOS — CONTA CORRENTE: {conta_vinculada}</div>", unsafe_allow_html=True)
                        
                        fontes_compartilhadas = sorted([fc for fc in df_banco_saldo['fonte_clean'].unique() if fc != ''])
                        linhas_banco = []
                        tot_rep_banco, tot_ren_banco, tot_gas_banco, tot_saldo_banco = 0.0, 0.0, 0.0, 0.0
                        
                        for f_item in fontes_compartilhadas:
                            # Fluxo do ano para o banco
                            df_i_fluxo = df_banco_fluxo[df_banco_fluxo['fonte_clean'] == f_item] if not df_banco_fluxo.empty else pd.DataFrame()
                            f_rep = float(df_i_fluxo['repasse'].sum()) if not df_i_fluxo.empty else 0.0
                            f_ren = float(df_i_fluxo['rendimento'].sum()) if not df_i_fluxo.empty else 0.0
                            f_des = float(df_i_fluxo['bruto'].sum()) if not df_i_fluxo.empty else 0.0
                            
                            # Histórico de saldos para o banco
                            df_i_saldo = df_banco_saldo[df_banco_saldo['fonte_clean'] == f_item]
                            f_sal_real = float(df_i_saldo['repasse'].sum() + df_i_saldo['rendimento'].sum()) - float(df_i_saldo['bruto'].sum())
                            
                            tot_rep_banco += f_rep
                            tot_ren_banco += f_ren
                            tot_gas_banco += f_des
                            tot_saldo_banco += f_sal_real
                            
                            linhas_banco.append({
                                'Fonte Orçamentária': f_item.upper() + (" (Ativa)" if f_item == fonte_sel else ""),
                                'Repasses no Ano': f_rep,
                                'Rendimentos no Ano': f_ren,
                                'Despesas no Ano': f_des,
                                'Saldo Real em Conta (Acumulado)': f_sal_real
                            })
                        
                        linhas_banco.append({
                            'Fonte Orçamentária': 'TOTAL CONSOLIDADO DA CONTA 🏦',
                            'Repasses no Ano': tot_rep_banco,
                            'Rendimentos no Ano': tot_ren_banco,
                            'Despesas no Ano': tot_gas_banco,
                            'Saldo Real em Conta (Acumulado)': tot_saldo_banco
                        })
                            
                        df_tab_banco = pd.DataFrame(linhas_banco)
                        
                        def _style_linhas(row):
                            txt_fonte = str(row['Fonte Orçamentária']).strip().upper()
                            if 'TOTAL CONSOLIDADO' in txt_fonte:
                                return ['background-color: #f1f5f9; font-weight: 800; border-top: 2px solid #000000;' for _ in row]
                            elif '(ATIVA)' in txt_fonte:
                                return ['background-color: #e0f2fe; font-weight: 700;' if '(ATIVA)' in txt_fonte else '' for _ in row]
                            return ['' for _ in row]
                            
                        df_estilizado = df_tab_banco.style.apply(_style_linhas, axis=1).format({
                            'Repasses no Ano': fmt, 'Rendimentos no Ano': fmt, 'Despesas no Ano': fmt, 'Saldo Real em Conta (Acumulado)': fmt
                        })
                        st.dataframe(df_estilizado, use_container_width=True, hide_index=True)

                    # Listagem de lançamentos (Filtrada pelo escopo do ano)
                    st.markdown("<div class='section-title'>📋 Detalhamento dos Lançamentos do Período</div>", unsafe_allow_html=True)
                    df_validos = df_fonte_fluxo[df_fonte_fluxo['EMPENHO_COL'] != '-']
                    if not df_validos.empty:
                        df_render = pd.DataFrame({
                            'DATA': df_validos['DATA_LANCAMENTO'],
                            'EMPENHO': df_validos['EMPENHO_COL'],
                            'NOTA': df_validos['NOTA_COL'],
                            'VALOR BRUTO': df_validos['bruto'].apply(fmt),
                            'PDF': df_validos['PDF_GERAL']
                        })
                        st.dataframe(df_render, use_container_width=True, hide_index=True)
                    else:
                        st.info("ℹ️ Nenhum empenho ou lançamento registrado especificamente neste ano.")

        with tab_geral:
            st.markdown("<div class='section-title' style='color:#1e3a8a; border-bottom:3px solid #1e3a8a;'>🌐 Balanço Consolidado de Recursos</div>", unsafe_allow_html=True)
            g_rep, g_ren, g_gas = float(df['repasse'].sum()), float(df['rendimento'].sum()), float(df['bruto'].sum())
            
            col_l1, col_l2 = st.columns(2)
            col_l1.markdown(f'''<div class='metric-container' style='background-color:#f8fafc; border-color:#2563eb; border-left:6px solid #2563eb;'><div>💰 Total Entradas Recebidas (Histórico)</div><div style="font-size:22px; font-weight:800; color:#059669;">{fmt(g_rep + g_ren)}</div></div>''', unsafe_allow_html=True)
            col_l2.markdown(f'''<div class='metric-container' style='border-color:#dc2626; border-left: 6px solid #dc2626;'><div>💸 Total Saídas Liquidadas (Histórico)</div><div style="font-size:22px; font-weight:800; color:#dc2626;">{fmt(g_gas)}</div></div>''', unsafe_allow_html=True)

            df_cronologico = df.groupby('ano_mov').agg({'repasse':'sum', 'rendimento':'sum', 'bruto':'sum'}).reset_index().sort_values('ano_mov')
            df_cronologico['Saldo_Acumulado'] = ((df_cronologico['repasse'] + df_cronologico['rendimento']) - df_cronologico['bruto']).cumsum()
            
            fig = go.Figure(go.Scatter(x=df_cronologico['ano_mov'], y=df_cronologico['Saldo_Acumulado'], mode='lines+markers+text', line=dict(color='#059669', width=4), text=[fmt(v) for v in df_cronologico['Saldo_Acumulado']], textposition="top center"))
            fig.update_layout(plot_bgcolor='#ffffff', paper_bgcolor='#ffffff', height=240, margin=dict(l=5,r=5,t=30,b=5), xaxis=dict(type='category'), yaxis=dict(showgrid=True, gridcolor='#e2e8f0'))
            st.plotly_chart(fig, use_container_width=True)

        with tab_deputados:
            st.markdown("<div class='section-title'>📊 Repasses por Parlamentar</div>", unsafe_allow_html=True)
            df_dep = df.groupby(['deputado', 'fonte_clean']).agg({'repasse': 'sum', 'bruto': 'sum', 'desc_clean': 'first'}).reset_index()
            df_dep = df_dep[df_dep['deputado'] != 'Não Informado']
            df_dep['Saldo'] = df_dep['repasse'] - df_dep['bruto']
            
            df_dep['repasse'] = df_dep['repasse'].apply(fmt)
            df_dep['bruto'] = df_dep['bruto'].apply(fmt)
            df_dep['Saldo'] = df_dep['Saldo'].apply(fmt)
            df_dep.columns = ['Parlamentar / Deputado', 'Fonte', '(+) Repasses', '(-) Gastos', '(=) Saldo Livre', 'Descrição']
            st.dataframe(df_dep, use_container_width=True, hide_index=True)

        with tab_secretarias:
            st.markdown("<div class='section-title'>🏛️ Recursos Direcionados por Secretaria</div>", unsafe_allow_html=True)
            df_sec = df.groupby(['secretaria', 'fonte_clean']).agg({'repasse': 'sum', 'bruto': 'sum'}).reset_index()
            df_sec = df_sec[df_sec['secretaria'] != 'Não Especificada']
            df_sec['Saldo'] = df_sec['repasse'] - df_sec['bruto']
            
            df_sec['repasse'] = df_sec['repasse'].apply(fmt)
            df_sec['bruto'] = df_sec['bruto'].apply(fmt)
            df_sec['Saldo'] = df_sec['Saldo'].apply(fmt)
            df_sec.columns = ['Secretaria / Pasta', 'Fonte Orçamentária', '(+) Repasses', '(-) Gastos', '(=) Saldo Real']
            st.dataframe(df_sec, use_container_width=True, hide_index=True)
            
except Exception as e:
    st.error(f"Erro no processamento completo: {e}")
