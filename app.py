import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import datetime as dt
from fpdf import FPDF
from io import BytesIO

###############################################################################
# CONFIGURAÇÃO DE PÁGINA ORIGEM
###############################################################################
st.set_page_config(
    page_title="Controle de Frequência",
    layout="centered",
    initial_sidebar_state="expanded"
)

###############################################################################
# BLOCO I: ESTILIZAÇÃO DO LAYOUT ORIGINAL
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
    
    .block-container {{
        max-width: 800px !important;
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }}
    
    /* Box do Formulário Original */
    div[data-testid="stForm"] {{
        background-color: rgba(255, 255, 255, 0.95) !important;
        padding: 25px !important;
        border-radius: 10px !important;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.15);
    }}
    
    /* Título Superior */
    .titulo-principal {{
        background-color: #f8fafc;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        font-size: 24px;
        color: #1e293b;
        margin-bottom: 20px;
        border: 1px solid #e2e8f0;
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
    st.markdown('<div class="titulo-principal">⚡ CONTROLE DE ACESSO</div>', unsafe_allow_html=True)
    
    with st.form(key='form_login'):
        usuario = st.text_input("Usuário / Credencial").strip().lower()
        senha = st.text_input("Senha", type="password")
        botao_login = st.form_submit_button("Autenticar")
        
        if botao_login:
            if usuario in USUARIOS_VALIDOS and str(USUARIOS_VALIDOS[usuario]) == str(senha):
                st.session_state['logado'] = True
                st.session_state['usuario_atual'] = usuario
                st.rerun()
            else:
                st.error("Credenciais incorretas ou operador não autorizado.")


###############################################################################
# BLOCO V: TELA DO SISTEMA ORIGINAL (DUAS COLUNAS PARALELAS)
###############################################################################
def tela_sistema():
    carregar_css_com_fundo()
    usuario_sessao = st.session_state['usuario_atual']
    
    # Sidebar
    st.sidebar.title("Menu")
    st.sidebar.write(f"Operador Ativo: **{usuario_sessao.upper()}**")
    if st.sidebar.button("🚪 Sair do Sistema", use_container_width=True):
        st.session_state['logado'] = False
        st.rerun()
        
    df_registros = buscar_registros_df(usuario_sessao)
    
    if usuario_sessao == 'admin':
        st.sidebar.markdown("---")
        st.sidebar.write("**Painel Admin**")
        if not df_registros.empty:
            try:
                pdf_bytes = gerar_pdf(df_registros)
                st.sidebar.download_button(
                    label="📥 Exportar para PDF",
                    data=pdf_bytes,
                    file_name=f"frequencia_{datetime.now().strftime('%d_%m_%Y')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.sidebar.error(f"Erro PDF: {e}")
                
        if st.sidebar.button("⚠️ Limpar Banco de Dados", use_container_width=True):
            conn = sqlite3.connect('registro_presenca.db')
            c = conn.cursor()
            c.execute("DROP TABLE IF EXISTS frequencia")
            conn.commit()
            conn.close()
            inicializar_banco_seguro()
            st.rerun()

    # Título do Formulário
    st.markdown('<div class="titulo-principal">📝 Nova Conferência de Frequência</div>', unsafe_allow_html=True)
    
    # Estrutura de colunas idêntica à foto de origem
    with st.form(key='form_registro'):
        col1, col2 = st.columns(2)
        
        with col1:
            encarregado_input = st.text_input("Encarregado", value=usuario_sessao.upper(), disabled=(usuario_sessao != 'admin'))
            lista_localidades = ["MIRITITUBA", "SANTARÉM", "BELÉM", "MANAUS", "TROMBETAS", "JURUTIR", "PORTO VELHO", "NOVO REMANSO"]
            localidade = st.selectbox("Localidade", options=lista_localidades)
            balsa_input = st.text_input("Balsa")
            
        with col2:
            nome_escolta_input = st.text_input("Nome do Escolta")
            fuso_horario = dt.timezone(dt.timedelta(hours=-3))
            agora_local = datetime.now(fuso_horario)
            data_atual = st.date_input("Data", agora_local.date(), format="DD/MM/YYYY")
            hora_atual = st.time_input("Hora", agora_local.time())
            
        observacao_input = st.text_area("Observação", value="", height=100)
        
        botao_enviar = st.form_submit_button("Registrar Presença")
        
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
                st.success("Presença registrada com sucesso!")
                st.rerun()
            else:
                st.error("Por favor, preencha todos os campos obrigatórios (Balsa e Escolta).")

    # Histórico abaixo do formulário
    st.markdown("---")
    st.subheader("📊 Histórico Operacional Geral")
    if not df_registros.empty:
        st.dataframe(df_registros, use_container_width=True)
    else:
        st.info("Nenhum registro de frequência encontrado até o momento.")


###############################################################################
# BLOCO VII: INICIALIZAÇÃO DO FLUXO
###############################################################################
inicializar_banco_seguro()

if not st.session_state['logado']:
    tela_login()
else:
    tela_sistema()
