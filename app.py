import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import datetime as dt
from fpdf import FPDF
from io import BytesIO

# --- CONFIGURAÇÃO VISUAL (CSS COM IMAGEM DE PESSOAS EM OPERAÇÃO PORTUÁRIA) ---
def carregar_css_com_fundo():
    # Imagem focada em trabalhadores/equipe em operação portuária logística
    url_imagem = "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?q=80&w=1200&auto=format&fit=crop"
    
    css_string = f"""
    <style>
    .stApp {{
        background-image: url("{url_imagem}");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
        background-position: center;
    }}

    /* Container semitransparente reforçado para garantir leitura absoluta das mensagens de erro ou texto */
    h1, h2, h3, p, .stMarkdown, div[data-baseweb="select"], .stAlert {{
        background-color: rgba(255, 255, 255, 0.94);
        padding: 8px 14px;
        border-radius: 6px;
        color: #0F172A !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    
    /* Cobertura para blocos de exceção/tracebacks do Streamlit ficarem legíveis */
    .stException {{
        background-color: rgba(255, 233, 233, 0.96) !important;
        border: 1px solid #EF4444 !important;
        border-radius: 6px;
        padding: 15px;
    }}
    
    /* Inputs visíveis */
    .stTextInput>div>div>input, .stForm {{
        background-color: white !important;
    }}
    
    /* Estilização da tabela */
    [data-testid="stDataFrame"] {{
        background-color: rgba(255, 255, 255, 0.96) !important;
        border-radius: 6px;
        padding: 5px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }}
    </style>
    """
    st.markdown(css_string, unsafe_allow_html=True)

# --- CONFIGURAÇÃO E CORREÇÃO AUTOMÁTICA DO BANCO DE DADOS ---
def iniciar_e_atualizar_bd():
    conn = sqlite3.connect('registro_presenca.db')
    c = conn.cursor()
    
    # 1. Cria a tabela se não existir
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
    
    # 2. Correção Inteligente: Verifica se a coluna antiga 'nome_esc' ainda existe e migra para 'nome_escolta'
    c.execute("PRAGMA table_info(frequencia)")
    colunas = [col[1] for col in c.fetchall()]
    
    if "nome_esc" in colunas and "nome_escolta" not in colunas:
        try:
            c.execute("ALTER TABLE frequencia RENAME COLUMN nome_esc TO nome_escolta")
        except Exception:
            pass
            
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
        # Tenta a busca padrão estruturada
        query = "SELECT encarregado, localidade, balsa, nome_escolta, data, hora, observacao FROM frequencia"
        df = pd.read_sql_query(query, conn)
    except Exception:
        # Fallback de segurança absoluto caso ocorra divergência residual
        query = "SELECT * FROM frequencia"
        df = pd.read_sql_query(query, conn)
        # Remove ID se ele vier na consulta genérica para mapear corretamente
        if 'id' in df.columns:
            df = df.drop(columns=['id'])
            
    conn.close()
    
    # Força a nomeação amigável e correta das colunas na interface
    df.columns = ["Encarregado", "Localidade", "Balsa", "Nome do Escolta", "Data", "Hora", "Observação"]
    return df

# Executa o sincronismo automático de tabelas
iniciar_e_atualizar_bd()

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
    
    # Painel de controle estrutural caso queira redefinir a tabela do zero
    if st.session_state['usuario_atual'] == 'admin':
        if st.button("⚠️ Redefinir Banco de Dados (Limpar Histórico Completo)"):
            conn = sqlite3.connect('registro_presenca.db')
            c = conn.cursor()
            c.execute("DROP TABLE IF EXISTS frequencia")
            conn.commit()
            conn.close()
            iniciar_e_atualizar_bd()
            st.success("Tabela recriada com sucesso com as novas colunas!")
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

# --- FLUXO PRINCIPAL ---
if not st.session_state['logado']:
    tela_login()
else:
    tela_sistema()
