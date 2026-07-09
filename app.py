import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import datetime as dt
from fpdf import FPDF
from io import BytesIO

# --- CONFIGURAÇÃO VISUAL (CSS COM IMAGEM DE FUNDO PORTUÁRIO ONLINE) ---
def carregar_css_com_fundo():
    # Usando uma imagem profissional de operação portuária via URL pública confiável
    url_imagem = "https://images.unsplash.com/photo-1578575437130-527eed3abbec?q=80&w=1920&auto=format&fit=crop"
    
    css_string = f"""
    <style>
    .stApp {{
        background-image: url("{url_imagem}");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}

    /* Caixa semitransparente para proteger o texto e dar excelente leitura */
    h1, h2, h3, p, .stMarkdown, div[data-baseweb="select"] {{
        background-color: rgba(255, 255, 255, 0.90);
        padding: 6px 12px;
        border-radius: 6px;
        color: #1E293B !important;
    }}
    
    /* Inputs totalmente visíveis */
    .stTextInput>div>div>input, .stForm {{
        background-color: white !important;
    }}
    
    /* Estilização da tabela */
    [data-testid="stDataFrame"] {{
        background-color: rgba(255, 255, 255, 0.95) !important;
        border-radius: 6px;
        padding: 5px;
    }}
    </style>
    """
    st.markdown(css_string, unsafe_allow_html=True)

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
def iniciar_bd():
    conn = sqlite3.connect('registro_presenca.db')
    c = conn.cursor()
    # Criando a tabela garantindo a coluna correta
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
    try:
        query = "SELECT encarregado, localidade, balsa, nome_escolta, data, hora, observacao FROM frequencia"
        df = pd.read_sql_query(query, conn)
        df.columns = ["Encarregado", "Localidade", "Balsa", "Nome do Escolta", "Data", "Hora", "Observação"]
    except Exception:
        # CASO A TABELA ANTIGA ESTEJA TRAVANDO: Tenta ler com o nome antigo para não quebrar a tela
        query = "SELECT encarregado, localidade, balsa, nome_esc, data, hora, observacao FROM frequencia"
        df = pd.read_sql_query(query, conn)
        df.columns = ["Encarregado", "Localidade", "Balsa", "Nome do Escolta", "Data", "Hora", "Observação"]
    finally:
        conn.close()
    return df

# Inicializa o banco de dados
iniciar_bd()

# --- FUNÇÃO PARA GERAR PDF ---
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

# --- CONTROLE DE SESSÃO (LOGIN) ---
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

USUARIOS_VALIDOS = {
    "admin": "1234",
    "supervisor": "senha123"
}

def tela_login():
    carregar_css_com_fundo()
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

# --- TELA PRINCIPAL ---
def tela_sistema():
    carregar_css_com_fundo()
    st.title("📋 Sistema de Registro de Presença")
    st.write(f"Conectado como: **{st.session_state['usuario_atual'].upper()}**")
    
    if st.button("Sair / Logout"):
        st.session_state['logado'] = False
        st.rerun()
        
    st.markdown("---")
    
    st.subheader("✍️ Nova Conferência de Frequência")
    lista_localidades = ["MIRITITUBA", "SANTARÉM", "BELÉM", "MANAUS", "TROMBETAS", "JURUTIR", "PORTO VELHO", "NOVO REMANSO"]
    
    fuso_horario = dt.timezone(dt.timedelta(hours=-3))
    agora_local = datetime.now(fuso_horario)
    
    with st.form(key='form_registro'):
        col1, col2 = st.columns(2)
        with col1:
            encarregado_input = st.text_input("Encarregado", value=st.session_state['usuario_atual'])
            localidade = st.selectbox("Localidade", options=lista_localidades)
            balsa_input = st.text_input("Balsa")
        with col2:
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
    st.subheader("📊 Histórico de Frequência")
    
    # IMPORTANTE: Botão para forçar a correção das colunas no servidor remoto
    if st.session_state['usuario_atual'] == 'admin':
        if st.button("🔄 Corrigir e Sincronizar Tabelas (Reset Necessário)"):
            conn = sqlite3.connect('registro_presenca.db')
            c = conn.cursor()
            c.execute("DROP TABLE IF EXISTS frequencia")
            conn.commit()
            conn.close()
            iniciar_bd()
            st.warning("Estrutura atualizada com sucesso!")
            st.rerun()
            
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
        st.info("Nenhum registro encontrado até o momento.")

# --- FLUXO ---
if not st.session_state['logado']:
    tela_login()
else:
    tela_sistema()
