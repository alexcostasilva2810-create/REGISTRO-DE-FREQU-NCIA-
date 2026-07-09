import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import datetime as dt
from fpdf import FPDF
from io import BytesIO
import base64  # Necessário para codificar a imagem de fundo

# --- CONFIGURAÇÃO VISUAL (CSS PERSONALIZADO) ---
def carregar_css_com_fundo(nome_arquivo_imagem):
    with open(nome_arquivo_imagem, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    
    css_string = f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpeg;base64,{encoded_string}");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}

    /* Ajuste para melhorar a legibilidade do texto sobre o fundo */
    h1, h2, h3, p, .stMarkdown, div[data-baseweb="select"] {{
        background-color: rgba(255, 255, 255, 0.85); /* Fundo branco semitransparente atrás do texto */
        padding: 5px 10px;
        border-radius: 5px;
    }}
    
    /* Ajustes específicos para inputs e texto do form */
    .stTextInput>div>div>input, .stForm {{
        background-color: white !important;
    }}
    
    /* Melhora visual para a tabela */
    [data-testid="stDataFrame"] {{
        background-color: rgba(255, 255, 255, 0.9) !important;
        border-radius: 5px;
        padding: 5px;
    }}
    </style>
    """
    st.markdown(css_string, unsafe_allow_html=True)

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
def iniciar_bd():
    conn = sqlite3.connect('registro_presenca.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS frequencia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            encarregado TEXT,
            localidade TEXT,
            balsa TEXT,
            nome_escolta TEXT, -- AJUSTE NO NOME DA COLUNA NO BD
            data TEXT,
            hora TEXT,
            observacao TEXT
        )
    ''')
    conn.commit()
    conn.close()

def salvar_registro(encarregado, localidade, balsa, nome_escolta, data, hora, observacao):
    conn = sqlite3.connect('registro_presenca.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO frequencia (encarregado, localidade, balsa, nome_escolta, data, hora, observacao)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (encarregado, localidade, balsa, nome_escolta, data, hora, observacao))
    conn.commit()
    conn.close()

def buscar_registros_df():
    conn = sqlite3.connect('registro_presenca.db')
    query = "SELECT encarregado, localidade, balsa, nome_escolta, data, hora, observacao FROM frequencia"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # AJUSTE NO NOME DA COLUNA NA EXIBIÇÃO DA TABELA
    df.columns = ["Encarregado", "Localidade", "Balsa", "Nome do Escolta", "Data", "Hora", "Observação"]
    return df

# Inicializa o banco de dados
iniciar_bd()

# --- FUNÇÃO PARA GERAR PDF EM MEMÓRIA ---
def gerar_pdf(df):
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    
    # Título do PDF
    pdf.cell(0, 10, "RELATORIO DE FREQUENCIA E PRESENCA", ln=True, align="C")
    pdf.ln(10)
    
    # Cabeçalho da Tabela
    pdf.set_font("Helvetica", "B", 10)
    col_larguras = [35, 35, 30, 55, 25, 25, 75]
    colunas = list(df.columns)
    
    for i, col in enumerate(colunas):
        pdf.cell(col_larguras[i], 8, col.upper(), border=1, align="C")
    pdf.ln()
    
    # Dados da Tabela
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

# --- CONTROLE DE SESSÃO (LOGIN) ---
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

USUARIOS_VALIDOS = {
    "admin": "1234",
    "supervisor": "senha123"
}

def tela_login():
    # Tenta carregar a imagem de fundo para a tela de login também
    try:
        carregar_css_com_fundo("fundo_porto.jpg")
    except FileNotFoundError:
        st.warning("Imagem 'fundo_porto.jpg' não encontrada. Usando fundo padrão.")

    st.subheader("🔑 Login do Sistema")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        if usuario in USUARIOS_VALIDOS and USUARIOS_VALIDOS[usuario] == senha:
            st.session_state['logado'] = True
            st.session_state['usuario_atual'] = usuario
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")

# --- TELA PRINCIPAL (SISTEMA) ---
def tela_sistema():
    # Carrega o CSS com a imagem de fundo
    try:
        carregar_css_com_fundo("fundo_porto.jpg")
    except FileNotFoundError:
        st.warning("Imagem 'fundo_porto.jpg' não encontrada. Usando fundo padrão.")

    st.title("📋 Sistema de Registro de Presença")
    st.write(f"Conectado como: **{st.session_state['usuario_atual'].upper()}**")
    
    if st.button("Sair / Logout"):
        st.session_state['logado'] = False
        st.rerun()
        
    st.markdown("---")
    
    # Formulário de Entrada de Dados
    st.subheader("✍️ Nova Conferência de Frequência")
    
    lista_localidades = [
        "MIRITITUBA", "SANTARÉM", "BELÉM", "MANAUS", 
        "TROMBETAS", "JURUTIR", "PORTO VELHO", "NOVO REMANSO"
    ]
    
    fuso_horario = dt.timezone(dt.timedelta(hours=-3))
    agora_local = datetime.now(fuso_horario)
    
    with st.form(key='form_registro'):
        col1, col2 = st.columns(2)
        
        with col1:
            encarregado_input = st.text_input("Encarregado", value=st.session_state['usuario_atual'])
            localidade = st.selectbox("Localidade", options=lista_localidades)
            balsa_input = st.text_input("Balsa")
            
        with col2:
            # AJUSTE NO RÓTULO DO CAMPO NO FORMULÁRIO
            nome_escolta_input = st.text_input("Nome do Escolta")
            data_atual = st.date_input("Data", agora_local.date(), format="DD/MM/YYYY")
            hora_atual = st.time_input("Hora", agora_local.time())
            
        observacao_input = st.text_area("Observação")
            
        botao_enviar = st.form_submit_button("Registrar Presença")
        
        if botao_enviar:
            if balsa_input and nome_escolta_input:
                hora_str = hora_atual.strftime("%H:%M")
                data_str = data_atual.strftime("%d/%m/%Y")
                
                encarregado = encarregado_input.strip().upper()
                balsa = balsa_input.strip().upper()
                nome_escolta = nome_escolta_input.strip().upper()
                observacao = observacao_input.strip().upper()
                
                salvar_registro(encarregado, localidade, balsa, nome_escolta, data_str, hora_str, observacao)
                st.success("✅ REGISTRO SALVO COM SUCESSO!")
                st.rerun()
            else:
                st.error("⚠️ Por favor, preencha os campos obrigatórios (Balsa e Nome do Escolta).")

    st.markdown("---")
    
    # Visualização da Tabela de Registros
    st.subheader("📊 Histórico de Frequência")
    
    if st.session_state['usuario_atual'] == 'admin':
        if st.button("⚠️ Limpar Histórico Antigo (Apagar Tabela/Reset)"):
            conn = sqlite3.connect('registro_presenca.db')
            c = conn.cursor()
            c.execute("DROP TABLE IF EXISTS frequencia")
            conn.commit()
            conn.close()
            iniciar_bd()
            st.warning("O banco de dados foi limpo. Faça um novo teste agora!")
            st.rerun()
            
    df_registros = buscar_registros_df()
    
    if not df_registros.empty:
        st.dataframe(df_registros, use_container_width=True)
        
        # PAINEL DO ADMINISTRADOR
        if st.session_state['usuario_atual'] == 'admin':
            st.markdown("### 🛠️ Painel do Administrador")
            try:
                pdf_bytes = gerar_pdf(df_registros)
                st.download_button(
                    label="📥 Exportar Histórico para PDF",
                    data=pdf_bytes,
                    file_name=f"historico_frequencia_{datetime.now().strftime('%d_%m_%Y')}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Erro ao processar PDF: {e}")
    else:
        st.info("Nenhum registro encontrado até o momento.")

# --- FLUXO DA APLICAÇÃO ---
if not st.session_state['logado']:
    tela_login()
else:
    tela_sistema()
