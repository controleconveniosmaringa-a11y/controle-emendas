import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
import os
import urllib.request

# 1. CONFIGURAÇÃO ESTRUTURAL DE NÍVEL DE KERNEL (Deve ser o primeiro comando)
st.set_page_config(page_title="Controle de Emendas", page_icon="📊", layout="wide")

# Interface Visual Enxuta via CSS de Alta Performance
st.markdown('''<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght=400;500;600;700;800&display=swap');
    html, body, [class*="css"], [data-testid="stAppViewContainer"] { font-family: 'Inter', sans-serif; background-color: #ffffff !important; color: #000000 !important; }
    [data-testid="stSidebar"], [data-testid="stSidebarUserContent"] { display: none !important; }
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

def obter_base_dados_global():
    url_dados_efetivos = "https://raw.githubusercontent.com/controleconveniosmaringa-a11y/controle-emendas/main/dados.csv"
    
    try:
        df_raw = pd.read_csv(url_dados_efetivos, low_memory=False, dtype=str, keep_default_na=False, na_filter=False)
    except Exception:
        if os.path.exists("dados.csv"):
            df_raw = pd.read_csv("dados.csv", low_memory=False, dtype=str, keep_default_na=False, na_filter=False)
        else:
            return pd.DataFrame()
            
    df = pd.DataFrame()
    colunas_originais = {re.sub(r'[^\w\s]', '', str(c).strip().lower()).replace('â', 'a').replace('ç', 'c').replace('ã', 'a').replace('ó', 'o'): c for c in df_raw.columns}
    
    def extrair_lista_limpa(nome_chave):
        col_real = next((orig for limpa, orig in colunas_originais.items() if nome_chave in limpa), None)
        if col_real is not None:
            return [str(item).strip() if (str(item).strip() != '' and str(item).strip().lower() != 'nan') else '' for item in df_raw[col_real]]
        return [''] * len(df_raw)

    fontes_brutas = extrair_lista_limpa('fonte')
    df['fonte_clean'] = [str(f).split('.')[0].lower().replace('-', '') for f in fontes_brutas]
    df['emenda_clean'] = [str(e).split('.')[0] for e in extrair_lista_limpa('emenda')]
    df['plano_clean'] = [str(p).split('.')[0] for p in extrair_lista_limpa('plano')]
    
    df['EMPENHO_COL'] = [x if x != '' else '-' for x in extrair_lista_limpa('empenho')]
    df['NOTA_COL'] = [x if x != '' else '-' for x in extrair_lista_limpa('nota')]
    df['PDF_GERAL'] = [x if x != '' else '-' for x in extrair_lista_limpa('pdf')]
    
    url_items = [''] * len(df_raw)
    for chave_tentativa in ['urllink', 'url', 'link', 'comprovante']:
        col_achada = next((orig for limpa, orig in colunas_originais.items() if chave_tentativa in limpa), None)
        if col_achada is not None:
            url_items = [str(item).strip() if (str(item).strip() != '' and str(item).strip().lower() != 'nan') else '' for item in df_raw[col_achada]]
            break
    df['URL_REAL_LINK'] = [x if x != '' else '-' for x in url_items]
    
    df['secretaria'] = [x if x != '' else 'Não Especificada' for x in extrair_lista_limpa('secretaria')]
    df['deputado'] = [x if x != '' else 'Não Informado' for x in extrair_lista_limpa('deputado')]
    df['desc_clean'] = [x if x != '' else 'Sem descrição informada' for x in extrair_lista_limpa('descricao')]
    df['conta corrente'] = [x if x != '' else 'Não Informada' for x in extrair_lista_limpa('conta')]

    datas_brutas = extrair_lista_limpa('data')
    df['DATA_LANCAMENTO'] = datas_brutas
    
    anos = []
    for d in datas_brutas:
        match = re.search(r'(20\d{2})', str(d))
        anos.append(match.group(1) if match else '2025')
    df['ano_mov'] = anos

    for col_num in ['repasse', 'rendimento', 'bruto']:
        valores_limpos = []
        for v in extrair_lista_limpa(col_num):
            txt = str(v).replace('R$', '').strip()
            if not txt or txt == '-':
                valores_limpos.append(0.0)
                continue
            if ',' in txt and '.' in txt:
                txt = txt.replace('.', '').replace(',', '.')
            elif ',' in txt:
                txt = txt.replace(',', '.')
            try:
                valores_limpos.append(float(txt))
            except ValueError:
                valores_limpos.append(0.0)
        df[col_num] = valores_limpos
        
    return df

try:
    df = obter_base_dados_global()
    
    if not df.empty:
        def fmt(v):
            return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        fontes = sorted([f for f in df['fonte_clean'].unique() if f not in ['', 'nan']])
        anos_disponiveis = sorted(list(set([str(a) for a in df['ano_mov'].unique() if a not in ['', 'nan']])))

        st.markdown("<div class='main-title'>Controle de Emendas</div>", unsafe_allow_html=True)
        
        c_filtro1, c_filtro2 = st.columns(2)
        with c_filtro1:
            fonte_sel = st.selectbox("🎯 Selecione a Fonte Orçamentária:", options=fontes, index=0)
        with c_filtro2:
            ano_selecionado = st.selectbox("📅 Selecione o Exercício Fiscal:", ["Exibir Histórico Acumulado Completo"] + anos_disponiveis, key="filtro_ano_central_global")
        
        tab_ativa, tab_geral, tab_deputados, tab_secretarias, tab_planos = st.tabs([
            f"🎯 Fonte Ativa: {fonte_sel}", "🌐 Panorama Geral", "🔍 Por Deputado", "🏛️ Por Secretaria", "📋 Por Plano de Ação"
        ])
        
        # [Aba 1 a 4 permanecem inalteradas mantendo o backup funcional]
        with tab_ativa:
            if fonte_sel:
                df_final = df[df['fonte_clean'] == fonte_sel]
                if not df_final.empty:
                    dep_vinculo = df_final['deputado'].unique()[0]
                    eme_vinculo = df_final['emenda_clean'].unique()[0]
                    pln_vinculo = df_final['plano_clean'].unique()[0]
                    conta_vinculada = df_final['conta corrente'].iloc[0]
                    
                    if ano_selecionado == "Exibir Histórico Acumulado Completo":
                        df_fonte_fluxo = df_final
                        df_fonte_saldo = df_final
                        df_conta_total_banco = df[df['conta corrente'] == conta_vinculada] if conta_vinculada != "Não Informada" else pd.DataFrame()
                        df_banco_fluxo = df_conta_total_banco
                        df_banco_saldo = df_conta_total_banco
                    else:
                        df_fonte_fluxo = df_final[df_final['ano_mov'] == ano_selecionado]
                        df_fonte_saldo = df_final[df_final['ano_mov'].astype(int) <= int(ano_selecionado)]
                        df_banco_base = df[df['conta corrente'] == conta_vinculada] if conta_vinculada != "Não Informada" else pd.DataFrame()
                        df_banco_fluxo = df_banco_base[df_banco_base['ano_mov'] == ano_selecionado] if not df_banco_base.empty else pd.DataFrame()
                        df_banco_saldo = df_banco_base[df_banco_base['ano_mov'].astype(int) <= int(ano_selecionado)] if not df_banco_base.empty else pd.DataFrame()

                    saldo_exclusivo_fonte = float(df_fonte_saldo['repasse'].sum() + df_fonte_saldo['rendimento'].sum()) - float(df_fonte_saldo['bruto'].sum())
                    saldo_real_banco_total = float(df_banco_saldo['repasse'].sum() + df_banco_saldo['rendimento'].sum()) - float(df_banco_saldo['bruto'].sum()) if not df_banco_saldo.empty else saldo_exclusivo_fonte
                    lbl_ano = "Histórico Total" if ano_selecionado == "Exibir Histórico Acumulado Completo" else f"Exercício {ano_selecionado}"

                    st.markdown(f'''<div class='kpi-row-container'>
                        <div class='kpi-card-head'>
                            <div class='kpi-label'>🎯 Saldo Disponível da Fonte ({lbl_ano})</div>
                            <div class='kpi-value'>{fmt(saldo_exclusivo_fonte)}</div>
                        </div>
                        <div class='kpi-card-head-blue'>
                            <div class='kpi-label' style='color:#1e40af;'>🏦 Saldo em Conta: {conta_vinculada} ({lbl_ano})</div>
                            <div class='kpi-value' style='color:#2563eb;'>{fmt(saldo_real_banco_total)}</div>
                        </div>
                    </div>''', unsafe_allow_html=True)
                    
                    st.markdown(f'''<div style='margin-bottom:10px;'>
                        <div class='meta-tag'>👤 Deputado: {dep_vinculo}</div>
                        <div class='meta-tag'>📄 Número Emenda: {eme_vinculo}</div>
                        <div class='meta-tag'>🎯 Plano de Ação: {pln_vinculo}</div>
                    </div>''', unsafe_allow_html=True)
                    
                    secretarias = [s for s in df_final['secretaria'].unique() if s != '']
                    if len(secretarias) > 1:
                        st.markdown(f"<div class='section-title'>🌍 RESUMO CONSOLIDADO DA FONTE — ({lbl_ano})</div>", unsafe_allow_html=True)
                        st.markdown(f'''<table class='extrato-table'>
                            <tr class='extrato-row'><td class='extrato-cell-label'>(+) REPASSE ENTRADO NO PERÍODO</td><td class='extrato-cell-val' style='color:#059669;'>{fmt(float(df_fonte_fluxo['repasse'].sum()))}</td></tr>
                            <tr class='extrato-row'><td class='extrato-cell-label'>(+) RENDIMENTOS DE APLICAÇÃO DO PERÍODO</td><td class='extrato-cell-val' style='color:#2563eb;'>{fmt(float(df_fonte_fluxo['rendimento'].sum()))}</td></tr>
                            <tr class='extrato-row'><td>(-) DESPESAS LIQUIDADAS NO PERÍODO (TODAS AS SECRETARIAS)</td><td class='extrato-cell-val' style='color:#dc2626;'>{fmt(float(df_fonte_fluxo['bruto'].sum()))}</td></tr>
                            <tr class='extrato-row-final' style='background-color:#ecf2ff;'><td class='extrato-cell-label'>(=) SALDO REAL ACUMULADO DISPONÍVEL NA EMENDA</td><td class='extrato-cell-val' style='color:{"#059669" if saldo_exclusivo_fonte >= 0 else "#dc2626"}; font-size:14px;'>{fmt(saldo_exclusivo_fonte)}</td></tr>
                        </table>''', unsafe_allow_html=True)

                    st.markdown(f"<div class='section-title'>🏢 Divisão de Recursos por Secretaria — ({lbl_ano})</div>", unsafe_allow_html=True)
                    for sec in secretarias:
                        df_sec_fluxo = df_fonte_fluxo[df_fonte_fluxo['secretaria'] == sec]
                        df_sec_saldo = df_fonte_saldo[df_fonte_saldo['secretaria'] == sec]
                        st.markdown(f"<div class='secretaria-header'>🏛️ {sec.upper()}</div>", unsafe_allow_html=True)
                        st.markdown(f'''<table class='extrato-table'>
                            <tr class='extrato-row'><td class='extrato-cell-label'>(+) REPASSE DESTINADO NO PERÍODO</td><td class='extrato-cell-val' style='color:#059669;'>{fmt(float(df_sec_fluxo['repasse'].sum()))}</td></tr>
                            <tr class='extrato-row'><td class='extrato-cell-label'>(+) RENDIMENTOS DA CONTA NO PERÍODO</td><td class='extrato-cell-val' style='color:#2563eb;'>{fmt(float(df_sec_fluxo['rendimento'].sum()))}</td></tr>
                            <tr class='extrato-row'><td class='extrato-cell-label'>(-) DESPESAS LIQUIDADAS NO PERÍODO (NF BRUTA)</td><td class='extrato-cell-val' style='color:#dc2626;'>{fmt(float(df_sec_fluxo['bruto'].sum()))}</td></tr>
                            <tr class='extrato-row-final'><td class='extrato-cell-label'>(=) SALDO REAL LIVRE ATUAL (COM SALDO ANTERIOR)</td><td class='extrato-cell-val' style='color:#059669;'>{fmt(float(df_sec_saldo['repasse'].sum() + df_sec_saldo['rendimento'].sum()) - float(df_sec_saldo['bruto'].sum()))}</td></tr>
                        </table>''', unsafe_allow_html=True)

                    if conta_vinculada != "Não Informada" and not df_banco_saldo.empty:
                        st.markdown(f"<div class='section-title' style='color:#2563eb; border-bottom:3px solid #2563eb;'>⚖️ ABERTURA DE SALDOS — CONTA CORRENTE: {conta_vinculada} ({lbl_ano})</div>", unsafe_allow_html=True)
                        fontes_compartilhadas = sorted([fc for fc in df_banco_saldo['fonte_clean'].unique() if fc != ''])
                        linhas_banco = []
                        tot_rep_ano, tot_ren_ano, tot_gasto_ano, tot_saldo_acum = 0.0, 0.0, 0.0, 0.0
                        for f_item in fontes_compartilhadas:
                            df_item_ano = df_banco_fluxo[df_banco_fluxo['fonte_clean'] == f_item] if not df_banco_fluxo.empty else pd.DataFrame()
                            f_rep = float(df_item_ano['repasse'].sum()) if not df_item_ano.empty else 0.0
                            f_ren = float(df_item_ano['rendimento'].sum()) if not df_item_ano.empty else 0.0
                            f_des = float(df_item_ano['bruto'].sum()) if not df_item_ano.empty else 0.0
                            df_item_acum = df_banco_saldo[df_banco_saldo['fonte_clean'] == f_item]
                            f_sal_real = float(df_item_acum['repasse'].sum() + df_item_acum['rendimento'].sum()) - float(df_item_acum['bruto'].sum())
                            tot_rep_ano += f_rep; tot_ren_ano += f_ren; tot_gasto_ano += f_des; tot_saldo_acum += f_sal_real
                            linhas_banco.append({'Fonte Orçamentária': f_item.upper() + (" (Ativa)" if f_item == fonte_sel else ""), 'Repasses no Período': f_rep, 'Rendimentos no Período': f_ren, 'Despesas no Período': f_des, 'Saldo Real em Conta (Acumulado)': f_sal_real})
                        linhas_banco.append({'Fonte Orçamentária': 'TOTAL CONSOLIDADO DA CONTA 🏦', 'Repasses no Período': tot_rep_ano, 'Rendimentos no Período': tot_ren_ano, 'Despesas no Período': tot_gasto_ano, 'Saldo Real em Conta (Acumulado)': tot_saldo_acum})
                        df_tab_banco = pd.DataFrame(linhas_banco)
                        def _style_linhas(row):
                            txt_fonte = str(row['Fonte Orçamentária']).strip().upper()
                            if 'TOTAL CONSOLIDADO' in txt_fonte: return ['background-color: #f1f5f9; font-weight: 800; border-top: 2px solid #000000;' for _ in row]
                            elif '(ATIVA)' in txt_fonte: return ['background-color: #e0f2fe; font-weight: 700;' for _ in row]
                            return ['' for _ in row]
                        df_estilizado = df_tab_banco.style.apply(_style_linhas, axis=1).format({'Repasses no Período': fmt, 'Rendimentos no Período': fmt, 'Despesas no Período': fmt, 'Saldo Real em Conta (Acumulado)': fmt})
                        st.dataframe(df_estilizado, use_container_width=True, hide_index=True)

                    st.markdown(f"<div class='section-title' style='color: #0f172a; border-bottom: 3px solid #0f172a;'>📋 Detalhamento dos Lançamentos do Período — ({lbl_ano})</div>", unsafe_allow_html=True)
                    df_validos = df_fonte_fluxo[df_fonte_fluxo['EMPENHO_COL'] != '-']
                    if not df_validos.empty:
                        lista_links_limpos = [str(lk).strip() if str(lk).strip().startswith("http") else None for lk in df_validos['URL_REAL_LINK']]
                        df_render = pd.DataFrame({'Data Lançamento': df_validos['DATA_LANCAMENTO'], 'Nº Empenho': df_validos['EMPENHO_COL'], 'Nota Fiscal': df_validos['NOTA_COL'], 'Valor Bruto NF': df_validos['bruto'], 'Comprovante/PDF 📄': lista_links_limpos})
                        st.dataframe(df_render.style.format({'Valor Bruto NF': fmt}).set_properties(**{'font-weight': '500', 'font-size': '12px'}), use_container_width=True, hide_index=True, column_config={"Data Lançamento": st.column_config.TextColumn(alignment="center"), "Nº Empenho": st.column_config.TextColumn(alignment="center"), "Nota Fiscal": st.column_config.TextColumn(alignment="center"), "Valor Bruto NF": st.column_config.NumberColumn(alignment="right"), "Comprovante/PDF 📄": st.column_config.LinkColumn(display_text="Abrir Documento 🔗")})
                    else:
                        st.info("ℹ️ Nenhum empenho ou nota fiscal emitidos especificamente no período selecionado.")

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
            df_dep['repasse'] = df_dep['repasse'].apply(fmt); df_dep['bruto'] = df_dep['bruto'].apply(fmt); df_dep['Saldo'] = df_dep['Saldo'].apply(fmt)
            df_dep.columns = ['Parlamentar / Deputado', 'Fonte', '(+) Repasses', '(-) Gastos', '(=) Saldo Livre', 'Descrição']
            st.dataframe(df_dep, use_container_width=True, hide_index=True)

        with tab_secretarias:
            st.markdown("<div class='section-title'>🏛️ Recursos Direcionados por Secretaria</div>", unsafe_allow_html=True)
            df_sec = df.groupby(['secretaria', 'fonte_clean']).agg({'repasse': 'sum', 'bruto': 'sum'}).reset_index()
            df_sec = df_sec[df_sec['secretaria'] != 'Não Especificada']
            df_sec['Saldo'] = df_sec['repasse'] - df_sec['bruto']
            df_sec['repasse'] = df_sec['repasse'].apply(fmt); df_sec['bruto'] = df_sec['bruto'].apply(fmt); df_sec['Saldo'] = df_sec['Saldo'].apply(fmt)
            df_sec.columns = ['Secretaria / Pasta', 'Fonte Orçamentária', '(+) Repasses', '(-) Gastos', '(=) Saldo Real']
            st.dataframe(df_sec, use_container_width=True, hide_index=True)

        # 🚀 📋 [NOVA ESTRUTURA]: ABA PLANO DE AÇÃO DINÂMICA COM FILTRO DE BUSCA EXCLUSIVO
        with tab_planos:
            st.markdown("<div class='section-title'>🔍 Painel de Investigação por Plano de Ação</div>", unsafe_allow_html=True)
            
            # Captura e limpa a listagem de planos de ação disponíveis para o selectbox
            lista_planos_validos = sorted([str(p).upper() for p in df['plano_clean'].unique() if str(p).strip() not in ['', 'nan']])
            
            if lista_planos_validos:
                # Caixa de Seleção Dinâmica do Plano de Ação
                plano_selecionado_aba = st.selectbox("📋 Selecione o Plano de Ação que deseja analisar:", options=lista_planos_validos, key="selecao_plano_acao_aba_exclusivo")
                
                # Base filtrada estritamente para o plano escolhido
                df_pln_ativo = df[df['plano_clean'].str.upper() == plano_selecionado_aba]
                
                if not df_pln_ativo.empty:
                    # Coleta metadados vinculados a esse plano
                    fonte_vinculo_pln = df_pln_ativo['fonte_clean'].unique()[0].upper()
                    dep_vinculo_pln = df_pln_ativo['deputado'].unique()[0]
                    eme_vinculo_pln = df_pln_ativo['emenda_clean'].unique()[0]
                    conta_vinculo_pln = df_pln_ativo['conta corrente'].iloc[0]
                    
                    # Ajuste de tempo (Fluxo x Saldo Acumulado) específico para esta tela
                    if ano_selecionado == "Exibir Histórico Acumulado Completo":
                        df_pln_fluxo = df_pln_ativo
                        df_pln_saldo = df_pln_ativo
                    else:
                        df_pln_fluxo = df_pln_ativo[df_pln_ativo['ano_mov'] == ano_selecionado]
                        df_pln_saldo = df_pln_ativo[df_pln_ativo['ano_mov'].astype(int) <= int(ano_selecionado)]
                    
                    # Cálculo matemático de Saldo Exclusivo do Plano de Ação
                    repasse_pln = float(df_pln_saldo['repasse'].sum())
                    rendimento_pln = float(df_pln_saldo['rendimento'].sum())
                    despesa_pln = float(df_pln_saldo['bruto'].sum())
                    saldo_final_pln = (repasse_pln + rendimento_pln) - despesa_pln
                    
                    lbl_ano_pln = "Histórico Total" if ano_selecionado == "Exibir Histórico Acumulado Completo" else f"Exercício {ano_selecionado}"
                    
                    # Bloco de KPI de Alto Impacto Visual
                    st.markdown(f'''<div class='kpi-row-container'>
                        <div class='kpi-card-head' style='border-color: #059669; border-left: 6px solid #059669;'>
                            <div class='kpi-label'>📋 Saldo Disponível no Plano ({lbl_ano_pln})</div>
                            <div class='kpi-value'>{fmt(saldo_final_pln)}</div>
                        </div>
                        <div class='kpi-card-head-blue'>
                            <div class='kpi-label' style='color:#1e40af;'>🏦 Conta Corrente Vinculada</div>
                            <div class='kpi-value' style='color:#2563eb; font-size: 20px;'>{conta_vinculo_pln}</div>
                        </div>
                    </div>''', unsafe_allow_html=True)
                    
                    # Meta Tags Informativas
                    st.markdown(f'''<div style='margin-bottom:15px;'>
                        <div class='meta-tag' style='border-color:#2563eb; color:#2563eb;'>🎯 Fonte Vinculada: {fonte_vinculo_pln}</div>
                        <div class='meta-tag'>👤 Parlamentar: {dep_vinculo_pln}</div>
                        <div class='meta-tag'>📄 Nº Emenda: {eme_vinculo_pln}</div>
                    </div>''', unsafe_allow_html=True)
                    
                    # Tabela de Extrato de Movimentação do Plano
                    st.markdown(f"<div class='section-title'>🌍 Extrato Consolidado do Plano — ({lbl_ano_pln})</div>", unsafe_allow_html=True)
                    st.markdown(f'''<table class='extrato-table'>
                        <tr class='extrato-row'><td class='extrato-cell-label'>(+) COMPOSIÇÃO DE RECEITA (REPASSE)</td><td class='extrato-cell-val' style='color:#059669;'>{fmt(float(df_pln_fluxo['repasse'].sum()))}</td></tr>
                        <tr class='extrato-row'><td class='extrato-cell-label'>(+) RENDIMENTOS DE APLICAÇÃO NO PERÍODO</td><td class='extrato-cell-val' style='color:#2563eb;'>{fmt(float(df_pln_fluxo['rendimento'].sum()))}</td></tr>
                        <tr class='extrato-row'><td>(-) DESPESAS E ORDENS PAGAS NO PERÍODO</td><td class='extrato-cell-val' style='color:#dc2626;'>{fmt(float(df_pln_fluxo['bruto'].sum()))}</td></tr>
                        <tr class='extrato-row-final' style='background-color:#ecf2ff;'><td class='extrato-cell-label'>(=) SALDO DISPONÍVEL LÍQUIDO DO PLANO DE AÇÃO</td><td class='extrato-cell-val' style='color:{"#059669" if saldo_final_pln >= 0 else "#dc2626"}; font-size:14px;'>{fmt(saldo_final_pln)}</td></tr>
                    </table>''', unsafe_allow_html=True)
                    
                    # Detalhamento de Notas Fiscais e Empenhos do Plano Selecionado
                    st.markdown(f"<div class='section-title' style='color: #0f172a; border-bottom: 3px solid #0f172a;'>📋 Detalhamento dos Lançamentos do Plano — ({lbl_ano_pln})</div>", unsafe_allow_html=True)
                    df_pln_validos = df_pln_fluxo[df_pln_fluxo['EMPENHO_COL'] != '-']
                    
                    if not df_pln_validos.empty:
                        lista_links_pln = [str(lk).strip() if str(lk).strip().startswith("http") else None for lk in df_pln_validos['URL_REAL_LINK']]
                        
                        df_render_pln = pd.DataFrame({
                            'Data Lançamento': df_pln_validos['DATA_LANCAMENTO'],
                            'Nº Empenho': df_pln_validos['EMPENHO_COL'],
                            'Nota Fiscal': df_pln_validos['NOTA_COL'],
                            'Secretaria Executor': df_pln_validos['secretaria'].astype(str).str.upper(),
                            'Valor Bruto NF': df_pln_validos['bruto'], 
                            'Comprovante/PDF 📄': lista_links_pln
                        })
                        
                        st.dataframe(
                            df_render_pln.style.format({'Valor Bruto NF': fmt}).set_properties(**{'font-weight': '500', 'font-size': '12px'}), 
                            use_container_width=True, 
                            hide_index=True,
                            column_config={
                                "Data Lançamento": st.column_config.TextColumn(alignment="center"),
                                "Nº Empenho": st.column_config.TextColumn(alignment="center"),
                                "Nota Fiscal": st.column_config.TextColumn(alignment="center"),
                                "Secretaria Executor": st.column_config.TextColumn(alignment="left"),
                                "Valor Bruto NF": st.column_config.NumberColumn(alignment="right"),
                                "Comprovante/PDF 📄": st.column_config.LinkColumn(display_text="Abrir Documento 🔗")
                            }
                        )
                    else:
                        st.info("ℹ️ Nenhum empenho ou nota fiscal emitidos para este Plano de Ação no período selecionado.")
            else:
                st.info("ℹ️ Nenhum Plano de Ação identificado ou registrado na base de dados atual.")
            
except Exception as e:
    st.error(f"Erro no processamento unificado: {e}")
