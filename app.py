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
        
        with tab_ativa:
            if fonte_sel:
                df_final = df[df['fonte_clean'] == fonte_sel]
                if not df_final.empty:
                    dep_vinculo = df_final['deputado'].unique()[0]
                    eme_vinculo = df_final['emenda_clean'].unique()[0]
                    conta_vinculada = df_final['conta corrente'].iloc[0]
                    
                    if ano_selecionado == "Exibir Histórico Acumulado Completo":
                        df_fonte_fluxo = df_final; df_fonte_saldo = df_final
                        df_conta_total_banco = df[df['conta corrente'] == conta_vinculada] if conta_vinculada != "Não Informada" else pd.DataFrame()
                        df_banco_fluxo = df_conta_total_banco; df_banco_saldo = df_conta_total_banco
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
                        <div class='meta-tag'>🎯 Plano de Ação: {df_final['plano_clean'].unique()[0]}</div>
                    </div>''', unsafe_allow_html=True)
                    
                    secretarias_lista = [s for s in df_final['secretaria'].unique() if s != '']
                    if len(secretarias_lista) > 1:
                        st.markdown(f"<div class='section-title'>🌍 RESUMO CONSOLIDADO DA FONTE — ({lbl_ano})</div>", unsafe_allow_html=True)
                        st.markdown(f'''<table class='extrato-table'>
                            <tr class='extrato-row'><td class='extrato-cell-label'>(+) REPASSE ENTRADO NO PERÍODO</td><td class='extrato-cell-val' style='color:#059669;'>{fmt(float(df_fonte_fluxo['repasse'].sum()))}</td></tr>
                            <tr class='extrato-row'><td class='extrato-cell-label'>(+) RENDIMENTOS DE APLICAÇÃO DO PERÍODO</td><td class='extrato-cell-val' style='color:#2563eb;'>{fmt(float(df_fonte_fluxo['rendimento'].sum()))}</td></tr>
                            <tr class='extrato-row'><td>(-) DESPESAS LIQUIDADAS NO PERÍODO (TODAS AS SECRETARIAS)</td><td class='extrato-cell-val' style='color:#dc2626;'>{fmt(float(df_fonte_fluxo['bruto'].sum()))}</td></tr>
                            <tr class='extrato-row-final' style='background-color:#ecf2ff;'><td class='extrato-cell-label'>(=) SALDO REAL ACUMULADO DISPONÍVEL NA EMENDA</td><td class='extrato-cell-val' style='color:{"#059669" if saldo_exclusivo_fonte >= 0 else "#dc2626"}; font-size:14px;'>{fmt(saldo_exclusivo_fonte)}</td></tr>
                        </table>''', unsafe_allow_html=True)

                    st.markdown(f"<div class='section-title'>🏢 Divisão de Recursos por Secretaria — ({lbl_ano})</div>", unsafe_allow_html=True)
                    for sec in secretarias_lista:
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

        # 🛠️ 🔍 [NOVA ESTRUTURA]: ABA DEPUTADO REFORMULADA DINAMICAMENTE (PADRÃO MESTRE)
        with tab_deputados:
            st.markdown("<div class='section-title'>🔍 Painel Parlamentar: Investigação por Deputado / Autor</div>", unsafe_allow_html=True)
            
            lista_deps_validos = sorted([str(d).upper() for d in df['deputado'].unique() if str(d).strip() not in ['', 'nan', 'Não Informado']])
            
            if lista_deps_validas := lista_deps_validos:
                col_dep_txt, col_dep_sel = st.columns(2)
                
                with col_dep_txt:
                    dep_digitado_raw = st.text_input("⌨️ Digite o nome do Deputado (Prioridade):", value="", placeholder="Ex: DEPUTADO ABC", key="input_texto_deputado_mestre").strip().upper()
                
                with col_dep_sel:
                    dep_padrao_idx = 0
                    if dep_digitado_raw in lista_deps_validas:
                        dep_padrao_idx = lista_deps_validas.index(dep_digitado_raw)
                    dep_selecionado_listbox = st.selectbox("🖱️ Ou selecione o parlamentar diretamente na lista abaixo:", options=lista_deps_validas, index=dep_padrao_idx, key="selecao_deputado_lista_mestre")
                
                if dep_digitado_raw and dep_digitado_raw in lista_deps_validas:
                    deputado_final_analise = dep_digitado_raw
                else:
                    if dep_digitado_raw and dep_digitado_raw not in lista_deps_validas:
                        st.warning(f"⚠️ O parlamentar '{dep_digitado_raw}' não foi localizado. Exibindo dados do deputado selecionado na lista.")
                    deputado_final_analise = dep_selecionado_listbox
                
                df_dep_ativo = df[df['deputado'].str.upper() == deputado_final_analise]
                
                if not df_dep_ativo.empty:
                    lbl_ano_dep = "Histórico Total" if ano_selecionado == "Exibir Histórico Acumulado Completo" else f"Exercício {ano_selecionado}"
                    
                    if ano_selecionado == "Exibir Histórico Acumulado Completo":
                        df_dep_fluxo = df_dep_ativo; df_dep_saldo = df_dep_ativo
                    else:
                        df_dep_fluxo = df_dep_ativo[df_dep_ativo['ano_mov'] == ano_selecionado]
                        df_dep_saldo = df_dep_ativo[df_dep_ativo['ano_mov'].astype(int) <= int(ano_selecionado)]
                    
                    repasse_dep = float(df_dep_saldo['repasse'].sum())
                    rendimento_dep = float(df_dep_saldo['rendimento'].sum())
                    despesa_dep = float(df_dep_saldo['bruto'].sum())
                    saldo_final_dep = (repasse_dep + rendimento_dep) - despesa_dep
                    
                    emendas_enviadas_num = len(df_dep_ativo['fonte_clean'].unique())
                    
                    st.markdown(f'''<div class='kpi-row-container' style='margin-top: 15px;'>
                        <div class='kpi-card-head' style='border-color: #2563eb; border-left: 6px solid #2563eb; background-color: #f8fafc;'>
                            <div class='kpi-label'>👤 Parlamentar em Foco</div>
                            <div class='kpi-value' style='color: #0f172a;'>{deputado_final_analise}</div>
                        </div>
                        <div class='kpi-card-head' style='border-color: #059669; border-left: 6px solid #059669;'>
                            <div class='kpi-label'>💰 Saldo Disponível das Emendas ({lbl_ano_dep})</div>
                            <div class='kpi-value'>{fmt(saldo_final_dep)}</div>
                        </div>
                        <div class='kpi-card-head' style='border-color: #0f172a; border-left: 6px solid #0f172a;'>
                            <div class='kpi-label'>📄 Emendas Destinadas</div>
                            <div class='kpi-value' style='color: #0f172a;'>{emendas_enviadas_num} Fonte(s) Ativa(s)</div>
                        </div>
                    </div>''', unsafe_allow_html=True)
                    
                    st.markdown(f"<div class='section-title'>🌍 Extrato Consolidado do Deputado — ({lbl_ano_dep})</div>", unsafe_allow_html=True)
                    st.markdown(f'''<table class='extrato-table'>
                        <tr class='extrato-row'><td class='extrato-cell-label'>(+) REPASSES TOTAIS ENVIADOS PELO PARLAMENTAR</td><td class='extrato-cell-val' style='color:#059669;'>{fmt(float(df_dep_fluxo['repasse'].sum()))}</td></tr>
                        <tr class='extrato-row'><td class='extrato-cell-label'>(+) RENDIMENTOS ACUMULADOS NAS EMENDAS NO PERÍODO</td><td class='extrato-cell-val' style='color:#2563eb;'>{fmt(float(df_dep_fluxo['rendimento'].sum()))}</td></tr>
                        <tr class='extrato-row'><td>(-) DESPESAS E ORDENS PAGAS COM ESTES RECURSOS</td><td class='extrato-cell-val' style='color:#dc2626;'>{fmt(float(df_dep_fluxo['bruto'].sum()))}</td></tr>
                        <tr class='extrato-row-final' style='background-color:#ecf2ff;'><td class='extrato-cell-label'>(=) RECURSO SALDO DISPONÍVEL LÍQUIDO DO PARLAMENTAR</td><td class='extrato-cell-val' style='color:{"#059669" if saldo_final_dep >= 0 else "#dc2626"}; font-size:14px;'>{fmt(saldo_final_dep)}</td></tr>
                    </table>''', unsafe_allow_html=True)
                    
                    st.markdown(f"<div class='section-title' style='color:#2563eb; border-bottom:3px solid #2563eb;'>⚖️ Abertura de Saldos Individuais por Fonte / Emenda ({lbl_ano_dep})</div>", unsafe_allow_html=True)
                    
                    fontes_do_dep = sorted([f for f in df_dep_saldo['fonte_clean'].unique() if f != ''])
                    linhas_fontes_dep = []
                    t_rep_d, t_ren_d, t_gas_d, t_sal_d = 0.0, 0.0, 0.0, 0.0
                    
                    for f_item in fontes_do_dep:
                        df_f_item_base = df_dep_ativo[df_dep_ativo['fonte_clean'] == f_item]
                        if ano_selecionado == "Exibir Histórico Acumulado Completo":
                            df_f_fluxo = df_f_item_base; df_f_saldo = df_f_item_base
                        else:
                            df_f_fluxo = df_f_item_base[df_f_item_base['ano_mov'] == ano_selecionado]
                            df_f_saldo = df_f_item_base[df_f_item_base['ano_mov'].astype(int) <= int(ano_selecionado)]
                        
                        r_rep = float(df_f_fluxo['repasse'].sum())
                        r_ren = float(df_f_fluxo['rendimento'].sum())
                        r_gas = float(df_f_fluxo['bruto'].sum())
                        r_sal = float(df_f_saldo['repasse'].sum() + df_f_saldo['rendimento'].sum()) - float(df_f_saldo['bruto'].sum())
                        
                        t_rep_d += r_rep; t_ren_d += r_ren; t_gas_d += r_gas; t_sal_d += r_sal
                        
                        linhas_fontes_dep.append({
                            'Fonte Orçamentária / Emenda': f_item.upper(),
                            'Nº Emenda': df_f_item_base['emenda_clean'].iloc[0],
                            'Repasses no Período': r_rep,
                            'Rendimentos no Período': r_ren,
                            'Despesas no Período': r_gas,
                            'Saldo Disponível (Acumulado)': r_sal
                        })
                        
                    linhas_fontes_dep.append({
                        'Fonte Orçamentária / Emenda': 'TOTAL CONSOLIDADO DO PARLAMENTAR 👤',
                        'Nº Emenda': '-',
                        'Repasses no Período': t_rep_d,
                        'Rendimentos no Período': t_ren_d,
                        'Despesas no Período': t_gas_d,
                        'Saldo Disponível (Acumulado)': t_sal_d
                    })
                    
                    df_tab_fontes_dep = pd.DataFrame(linhas_fontes_dep)
                    def _style_linhas_dep(row):
                        if 'TOTAL CONSOLIDADO' in str(row['Fonte Orçamentária / Emenda']).upper():
                            return ['background-color: #f1f5f9; font-weight: 800; border-top: 2px solid #000000;' for _ in row]
                        return ['' for _ in row]
                        
                    st.dataframe(df_tab_fontes_dep.style.apply(_style_linhas_dep, axis=1).format({
                        'Repasses no Período': fmt, 'Rendimentos no Período': fmt, 'Despesas no Período': fmt, 'Saldo Disponível (Acumulado)': fmt
                    }), use_container_width=True, hide_index=True)
                    
                    st.markdown(f"<div class='section-title' style='color: #0f172a; border-bottom: 3px solid #0f172a;'>📋 Caderno de Lançamentos Vinculados ao Deputado — ({lbl_ano_dep})</div>", unsafe_allow_html=True)
                    df_dep_validos = df_dep_fluxo[df_dep_fluxo['EMPENHO_COL'] != '-']
                    
                    if not df_dep_validos.empty:
                        lista_links_dep = [str(lk).strip() if str(lk).strip().startswith("http") else None for lk in df_dep_validos['URL_REAL_LINK']]
                        df_render_dep = pd.DataFrame({
                            'Data Lançamento': df_dep_validos['DATA_LANCAMENTO'],
                            'Fonte Recurso': df_dep_validos['fonte_clean'].astype(str).str.upper(),
                            'Nº Empenho': df_dep_validos['EMPENHO_COL'],
                            'Nota Fiscal': df_dep_validos['NOTA_COL'],
                            'Secretaria Executor': df_dep_validos['secretaria'].astype(str).str.upper(),
                            'Plano de Ação': df_dep_validos['plano_clean'].astype(str).str.upper(),
                            'Valor Bruto NF': df_dep_validos['bruto'], 
                            'Comprovante/PDF 📄': lista_links_dep
                        })
                        st.dataframe(df_render_dep.style.format({'Valor Bruto NF': fmt}).set_properties(**{'font-weight': '500', 'font-size': '12px'}), use_container_width=True, hide_index=True, column_config={"Data Lançamento": st.column_config.TextColumn(alignment="center"), "Fonte Recurso": st.column_config.TextColumn(alignment="center"), "Nº Empenho": st.column_config.TextColumn(alignment="center"), "Nota Fiscal": st.column_config.TextColumn(alignment="center"), "Secretaria Executor": st.column_config.TextColumn(alignment="left"), "Plano de Ação": st.column_config.TextColumn(alignment="center"), "Valor Bruto NF": st.column_config.NumberColumn(alignment="right"), "Comprovante/PDF 📄": st.column_config.LinkColumn(display_text="Abrir Documento 🔗")})
                    else:
                        st.info("ℹ️ Nenhum empenho ou nota fiscal emitidos para este Deputado no período selecionado.")
            else:
                st.info("ℹ️ Nenhum Deputado identificado ou registrado na base de dados atual.")

        with tab_secretarias:
            st.markdown("<div class='section-title'>🏛️ Painel Gestor: Investigação por Secretaria / Pasta</div>", unsafe_allow_html=True)
            lista_sec_validas = sorted([str(s).upper() for s in df['secretaria'].unique() if str(s).strip() not in ['', 'nan', 'Não Especificada']])
            
            if lista_sec_validas:
                col_sec_txt, col_sec_sel = st.columns(2)
                with col_sec_txt:
                    sec_digitada_raw = st.text_input("⌨️ Digite o nome da Secretaria (Prioridade):", value="", placeholder="Ex: SEINFRA", key="input_texto_secretaria_mestre").strip().upper()
                with col_sec_sel:
                    sec_padrao_idx = 0
                    if sec_digitada_raw in lista_sec_validas: sec_padrao_idx = lista_sec_validas.index(sec_digitada_raw)
                    sec_selecionada_listbox = st.selectbox("🖱️ Ou selecione diretamente na lista clicando aqui:", options=lista_sec_validas, index=sec_padrao_idx, key="selecao_secretaria_lista_mestre")
                
                if sec_digitada_raw and sec_digitada_raw in lista_sec_validas: secretaria_final_analise = sec_digitada_raw
                else:
                    if sec_digitada_raw and sec_digitada_raw not in lista_sec_validas: st.warning(f"⚠️ A pasta '{sec_digitada_raw}' não foi localizada. Exibindo dados da secretaria selecionada na lista abaixo.")
                    secretaria_final_analise = sec_selecionada_listbox
                
                df_sec_ativa = df[df['secretaria'].str.upper() == secretaria_final_analise]
                if not df_sec_ativa.empty:
                    lbl_ano_sec = "Histórico Total" if ano_selecionado == "Exibir Histórico Acumulado Completo" else f"Exercício {ano_selecionado}"
                    if ano_selecionado == "Exibir Histórico Acumulado Completo": df_sec_fluxo = df_sec_ativa; df_sec_saldo = df_sec_ativa
                    else:
                        df_sec_fluxo = df_sec_ativa[df_sec_ativa['ano_mov'] == ano_selecionado]
                        df_sec_saldo = df_sec_ativa[df_sec_ativa['ano_mov'].astype(int) <= int(ano_selecionado)]
                    
                    repasse_sec = float(df_sec_saldo['repasse'].sum()); rendimento_sec = float(df_sec_saldo['rendimento'].sum()); despesa_sec = float(df_sec_saldo['bruto'].sum())
                    saldo_final_sec = (repasse_sec + rendimento_sec) - despesa_sec
                    fontes_gerenciadas_num = len(df_sec_ativa['fonte_clean'].unique())
                    
                    st.markdown(f'''<div class='kpi-row-container' style='margin-top: 15px;'>
                        <div class='kpi-card-head' style='border-color: #2563eb; border-left: 6px solid #2563eb; background-color: #f8fafc;'>
                            <div class='kpi-label'>🏛️ Secretaria em Foco</div>
                            <div class='kpi-value' style='color: #0f172a;'>{secretaria_final_analise}</div>
                        </div>
                        <div class='kpi-card-head' style='border-color: #059669; border-left: 6px solid #059669;'>
                            <div class='kpi-label'>💰 Saldo Livre Acumulado da Pasta ({lbl_ano_sec})</div>
                            <div class='kpi-value'>{fmt(saldo_final_sec)}</div>
                        </div>
                        <div class='kpi-card-head' style='border-color: #0f172a; border-left: 6px solid #0f172a;'>
                            <div class='kpi-label'>📊 Fontes de Recursos Ativas</div>
                            <div class='kpi-value' style='color: #0f172a;'>{fontes_gerenciadas_num} Emenda(s)</div>
                        </div>
                    </div>''', unsafe_allow_html=True)
                    
                    st.markdown(f"<div class='section-title'>🌍 Extrato Consolidado da Pasta — ({lbl_ano_sec})</div>", unsafe_allow_html=True)
                    st.markdown(f'''<table class='extrato-table'>
                        <tr class='extrato-row'><td class='extrato-cell-label'>(+) REPASSES TOTAIS DESTINADOS À PASTA</td><td class='extrato-cell-val' style='color:#059669;'>{fmt(float(df_sec_fluxo['repasse'].sum()))}</td></tr>
                        <tr class='extrato-row'><td class='extrato-cell-label'>(+) RENDIMENTOS DE ACONTA DA PASTA NO PERÍODO</td><td class='extrato-cell-val' style='color:#2563eb;'>{fmt(float(df_sec_fluxo['rendimento'].sum()))}</td></tr>
                        <tr class='extrato-row'><td>(-) DESPESAS LIQUIDADAS NO PERÍODO (NF BRUTA)</td><td class='extrato-cell-val' style='color:#dc2626;'>{fmt(float(df_sec_fluxo['bruto'].sum()))}</td></tr>
                        <tr class='extrato-row-final' style='background-color:#ecf2ff;'><td class='extrato-cell-label'>(=) RECURSO REAL LIVRE DISPONÍVEL NA SECRETARIA</td><td class='extrato-cell-val' style='color:{"#059669" if saldo_final_sec >= 0 else "#dc2626"}; font-size:14px;'>{fmt(saldo_final_sec)}</td></tr>
                    </table>''', unsafe_allow_html=True)
                    
                    st.markdown(f"<div class='section-title' style='color:#2563eb; border-bottom:3px solid #2563eb;'>⚖️ Distribuição do Caixa por Fonte Orçamentária / Emenda ({lbl_ano_sec})</div>", unsafe_allow_html=True)
                    fontes_vinculadas_sec = sorted([f for f in df_sec_saldo['fonte_clean'].unique() if f != ''])
                    linhas_fontes_sec = []
                    tot_rep_s, tot_ren_s, tot_gas_s, tot_sal_s = 0.0, 0.0, 0.0, 0.0
                    for f_item in fontes_vinculadas_sec:
                        df_f_item_base = df_sec_ativa[df_sec_ativa['fonte_clean'] == f_item]
                        if ano_selecionado == "Exibir Histórico Acumulado Completo": df_f_fluxo = df_f_item_base; df_f_saldo = df_f_item_base
                        else: df_f_fluxo = df_f_item_base[df_f_item_base['ano_mov'] == ano_selecionado]; df_f_saldo = df_f_item_base[df_f_item_base['ano_mov'].astype(int) <= int(ano_selecionado)]
                        r_rep = float(df_f_fluxo['repasse'].sum()); r_ren = float(df_f_fluxo['rendimento'].sum()); r_gas = float(df_f_fluxo['bruto'].sum())
                        r_sal = float(df_f_saldo['repasse'].sum() + df_f_saldo['rendimento'].sum()) - float(df_f_saldo['bruto'].sum())
                        tot_rep_s += r_rep; tot_ren_s += r_ren; tot_gas_s += r_gas; tot_sal_s += r_sal
                        linhas_fontes_sec.append({'Fonte Orçamentária': f_item.upper(), 'Repasses no Período': r_rep, 'Rendimentos no Período': r_ren, 'Despesas no Período': r_gas, 'Saldo Disponível (Acumulado)': r_sal})
                    linhas_fontes_sec.append({'Fonte Orçamentária': 'TOTAL CONSOLIDADO DA SECRETARIA 🏛️', 'Repasses no Período': tot_rep_s, 'Rendimentos no Período': tot_ren_s, 'Despesas no Período': tot_gas_s, 'Saldo Disponível (Acumulado)': tot_sal_s})
                    df_tab_fontes_sec = pd.DataFrame(linhas_fontes_sec)
                    def _style_linhas_sec(row): return ['background-color: #f1f5f9; font-weight: 800; border-top: 2px solid #000000;' if 'TOTAL CONSOLIDADO' in str(row['Fonte Orçamentária']).upper() else '' for _ in row]
                    st.dataframe(df_tab_fontes_sec.style.apply(_style_linhas_sec, axis=1).format({'Repasses no Período': fmt, 'Rendimentos no Período': fmt, 'Despesas no Período': fmt, 'Saldo Disponível (Acumulado)': fmt}), use_container_width=True, hide_index=True)
                    
                    st.markdown(f"<div class='section-title' style='color: #0f172a; border-bottom: 3px solid #0f172a;'>📋 Caderno de Lançamentos da Pasta — ({lbl_ano_sec})</div>", unsafe_allow_html=True)
                    df_sec_validos = df_sec_fluxo[df_sec_fluxo['EMPENHO_COL'] != '-']
                    if not df_sec_validos.empty:
                        lista_links_sec = [str(lk).strip() if str(lk).strip().startswith("http") else None for lk in df_sec_validos['URL_REAL_LINK']]
                        df_render_sec = pd.DataFrame({'Data Lançamento': df_sec_validos['DATA_LANCAMENTO'], 'Fonte Recurso': df_sec_validos['fonte_clean'].astype(str).str.upper(), 'Nº Empenho': df_sec_validos['EMPENHO_COL'], 'Nota Fiscal': df_sec_validos['NOTA_COL'], 'Plano de Ação': df_sec_validos['plano_clean'].astype(str).str.upper(), 'Valor Bruto NF': df_sec_validos['bruto'], 'Comprovante/PDF 📄': lista_links_sec})
                        st.dataframe(df_render_sec.style.format({'Valor Bruto NF': fmt}).set_properties(**{'font-weight': '500', 'font-size': '12px'}), use_container_width=True, hide_index=True, column_config={"Data Lançamento": st.column_config.TextColumn(alignment="center"), "Fonte Recurso": st.column_config.TextColumn(alignment="center"), "Nº Empenho": st.column_config.TextColumn(alignment="center"), "Nota Fiscal": st.column_config.TextColumn(alignment="center"), "Plano de Ação": st.column_config.TextColumn(alignment="center"), "Valor Bruto NF": st.column_config.NumberColumn(alignment="right"), "Comprovante/PDF 📄": st.column_config.LinkColumn(display_text="Abrir Documento 🔗")})
                    else: st.info("ℹ️ Nenhum empenho ou nota fiscal emitidos para esta Secretaria no período selecionado.")
            else: st.info("ℹ️ Nenhuma Secretaria identificada ou registrada na base de dados atual.")

        with tab_planos:
            st.markdown("<div class='section-title'> 📋 Painel Híbrido: Pesquisa e Seleção de Plano de Ação</div>", unsafe_allow_html=True)
            lista_planos_validos = sorted([str(p).upper() for p in df['plano_clean'].unique() if str(p).strip() not in ['', 'nan']])
            
            if lista_planos_validos:
                col_busca_txt, col_busca_sel = st.columns(2)
                with col_busca_txt:
                    plano_digitado_raw = st.text_input("⌨️ Escreva o número do Plano de Ação (Apenas números, sem traços):", value="", placeholder="Ex: 1264", key="input_texto_plano_acao").strip()
                    plano_digitado_numerico = re.sub(r'\D', '', plano_digitado_raw)
                
                plano_encontrado_por_digito = None
                if plano_digitado_numerico:
                    for pln_real in lista_planos_validos:
                        if re.sub(r'\D', '', pln_real) == plano_digitado_numerico:
                            plano_encontrado_por_digito = pln_real
                            break
                
                with col_busca_sel:
                    plano_padrao_idx = 0
                    if plano_encontrado_por_digito in lista_planos_validos: plano_padrao_idx = lista_planos_validos.index(plano_encontrado_por_digito)
                    plano_selecionado_listbox = st.selectbox("🖱️ Ou escolha clicando aqui na lista:", options=lista_planos_validos, index=plano_padrao_idx, key="selecao_plano_lista_hibrida")
                
                if plano_encontrado_por_digito: plano_final_analise = plano_encontrado_por_digito
                else:
                    if plano_digitado_raw and not plano_encontrado_por_digito: st.warning(f"⚠️ O plano contendo apenas os números '{plano_digitado_numerico}' não foi localizado. Usando a lista suspensa abaixo.")
                    plano_final_analise = plano_selecionado_listbox
                
                df_pln_ativo = df[df['plano_clean'].str.upper() == plano_final_analise]
                if not df_pln_ativo.empty:
                    fonte_maee = df_pln_ativo['fonte_clean'].iloc[0].lower().strip(); df_fonte_maee_completa = df[df['fonte_clean'] == fonte_maee]
                    dep_vinculo_pln = df_pln_ativo['deputado'].unique()[0]; eme_vinculo_pln = df_pln_ativo['emenda_clean'].unique()[0]; conta_vinculo_pln = df_pln_ativo['conta corrente'].iloc[0]
                    lbl_ano_pln = "Histórico Total" if ano_selecionado == "Exibir Histórico Acumulado Completo" else f"Exercício {ano_selecionado}"
                    
                    if ano_selecionado == "Exibir Histórico Acumulado Completo": df_despesas_fluxo = df_pln_ativo; df_despesas_saldo = df_pln_ativo; df_receitas_fluxo = df_fonte_maee_completa; df_receitas_saldo = df_fonte_maee_completa
                    else:
                        df_despesas_fluxo = df_pln_ativo[df_pln_ativo['ano_mov'] == ano_selecionado]; df_despesas_saldo = df_pln_ativo[df_pln_ativo['ano_mov'].astype(int) <= int(ano_selecionado)]
                        df_receitas_fluxo = df_fonte_maee_completa[df_fonte_maee_completa['ano_mov'] == ano_selecionado]
                        df_receitas_saldo = df_fonte_maee_completa[df_fonte_maee_completa['fonte_clean'] == fonte_maee]; df_receitas_saldo = df_receitas_saldo[df_receitas_saldo['ano_mov'].astype(int) <= int(ano_selecionado)]
                    
                    repasse_pln = float(df_receitas_saldo['repasse'].sum()); rendimento_pln = float(df_receitas_saldo['rendimento'].sum()); despesa_pln = float(df_despesas_saldo['bruto'].sum())
                    saldo_final_pln = (repasse_pln + rendimento_pln) - despesa_pln
                    
                    st.markdown(f'''<div class='kpi-row-container' style='margin-top: 15px;'>
                        <div class='kpi-card-head' style='border-color: #2563eb; border-left: 6px solid #2563eb; background-color: #f8fafc;'>
                            <div class='kpi-label'>📋 Plano Ativo em Análise</div>
                            <div class='kpi-value' style='color: #0f172a;'>{plano_final_analise}</div>
                        </div>
                        <div class='kpi-card-head' style='border-color: #059669; border-left: 6px solid #059669;'>
                            <div class='kpi-label'>💰 Saldo Disponível no Plano ({lbl_ano_pln})</div>
                            <div class='kpi-value'>{fmt(saldo_final_pln)}</div>
                        </div>
                        <div class='kpi-card-head-blue'>
                            <div class='kpi-label' style='color:#1e40af;'>🏦 Conta Corrente Vinculada</div>
                            <div class='kpi-value' style='color:#2563eb; font-size: 20px;'>{conta_vinculo_pln}</div>
                        </div>
                    </div>''', unsafe_allow_html=True)
                    
                    st.markdown(f'''<div style='margin-bottom:15px;'>
                        <div class='meta-tag' style='border-color:#2563eb; color:#2563eb;'>🎯 Fonte Vinculada: {fonte_maee.upper()}</div>
                        <div class='meta-tag'>👤 Parlamentar: {dep_vinculo_pln}</div>
                        <div class='meta-tag'>📄 Nº Emenda: {eme_vinculo_pln}</div>
                    </div>''', unsafe_allow_html=True)
                    
                    st.markdown(f"<div class='section-title'>🌍 Extrato Consolidado do Plano — ({lbl_ano_pln})</div>", unsafe_allow_html=True)
                    st.markdown(f'''<table class='extrato-table'>
                        <tr class='extrato-row'><td class='extrato-cell-label'>(+) COMPOSIÇÃO DE RECEITA (REPASSE INTEGRAL DA FONTE)</td><td class='extrato-cell-val' style='color:#059669;'>{fmt(float(df_receitas_fluxo['repasse'].sum()))}</td></tr>
                        <tr class='extrato-row'><td class='extrato-cell-label'>(+) RENDIMENTOS DE APLICAÇÃO DA FONTE NO PERÍODO</td><td class='extrato-cell-val' style='color:#2563eb;'>{fmt(float(df_receitas_fluxo['rendimento'].sum()))}</td></tr>
                        <tr class='extrato-row'><td>(-) DESPESAS LIQUIDADAS EXCLUSIVAS DESTE PLANO DE AÇÃO</td><td class='extrato-cell-val' style='color:#dc2626;'>{fmt(float(df_despesas_fluxo['bruto'].sum()))}</td></tr>
                        <tr class='extrato-row-final' style='background-color:#ecf2ff;'><td class='extrato-cell-label'>(=) SALDO DISPONÍVEL LÍQUIDO DO PLANO DE AÇÃO</td><td class='extrato-cell-val' style='color:{"#059669" if saldo_final_pln >= 0 else "#dc2626"}; font-size:14px;'>{fmt(saldo_final_pln)}</td></tr>
                    </table>''', unsafe_allow_html=True)
                    
                    if conta_vinculo_pln != "Não Informada":
                        st.markdown(f"<div class='section-title' style='color:#2563eb; border-bottom:3px solid #2563eb;'>⚖️ ABERTURA DE SALDOS DA CONTA BANCÁRIA POR PLANO DE AÇÃO ({lbl_ano_pln})</div>", unsafe_allow_html=True)
                        df_banco_geral_pln = df[df['conta corrente'] == conta_vinculo_pln]
                        planos_compartilhados = sorted([str(p).upper() for p in df_banco_geral_pln['plano_clean'].unique() if str(p).strip() not in ['', 'nan']])
                        linhas_banco_pln = []
                        t_rep, t_ren, t_gasto, t_saldo = 0.0, 0.0, 0.0, 0.0
                        for p_item in planos_compartilhados:
                            df_p_ativo = df_banco_geral_pln[df_banco_geral_pln['plano_clean'].str.upper() == p_item]
                            if ano_selecionado == "Exibir Histórico Acumulado Completo": df_p_fluxo = df_p_ativo; df_p_saldo = df_p_ativo; f_maee_item = df_p_ativo['fonte_clean'].iloc[0].lower().strip(); df_f_maee_item = df[df['fonte_clean'] == f_maee_item]; df_f_saldo = df_f_maee_item; df_f_fluxo = df_f_maee_item
                            else:
                                df_p_fluxo = df_p_ativo[df_p_ativo['ano_mov'] == ano_selecionado]; df_p_saldo = df_p_ativo[df_p_ativo['ano_mov'].astype(int) <= int(ano_selecionado)]
                                f_maee_item = df_p_ativo['fonte_clean'].iloc[0].lower().strip(); df_f_maee_item = df[df['fonte_clean'] == f_maee_item]; df_f_saldo = df_f_maee_item[df_f_maee_item['ano_mov'].astype(int) <= int(ano_selecionado)]; df_f_fluxo = df_f_maee_item[df_f_maee_item['ano_mov'] == ano_selecionado]
                            p_rep = float(df_f_fluxo['repasse'].sum()) if p_item == plano_final_analise else float(df_p_fluxo['repasse'].sum())
                            p_ren = float(df_f_fluxo['rendimento'].sum()) if p_item == plano_final_analise else float(df_p_fluxo['rendimento'].sum())
                            p_des = float(df_p_fluxo['bruto'].sum())
                            p_saldo_acum = (float(df_f_saldo['repasse'].sum() + df_f_saldo['rendimento'].sum()) - p_des) if p_item == plano_final_analise else (float(df_p_saldo['repasse'].sum() + df_p_saldo['rendimento'].sum()) - p_des)
                            t_rep += p_rep; t_ren += p_ren; t_gasto += p_des; t_saldo += p_saldo_acum
                            linhas_banco_pln.append({'Plano de Ação': p_item + (" (Ativo 🎯)" if p_item == plano_final_analise else ""), 'Fonte Vinculada': f_maee_item.upper(), 'Repasses no Período': p_rep, 'Rendimentos no Período': p_ren, 'Despesas no Período': p_des, 'Saldo Real do Plano (Acumulado)': p_saldo_acum})
                        linhas_banco_pln.append({'Plano de Ação': 'TOTAL CONSOLIDADO DA CONTA CORRENTE 🏦', 'Fonte Vinculada': '-', 'Repasses no Período': t_rep, 'Rendimentos no Período': t_ren, 'Despesas no Período': t_gasto, 'Saldo Real do Plano (Acumulado)': t_saldo})
                        df_tab_banco_pln = pd.DataFrame(linhas_banco_pln)
                        def _style_linhas_pln(row): return ['background-color: #f1f5f9; font-weight: 800; border-top: 2px solid #000000;' if 'TOTAL CONSOLIDADO' in str(row['Plano de Ação']).upper() else ('background-color: #e0f2fe; font-weight: 700;' if '(ATIVO 🎯)' in str(row['Plano de Ação']).upper() else '') for _ in row]
                        st.dataframe(df_tab_banco_pln.style.apply(_style_linhas_pln, axis=1).format({'Repasses no Período': fmt, 'Rendimentos no Período': fmt, 'Despesas no Período': fmt, 'Saldo Real do Plano (Acumulado)': fmt}), use_container_width=True, hide_index=True)
                    
                    st.markdown(f"<div class='section-title' style='color: #0f172a; border-bottom: 3px solid #0f172a;'>📋 Detalhamento dos Lançamentos do Plano — ({lbl_ano_pln})</div>", unsafe_allow_html=True)
                    df_pln_validos = df_despesas_fluxo[df_despesas_fluxo['EMPENHO_COL'] != '-']
                    if not df_pln_validos.empty:
                        lista_links_pln = [str(lk).strip() if str(lk).strip().startswith("http") else None for lk in df_pln_validos['URL_REAL_LINK']]
                        df_render_pln = pd.DataFrame({'Data Lançamento': df_pln_validos['DATA_LANCAMENTO'], 'Nº Empenho': df_pln_validos['EMPENHO_COL'], 'Nota Fiscal': df_pln_validos['NOTA_COL'], 'Secretaria Executor': df_pln_validos['secretaria'].astype(str).str.upper(), 'Valor Bruto NF': df_pln_validos['bruto'], 'Comprovante/PDF 📄': lista_links_pln})
                        st.dataframe(df_render_pln.style.format({'Valor Bruto NF': fmt}).set_properties(**{'font-weight': '500', 'font-size': '12px'}), use_container_width=True, hide_index=True, column_config={"Data Lançamento": st.column_config.TextColumn(alignment="center"), "Nº Empenho": st.column_config.TextColumn(alignment="center"), "Nota Fiscal": st.column_config.TextColumn(alignment="center"), "Secretaria Executor": st.column_config.TextColumn(alignment="left"), "Valor Bruto NF": st.column_config.NumberColumn(alignment="right"), "Comprovante/PDF 📄": st.column_config.LinkColumn(display_text="Abrir Documento 🔗")})
                    else: st.info("ℹ️ Nenhum empenho ou nota fiscal emitidos para este Plano de Ação no período selecionado.")
            else: st.info("ℹ️ Nenhum Plano de Ação identificado ou registrado na base de dados atual.")
            
except Exception as e:
    st.error(f"Erro no processamento unificado: {e}")
