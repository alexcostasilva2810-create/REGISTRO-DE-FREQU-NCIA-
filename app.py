import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import datetime as dt
from fpdf import FPDF
from io import BytesIO

###############################################################################
# CONFIGURAÇÃO COMPACTA MÁXIMA DE PÁGINA
###############################################################################
st.set_page_config(
    page_title="Controle",
    layout="wide",
    initial_sidebar_state="collapsed"
)

###############################################################################
# BLOCO I: DESIGN ULTRA-COMPACTO (CSS SLIM)
###############################################################################
def carregar_css_com_fundo():
    url_fundo = "https://images.unsplash.com/photo-1557597774-9d273605dfa9?q=80&w=1200&auto=format&fit=crop"
    
    css_string = f"""
    <style>
    .stApp {{
        background-image: url("{url_fundo}");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
        background-position: center;
    }}
    
    /* Remove espaços vazios do topo e fundo */
    .block-container {{
        padding-top: 0.2rem !important;
        padding-bottom: 0.2rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }}
    
    h1 {{
        font-size: 16px !important;
        margin: 2px 0px !important;
        padding: 2px !important;
        text-align: center;
        background-color: rgba(255, 255, 255, 0.96);
        border-radius: 4px;
    }}
    
    /* Elementos menores e com pouca margem */
    div[data-testid="stForm"] {{
        padding: 6px !important;
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 6px;
        margin-bottom: 2px !important;
    }}
    
    .stTextInput>div>div>input, div[data-baseweb="select"]>div, .stForm {{
        background-color: white !important;
        border: 1px solid #1E293B !important;
        height: 28px !important;
        font-size: 12px !important;
    }}
    
    label {{
        font-size: 11px !important;
        margin-bottom: 1px !important;
        font-weight: bold !important;
    }}
    
    /* Botão Slim */
    .stButton>button {{
        width: 100% !important;
        height: 32px !important;
        font-size: 13px !important;
        background-color: #1E293B !important;
        color: white !important;
        margin-top: 5px !important;
    }}
    
    /* Histórico Compactado */
    [data-testid="stDataFrame"] {{
        background-color: rgba(255, 255, 255, 0.96) !important;
        font-size: 11px !important;
    }}
    </style>
    """
    st.markdown(css_string, unsafe_allow_html=True)


###############################################################################
# BLOCO II: BANCO DE DADOS (SQLITE3)
###############################################################################
def inicializar_banco_seguro():
    conn = sqlite3.connect('registro_presenca.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS frequencia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            encarregado TEXT,
            localidade TEXT,
            balsa TEXT,
            nome_escolta TEXT,
            data TEXT,
            hora TEXT,
            observacao TEXT
        )
    ''')
    conn.commit()
    conn.close()

def obter_coluna_segura():
    inicializar_banco_seguro()
    conn = sqlite3.connect('registro_presenca.db')
    c = conn.cursor()
    c.execute("PRAGMA table_info(frequencia)")
    colunas = [col[1] for col in c.fetchall()]
    conn.close()
    
    if "nome_esc" in colunas:
        return "nome_esc"
    return "nome_escolta"

def salvar_registro(encarregado, localidade, balsa, valor_escolta, data, hora, observacao):
    coluna_ativa = obter_coluna_segura()
    conn = sqlite3.connect('registro_presenca.db')
    c = conn.cursor()
    
    query = f'''
        INSERT INTO frequencia (encarregado, localidade, balsa, {coluna_ativa}, data, hora, observacao)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    '''
    c.execute(query, (encarregado.strip().upper(), localidade, balsa, valor_escolta, data, hora, observacao))
    conn.commit()
    conn.close()

def buscar_registros_df(usuario_atual):
    inicializar_banco_seguro()
    conn = sqlite3.connect('registro_presenca.db')
    c = conn.cursor()
    c.execute("PRAGMA table_info(frequencia)")
    colunas = [col[1] for col in c.fetchall()]
    
    coluna_busca = "nome_esc" if "nome_esc" in colunas else "nome_escolta"
    
    if usuario_atual.lower() == 'admin':
        query = f"SELECT encarregado, localidade, balsa, {coluna_busca}, data, hora, observacao FROM frequencia"
        df = pd.read_sql_query(query, conn)
    else:
        query = f"SELECT encarregado, localidade, balsa, {coluna_busca}, data, hora, observacao FROM frequencia WHERE UPPER(encarregado) = ?"
        df = pd.read_sql_query(query, conn, params=(usuario_atual.strip().upper(),))
        
    conn.close()
    
    df.columns = ["Encarregado", "Localidade", "Balsa", "Nome do Escolta", "Data", "Hora", "Observação"]
    return df


###############################################################################
# BLOCO III: RELATÓRIOS (PDF)
###############################################################################
def gerar_pdf(df):
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "RELATORIO DE FREQUENCIA E PRESENCA", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Helvetica", "B", 10)
    col_larguras = [35, 35, 30, 55, 25, 25, 75]
    colunas = list(df.columns)
    
    for i, col in enumerate(colunas):
        pdf.cell(col_larguras[i], 8, col.upper(), border=1, align="C")
    pdf.ln()
    
    pdf.set_font("Helvetica", "", 9)
    for _, row in df.iterrows():
        for i, col in enumerate(colunas):
            texto = str(row[col]).encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(col_larguras[i], 8, texto, border=1, align="L" if i == 6 else "C")
        pdf.ln()
        
    pdf_buffer = BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()


###############################################################################
# BLOCO IV: CONTROLE DE ACESSO
###############################################################################
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

USUARIOS_VALIDOS = {
    "admin": "1234",
    "supervisor": "senha123",
    "janari": "223344",
    "elton": "431263",
    "usuario4": "frequencia4",
    "usuario5": "frequencia5",
    "usuario6": "frequencia6",
    "usuario7": "frequencia7"
}

def tela_login():
    carregar_css_com_fundo()
    st.subheader("⚡ LOGIN")
    
    usuario = st.text_input("Usuário").strip().lower()
    senha = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        if usuario in USUARIOS_VALIDOS and str(USUARIOS_VALIDOS[usuario]) == str(senha):
            st.session_state['logado'] = True
            st.session_state['usuario_atual'] = usuario
            st.rerun()
        else:
            st.error("Incorreto.")


###############################################################################
# BLOCO V: INTERFACE TOTALMENTE COMPACTADA EM LINHAS TRIPLAS
###############################################################################
def tela_sistema():
    carregar_css_com_fundo()
    usuario_sessao = st.session_state['usuario_atual']
    
    st.sidebar.write(f"Operador: **{usuario_sessao.upper()}**")
    if st.sidebar.button("🚪 Sair", use_container_width=True):
        st.session_state['logado'] = False
        st.rerun()
        
    df_registros = buscar_registros_df(usuario_sessao)
    
    if usuario_sessao == 'admin':
        if not df_registros.empty:
            try:
                pdf_bytes = gerar_pdf(df_registros)
                st.sidebar.download_button(
                    label="📥 PDF",
                    data=pdf_bytes,
                    file_name=f"frequencia_{datetime.now().strftime('%d_%m_%Y')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.sidebar.error(f"Erro PDF: {e}")
                
        if st.sidebar.button("⚠️ Limpar Banco", use_container_width=True):
            conn = sqlite3.connect('registro_presenca.db')
            c = conn.cursor()
            c.execute("DROP TABLE IF EXISTS frequencia")
            conn.commit()
            conn.close()
            inicializar_banco_seguro()
            st.rerun()

    st.title("🛡️ Painel Operacional")
    
    with st.form(key='form_registro'):
        # Linha 1 do Formulário
        c1, c2, c3 = st.columns(3)
        with c1:
            encarregado_input = st.text_input("Encarregado", value=usuario_sessao.upper(), disabled=(usuario_sessao != 'admin'))
        with c2:
            lista_localidades = ["MIRITITUBA", "SANTARÉM", "BELÉM", "MANAUS", "TROMBETAS", "JURUTIR", "PORTO VELHO", "NOVO REMANSO"]
            localidade = st.selectbox("Localidade", options=lista_localidades)
        with c3:
            balsa_input = st.text_input("Balsa")
            
        # Linha 2 do Formulário
        c4, c5, c6 = st.columns(3)
        with c4:
            nome_escolta_input = st.text_input("Escolta")
        with c5:
            fuso_horario = dt.timezone(dt.timedelta(hours=-3))
            agora_local = datetime.now(fuso_horario)
            data_atual = st.date_input("Data", agora_local.date(), format="DD/MM/YYYY")
        with c6:
            hora_atual = st.time_input("Hora", agora_local.time())
            
        observacao_input = st.text_input("Observação")
        
        botao_enviar = st.form_submit_button("SALVAR REGISTRO")
        
        if botao_enviar:
            if balsa_input and nome_escolta_input:
                hora_str = hora_atual.strftime("%H:%M")
                data_str = data_atual.strftime("%d/%m/%Y")
                
                salvar_registro(
                    encarregado_input.strip().upper(), 
                    localidade, 
                    balsa_input.strip().upper(), 
                    nome_escolta_input.strip().upper(), 
                    data_str, 
                    hora_str, 
                    observacao_input.strip().upper()
                )
                st.success("Salvo!")
                st.rerun()
            else:
                st.error("Preencha balsa e escolta.")

    st.write("**Histórico Recente**")
    if not df_registros.empty:
        st.dataframe(df_registros, use_container_width=True, height=150) # Altura fixa para não empurrar a tela
    else:
        st.info("Vazio.")


###############################################################################
# BLOCO VII: START
###############################################################################
inicializar_banco_seguro()

if not st.session_state['logado']:
    tela_login()
else:
    tela_sistema()
