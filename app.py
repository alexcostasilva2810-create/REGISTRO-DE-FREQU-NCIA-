import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from fpdf import FPDF
from io import BytesIO

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
            nome_esc TEXT,
            data TEXT,
            hora TEXT,
            observacao TEXT
        )
    ''')
    conn.commit()
    conn.close()

def salvar_registro(encarregado, localidade, balsa, nome_esc, data, hora, observacao):
    conn = sqlite3.connect('registro_presenca.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO frequencia (encarregado, localidade, balsa, nome_esc, data, hora, observacao)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (encarregado, localidade, balsa, nome_esc, data, hora, observacao))
    conn.commit()
    conn.close()

def buscar_registros_df():
    conn = sqlite3.connect('registro_presenca.db')
    query = "SELECT encarregado, localidade, balsa, nome_esc, data, hora, observacao FROM frequencia"
    df = pd.read_sql_query(query, conn)
    conn.close()
    df.columns = ["Encarregado", "Localidade", "Balsa", "Nome do Esc.", "Data", "Hora", "Observação"]
    return df

# Inicializa o banco de dados ao abrir o app
iniciar_bd()

# --- FUNÇÃO CORRETA PARA GERAR PDF EM MEMÓRIA ---
def gerar_pdf(df):
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    
    # Título do PDF
    pdf.cell(0, 10, "Relatorio de Frequencia e Presenca", ln=True, align="C")
    pdf.ln(10)
    
    # Cabeçalho da Tabela
    pdf.set_font("Helvetica", "B", 10)
    col_larguras = [35, 35, 30, 55, 25, 25, 75]
    colunas = list(df.columns)
    
    for i, col in enumerate(colunas):
        pdf.cell(col_larguras[i], 8, col, border=1, align="C")
    pdf.ln()
    
    # Dados da Tabela
    pdf.set_font("Helvetica", "", 9)
    for _, row in df.iterrows():
        for i, col in enumerate(colunas):
            texto = str(row[col]).encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(col_larguras[i], 8, texto, border=1, align="L" if i == 6 else "C")
        pdf.ln()
        
    # Método seguro: Envia para um buffer de Bytes em vez de retornar direto
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
    st.title("📋 Sistema de Registro de Presença")
    st.write(f"Conectado como: **{st.session_state['usuario_atual']}**")
    
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
    
    with st.form(key='form_registro', clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            encarregado = st.text_input("Encarregado", value=st.session_state['usuario_atual'])
            localidade = st.selectbox("Localidade", options=lista_localidades)
            balsa = st.text_input("Balsa")
            
        with col2:
            nome_esc = st.text_input("Nome do Esc.")
            data_atual = st.date_input("Data", datetime.now().date(), format="DD/MM/YYYY")
            hora_atual = st.time_input("Hora", datetime.now().time())
            
        observacao = st.text_area("Observação")
            
        botao_enviar = st.form_submit_button("Registrar Presença")
        
        if botao_enviar:
            if balsa and nome_esc:
                data_str = data_atual.strftime("%d/%m/%Y")
                hora_str = hora_atual.strftime("%H:%M")
                
                salvar_registro(encarregado, localidade, balsa, nome_esc, data_str, hora_str, observacao)
                st.success("✅ Registro salvo com sucesso!")
                st.rerun()
            else:
                st.error("⚠️ Por favor, preencha os campos obrigatórios (Balsa e Nome do Esc.).")

    st.markdown("---")
    
    # Visualização da Tabela de Registros
    st.subheader("📊 Histórico de Frequência")
    
    # Botão de Reset para o Administrador limpar lixos de tabelas anteriores
    if st.session_state['usuario_atual'] == 'admin':
        if st.button("⚠️ Limpar Histórico Antigo (Apagar Tabela/Reset)"):
            conn = sqlite3.connect('registro_presenca.db')
            c = conn.cursor()
            c.execute("DROP TABLE IF EXISTS frequencia")
            conn.commit()
            conn.close()
            iniciar_bd()
            st.warning("O banco de dados foi resetado para corrigir as colunas!")
            st.rerun()
            
    df_registros = buscar_registros_df()
    
    if not df_registros.empty:
        st.dataframe(df_registros, use_container_width=True)
        
        # PAINEL DO ADMINISTRADOR - DOWNLOAD DO PDF CORRIGIDO
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
