import streamlit as st
import sqlite3
from datetime import datetime

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
def iniciar_bd():
    conn = sqlite3.connect('registro_presenca.db')
    c = conn.cursor()
    # Cria a tabela caso ela não exista (incluindo a coluna 'localidade')
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

def buscar_registros():
    conn = sqlite3.connect('registro_presenca.db')
    c = conn.cursor()
    c.execute("SELECT encarregado, localidade, balsa, nome_esc, data, hora, observacao FROM frequencia")
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
    
    # Lista de localidades solicitadas
    lista_localidades = [
        "MIRITITUBA",
        "SANTARÉM",
        "BELÉM",
        "MANAUS",
        "TROMBETAS",
        "JURUTIR",
        "PORTO VELHO",
        "NOVO REMANSO"
    ]
    
    with st.form(key='form_registro', clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            encarregado = st.text_input("Encarregado", value=st.session_state['usuario_atual'])
            localidade = st.selectbox("Localidade", options=lista_localidades)
            balsa = st.text_input("Balsa")
            
        with col2:
            nome_esc = st.text_input("Nome do Esc.")
            # ADICIONADO: format="DD/MM/YYYY" para exibir no padrão brasileiro
            data_atual = st.date_input("Data", datetime.now().date(), format="DD/MM/YYYY")
            hora_atual = st.time_input("Hora", datetime.now().time())
            
        observacao = st.text_area("Observação")
            
        botao_enviar = st.form_submit_button("Registrar Presença")
        
        if botao_enviar:
            if balsa and nome_esc: # Validação simples para campos obrigatórios
