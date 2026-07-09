import streamlit as st
import sqlite3
from datetime import datetime

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
def iniciar_bd():
    conn = sqlite3.connect('registro_presenca.db')
    c = conn.cursor()
    # Cria a tabela caso ela não exista
    c.execute('''
        CREATE TABLE IF NOT EXISTS frequencia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            encarregado TEXT,
            balsa TEXT,
            nome_esc TEXT,
            data TEXT,
            hora TEXT,
            observacao TEXT
        )
    ''')
    conn.commit()
    conn.close()

def salvar_registro(encarregado, balsa, nome_esc, data, hora, observacao):
    conn = sqlite3.connect('registro_presenca.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO frequencia (encarregado, balsa, nome_esc, data, hora, observacao)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (encarregado, balsa, nome_esc, data, hora, observacao))
    conn.commit()
    conn.close()

def buscar_registros():
    conn = sqlite3.connect('registro_presenca.db')
    c = conn.cursor()
    c.execute("SELECT encarregado, balsa, nome_esc, data, hora, observacao FROM frequencia")
    dados = c.fetchall()
    conn.close()
    return dados

# Inicializa o banco de dados ao abrir o app
iniciar_bd()

# --- CONTROLE DE SESSÃO (LOGIN) ---
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

# Usuários simulados (em produção, use métodos mais seguros)
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
    
    with st.form(key='form_registro', clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # Pega o nome do usuário logado automaticamente ou permite digitação
            encarregado = st.text_input("Encarregado", value=st.session_state['usuario_atual'])
            balsa = st.text_input("Balsa")
            nome_esc = st.text_input("Nome do Esc.")
            
        with col2:
            data_atual = st.date_input("Data", datetime.now().date())
            hora_atual = st.time_input("Hora", datetime.now().time())
            observacao = st.text_area("Observação")
            
        botao_enviar = st.form_submit_button("Registrar Presença")
        
        if botao_enviar:
            if balsa and nome_esc: # Validação simples para campos obrigatórios
                # Converte data e hora para string para salvar no banco
                data_str = data_atual.strftime("%d/%m/%Y")
                hora_str = hora_atual.strftime("%H:%M:%S")
                
                salvar_registro(encarregado, balsa, nome_esc, data_str, hora_str, observacao)
                st.success("✅ Registro salvo com sucesso!")
            else:
                st.error("⚠️ Por favor, preencha os campos obrigatórios (Balsa e Nome do Esc.).")

    st.markdown("---")
    
    # Visualização da Tabela de Registros
    st.subheader("📊 Histórico de Frequência")
    registros = buscar_registros()
    
    if registros:
        # Exibe os dados em formato de tabela interativa do Streamlit
        colunas = ["Encarregado", "Balsa", "Nome do Esc.", "Data", "Hora", "Observação"]
        st.dataframe(registros, column_config={i: col for i, col in enumerate(colunas)}, use_container_width=True)
    else:
        st.info("Nenhum registro encontrado até o momento.")

# --- FLUXO DA APLICAÇÃO ---
if not st.session_state['logado']:
    tela_login()
else:
    tela_sistema()
