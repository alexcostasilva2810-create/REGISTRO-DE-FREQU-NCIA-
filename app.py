import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from fpdf import FPDF

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

# Inicializa o banco de dados
iniciar_bd()

# --- FUNÇÃO PARA GERAR PDF (CORRIGIDA) ---
def gerar_pdf(df):
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.set
