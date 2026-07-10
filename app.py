import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import datetime as dt
from fpdf import FPDF
from io import BytesIO

###############################################################################
# BLOCO I: CONFIGURAÇÃO VISUAL E ESTILIZAÇÃO (CSS)
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
    h1, h2, h3, p, .stMarkdown, div[data-baseweb="select"], .stAlert {{
        background-color: rgba(255, 255, 255, 0.95);
        padding: 10px 15px;
        border-radius: 6px;
        color: #0F172A !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.15);
    }}
    .stTextInput>div>div>input, .stForm {{
        background-color: white !important;
        border: 1px solid #1E293B !important;
    }}
    [data-testid="stDataFrame"] {{
        background-color: rgba(255, 255, 255, 0.96) !important;
        border-radius: 6px;
        padding: 5px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }}
    </style>
    """
    st.markdown(css_string, unsafe_allow_html=True)


###############################################################################
# BLOCO II: CONEXÃO E GERENCIAMENTO DO BANCO DE DADOS (SQLITE3)
###############################################################################
def inicializar_banco_seguro():
    """Garante que a tabela sempre exista para evitar erros de 'no such table'"""
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
    c.execute(query, (encarregado, localidade, balsa, valor_escolta, data, hora, observacao))
    conn.commit()
    conn.close()

def buscar_registros_df():
    inicializar_banco_seguro()
    conn = sqlite3.connect('registro_presenca.db')
    c = conn.cursor()
    c.execute("PRAGMA table_info(frequencia)")
    colunas = [col[1] for col in c.fetchall()]
    
    coluna_busca = "nome_esc" if "nome_esc" in colunas else "nome_escolta"
    query = f"SELECT encarregado, localidade, balsa, {coluna_busca}, data, hora, observacao FROM frequencia"
    
    df = pd.read_sql_query(query, conn)
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
# BLOCO IV: CADASTRO E CONTROLE DE ACESSO (7 USUÁRIOS CORRIGIDOS)
###############################################################################
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

# CORREÇÃO CRÍTICA: Todas as chaves agora estão estritamente em letras minúsculas 
# para bater perfeitamente com a validação do login sem travar.
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
    st.subheader("⚡ CONTROLE DE ACESSO - OPERAÇÃO")
    usuario = st.text_input("Usuário / Credencial").strip().lower()
    senha = st.text_input("Senha", type="password")
    
    if st.button("Autenticar"):
        if usuario in USUARIOS_VALIDOS and str(USUARIOS_VALIDOS[usuario]) == str(senha):
            st.session_state['logado'] = True
            st.session_state['usuario_atual'] = usuario
            st.rerun()
        else:
            st.error("Credenciais incorretas ou operador não autorizado.")


###############################################################################
# BLOCO V: FORMULÁRIO DE CADASTRO DE FREQUÊNCIA
###############################################################################
def tela_sistema():
    carregar_css_com_fundo()
    st.title("🛡️ Painel de Segurança e Frequência")
    st.write(f"Operador Ativo: **{st.session_state['usuario_atual'].upper()}**")
    
    if st.button("Finalizar Turno (Logout)"):
        st.session_state['logado'] = False
        st.rerun()
        
    st.markdown("---")
    st.subheader("✍️ Nova Conferência de Frequência")
    
    url_escolta_esquerda = "https://images.unsplash.com/photo-1579202673506-ca3ce28943ef?q=80&w=300&auto=format&fit=crop"
    url_escolta_direita = "https://images.unsplash.com/photo-1540910419892-4a36d2c3266c?q=80&w=300&auto=format&fit=crop"
    
    col_lateral_esq, col_central_painel, col_lateral_dir = st.columns([1, 4, 1])
    
    with col_lateral_esq:
        st.image(url_escolta_esquerda, use_container_width=True)
        
    with col_lateral_dir:
        st.image(url_escolta_direita, use_container_width=True)
        
    with col_central_painel:
        lista_localidades = ["MIRITITUBA", "SANTARÉM", "BELÉM", "MANAUS", "TROMBETAS", "JURUTIR", "PORTO VELHO", "NOVO REMANSO"]
        fuso_horario = dt.timezone(dt.timedelta(hours=-3))
        agora_local = datetime.now(fuso_horario)
        
        with st.form(key='form_registro'):
            c1, c2 = st.columns(2)
            with c1:
                encarregado_input = st.text_input("Encarregado", value=st.session_state['usuario_atual'].upper())
                localidade = st.selectbox("Localidade", options=lista_localidades)
                balsa_input = st.text_input("Balsa")
            with c2:
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


###############################################################################
# BLOCO VI: HISTÓRICO DE FREQUÊNCIA (CORRIGIDO CONTRA QUEDAS)
###############################################################################
    st.markdown("---")
    st.subheader("📊 Histórico de Frequência Recente")
    
    if st.session_state['usuario_atual'] == 'admin':
        if st.button("⚠️ Redefinir Banco de Dados (Limpar Histórico Completo)"):
            conn = sqlite3.connect('registro_presenca.db')
            c = conn.cursor()
            c.execute("DROP TABLE IF EXISTS frequencia")
            conn.commit()
            conn.close()
            # CORREÇÃO CRÍTICA: Força a recriação imediata da tabela para evitar o erro de sumir tudo na tela
            inicializar_banco_seguro()
            st.success("Banco de dados limpo e reiniciado com segurança!")
            st.rerun()
            
    try:
        df_registros = buscar_registros_df()
        if not df_registros.empty:
            st.dataframe(df_registros, use_container_width=True)
            
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
            st.info("Nenhum registro de frequência encontrado até o momento.")
    except Exception as e:
        st.error(f"Erro crítico ao carregar os dados salvos: {e}")


###############################################################################
# BLOCO VII: FLUXO DE EXECUÇÃO PRINCIPAL
###############################################################################
# Garante a existência da estrutura antes de carregar a tela
inicializar_banco_seguro()

if not st.session_state['logado']:
    tela_login()
else:
    tela_sistema()
