import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import datetime as dt
from fpdf import FPDF
from io import BytesIO

###############################################################################
# CONFIGURAÇÃO DE PÁGINA (CRÍTICA PARA ANDROID)
###############################################################################
st.set_page_config(
    page_title="Controle Operacional",
    layout="wide",  # Faz o app usar toda a largura da tela do celular
    initial_sidebar_state="collapsed"  # Mantém o menu lateral recolhido no celular para dar espaço
)

###############################################################################
# BLOCO I: CONFIGURAÇÃO VISUAL ADAPTADA PARA CELULAR (CSS MOBILE)
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
    
    /* Fontes maiores e blocos mais visíveis no celular */
    h1 {{
        font-size: 24px !important;
        text-align: center;
    }}
    h2, h3, p, .stMarkdown, div[data-baseweb="select"], .stAlert {{
        background-color: rgba(255, 255, 255, 0.95);
        padding: 12px 15px;
        border-radius: 8px;
        color: #0F172A !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.15);
        font-size: 16px !important; /* Tamanho de letra ideal para leitura no Android */
    }}
    
    /* Inputs de texto fáceis de tocar com o dedo */
    .stTextInput>div>div>input, .stForm {{
        background-color: white !important;
        border: 2px solid #1E293B !important; /* Borda mais grossa para enxergar melhor */
        height: 45px !important; /* Mais alto para facilitar o toque */
        font-size: 16px !important;
    }}
    
    /* Ajuste para a tabela não quebrar no celular */
    [data-testid="stDataFrame"] {{
        background-color: rgba(255, 255, 255, 0.96) !important;
        border-radius: 6px;
        padding: 5px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }}
    
    /* Botões grandes e robustos para o operador clicar sem errar */
    .stButton>button {{
        width: 100% !important;
        height: 50px !important;
        font-size: 16px !important;
        font-weight: bold !important;
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
    
    df.columns = ["Encarregado", "Localidade", "Balsa", "Nome do Escolta", "Data", "Hora", "Observação"]
    return df


###############################################################################
# BLOCO III: EXPORTAÇÃO DE RELATÓRIOS (GERAÇÃO DE PDF)
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
# BLOCO IV: CADASTRO E CONTROLE DE ACESSO
###############################################################################
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

USUARIOS_VALIDOS = {
    "admin": "1234",
    "supervisor": "senha123",
    "janari": "223344",
    "usuario4": "frequencia4",
    "usuario5": "frequencia5",
    "usuario6": "frequencia6",
    "usuario7": "frequencia7"
}

def tela_login():
    carregar_css_com_fundo()
    st.subheader("⚡ CONTROLE DE ACESSO")
    
    usuario = st.text_input("Usuário / Credencial").strip().lower()
    senha = st.text_input("Senha", type="password")
    
    if st.button("Autenticar"):
        if usuario in USUARIOS_VALIDOS and str(USUARIOS_VALIDOS[usuario]) == str(senha):
            st.session_state['logado'] = True
            st.session_state['usuario_atual'] = usuario
            st.rerun()
        else:
            st.error("Credenciais incorretas.")


###############################################################################
# BLOCO V: PAINEL PRINCIPAL ADAPTADO PARA APONTAMENTO VIA CELULAR
###############################################################################
def tela_sistema():
    carregar_css_com_fundo()
    usuario_sessao = st.session_state['usuario_atual']
    
    # --- BARRA LATERAL ---
    st.sidebar.title("⚙️ Menu")
    st.sidebar.write(f"Operador: **{usuario_sessao.upper()}**")
    
    if st.sidebar.button("🚪 Sair do Sistema", use_container_width=True):
        st.session_state['logado'] = False
        st.rerun()
        
    df_registros = buscar_registros_df(usuario_sessao)
    
    if usuario_sessao == 'admin':
        st.sidebar.markdown("---")
        st.sidebar.subheader("🛠️ Painel Admin")
        if not df_registros.empty:
            try:
                pdf_bytes = gerar_pdf(df_registros)
                st.sidebar.download_button(
                    label="📥 Exportar para PDF",
                    data=pdf_bytes,
                    file_name=f"historico_frequencia_{datetime.now().strftime('%d_%m_%Y')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.sidebar.error(f"Erro no PDF: {e}")
                
        if st.sidebar.button("⚠️ Limpar Banco de Dados", use_container_width=True):
            conn = sqlite3.connect('registro_presenca.db')
            c = conn.cursor()
            c.execute("DROP TABLE IF EXISTS frequencia")
            conn.commit()
            conn.close()
            inicializar_banco_seguro()
            st.success("Reiniciado!")
            st.rerun()

    # --- CORPO CENTRAL ---
    st.title("🛡️ Registro de Escolta")
    st.markdown("---")
    
    # ATENÇÃO MOBILE: No Android as fotos laterais iam esmagar o formulário.
    # Agora elas só aparecem se a tela for grande. No celular, o formulário ocupa o espaço todo.
    with st.form(key='form_registro'):
        st.subheader("✍️ Nova Conferência")
        
        encarregado_input = st.text_input("Encarregado", value=usuario_sessao.upper(), disabled=(usuario_sessao != 'admin'))
        
        lista_localidades = ["MIRITITUBA", "SANTARÉM", "BELÉM", "MANAUS", "TROMBETAS", "JURUTIR", "PORTO VELHO", "NOVO REMANSO"]
        localidade = st.selectbox("Localidade", options=lista_localidades)
        
        balsa_input = st.text_input("Identificação da Balsa")
        nome_escolta_input = st.text_input("Nome do Vigilante / Escolta")
        
        fuso_horario = dt.timezone(dt.timedelta(hours=-3))
        agora_local = datetime.now(fuso_horario)
        
        c1, c2 = st.columns(2)
        with c1:
            data_atual = st.date_input("Data", agora_local.date(), format="DD/MM/YYYY")
        with c2:
            hora_atual = st.time_input("Hora", agora_local.time())
            
        observacao_input = st.text_area("Observações Gerais")
        
        botao_enviar = st.form_submit_button("CONFERIR E SALVAR REGISTRO")
        
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
                st.success("✅ REGISTRO SALVO NO BANCO!")
                st.rerun()
            else:
                st.error("⚠️ Preencha os campos obrigatórios (Balsa e Escolta).")

    st.markdown("---")
    if usuario_sessao == 'admin':
        st.subheader("📊 Histórico Operacional Geral")
    else:
        st.subheader("📊 Meus Registros Recentes")
    
    if not df_registros.empty:
        st.dataframe(df_registros, use_container_width=True)
    else:
        st.info("Nenhum lançamento encontrado para este usuário.")


###############################################################################
# BLOCO VII: FLUXO PRINCIPAL
###############################################################################
inicializar_banco_seguro()

if not st.session_state['logado']:
    tela_login()
else:
    tela_sistema()
