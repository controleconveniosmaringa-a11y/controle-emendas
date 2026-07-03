import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
import json
import re

# ==========================================
# 1. CONFIGURAÇÃO
# ==========================================
st.set_page_config(page_title="Fluxo BPM Pro", page_icon="🏢", layout="wide")

if "etapas" not in st.session_state: 
    st.session_state.etapas = []

# Configuração Groq
if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.error("Configure sua GROQ_API_KEY no secrets.")
    st.stop()

# ==========================================
# 2. MOTOR DE DESIGN BPMN (CSS + SUBGRAPHS)
# ==========================================
def renderizar_mermaid(codigo_mermaid, altura=800):
    html = f"""
    <html><body><div class="mermaid">{codigo_mermaid}</div>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ 
            startOnLoad: true, theme: 'base',
            themeVariables: {{ 
                fontFamily: 'Inter, sans-serif', 
                primaryColor: '#f1f5f9',
                secondaryColor: '#e2e8f0'
            }},
            flowchart: {{ useMaxWidth: true, htmlLabels: true }}
        }});
    </script></body></html>
    """
    components.html(html, height=altura, scrolling=True)

# ==========================================
# 3. IA (GROQ LLAMA 3.1)
# ==========================================
def processar_ia(texto):
    prompt = """
    Analise o processo e retorne APENAS um JSON array.
    Estrutura: {"id": "A", "texto": "Curto", "tipo": "Processo", "raia": "Departamento", "proxima": "B"}
    Os tipos permitidos: "Início", "Processo", "Decisão", "Fim"
    Processo: """ + texto
    
    completion = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    res = completion.choices[0].message.content
    match = re.search(r'\[.*\]', res, re.DOTALL)
    if match: return json.loads(match.group(0))
    return []

# ==========================================
# 4. INTERFACE
# ==========================================
st.title("🏢 Gerador de Fluxos BPM (Swimlanes)")

aba1, aba2 = st.tabs(["🤖 Gerador IA", "✏️ Tabela de Edição"])

with aba1:
    texto = st.text_area("Descreva o processo (quem faz o quê):")
    if st.button("Gerar Fluxo BPM"):
        st.session_state.etapas = processar_ia(texto)
        st.rerun()

with aba2:
    st.session_state.etapas = st.data_editor(st.session_state.etapas, use_container_width=True, num_rows="dynamic")

# ==========================================
# 5. GERADOR DE CÓDIGO BPM (Swimlanes)
# ==========================================
if st.session_state.etapas:
    # 1. Agrupar por Raia
    raias = {}
    for et in st.session_state.etapas:
        r = et.get('raia', 'Geral')
        if r not in raias: raias[r] = []
        raias[r].append(et)
    
    # 2. Montar código Mermaid com subgraphs
    codigo = "graph TD\n"
    for nome_raia, nodes in raias.items():
        codigo += f"subgraph {nome_raia.replace(' ', '_')}[{nome_raia}]\n"
        for et in nodes:
            id_n = str(et['id']).replace(" ", "_")
            txt = et['texto'].replace('"', "'")
            cls = et['tipo']
            if cls == "Decisão": codigo += f'{id_n}{{"{txt}"}}\n'
            else: codigo += f'{id_n}["{txt}"]\n'
        codigo += "end\n"
        
    # 3. Adicionar conexões
    for et in st.session_state.etapas:
        if et.get('proxima'):
            for p in str(et['proxima']).split(","):
                codigo += f"{et['id'].replace(' ', '_')} --> {p.strip().replace(' ', '_')}\n"
    
    renderizar_mermaid(codigo)
