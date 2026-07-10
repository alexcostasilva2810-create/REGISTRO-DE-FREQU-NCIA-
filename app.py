import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import datetime as dt
from fpdf import FPDF
from io import BytesIO

###############################################################################
# CONFIGURAÇÃO COMPACTA DE PÁGINA
###############################################################################
st.set_page_config(
    page_title="Controle",
    layout="wide",
    initial_sidebar_state="collapsed"
)

###############################################################################
# BLOCO I: DESIGN COMPACTO (CSS MINIMALISTA)
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
    
    /* Reduzindo margens e paddings para compactar a tela */
    .block-container {{
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }}
    
    h1 {{
        font-size: 20px !important;
        margin-bottom: 5px !important;
        padding: 5px !important;
        text-align: center;
    }}
    
    h3, p, .stMarkdown, div[data-baseweb="select"], .stAlert {{
        background-color: rgba(255, 255, 255, 0.96);
        padding: 6px 10px !important;
        border-radius: 6px;
        color: #0F172A !important;
        font-size: 14px !important;
        margin-bottom: 4px !important;
    }}
    
    /* Inputs menores e mais juntos */
    .stTextInput>div>div>input, .stForm {{
        background-color: white !important;
        border: 1px solid #1E293B !important;
        height: 35px !important;
        font-size: 14px !important;
    }}
    
    div[data-testid="stForm"] {{
        padding: 10px !important;
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 8px;
    }}
    
    /* Botão de envio firme e limpo */
    .stButton>button {{
        width: 100% !important;
        height: 40px !important;
        font-size: 14px !important;
        background-color: #1E293B !important;
        color: white !important;
    }}
    </style>
    """
    st.markdown(css_string, unsafe_allow_html=True)


###############################################################################
# BLOCO II: CONEXÃO E GERENCIAMENTO DO BANCO DE DADOS (SQLITE3)
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
    coluna_ativa = obtener_coluna_segura()
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
    
    df.columns =
