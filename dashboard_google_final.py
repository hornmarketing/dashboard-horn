import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import base64
from pathlib import Path

# === CONFIGURAÇÕES ===
st.set_page_config(page_title=" 🤟🏽Dashboard Horn Marketing 2024", page_icon="🔥", layout="wide")
saida = "./"
sheet_id = "1BJ6gwg0uyIg7nP3NV1CSIsCa14rrXlF-bbfOyHLC1Gg"
aba_nome = "entrada"
escopos = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# === LOGO ===
def exibir_logo():
    file_path = "LOGO_HORN.png"
    try:
        with open(file_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
            st.markdown(
                f"<div style='text-align:center; margin-bottom: 1rem;'><img src='data:image/png;base64,{encoded}' width='200'/></div>",
                unsafe_allow_html=True
            )
    except FileNotFoundError:
        st.warning("Logo não encontrada. Suba o arquivo LOGO_HORN.png para exibir.")

exibir_logo()

# === CABEÇALHO ===
st.markdown("""
    <h1 style='text-align: center; color: #060D38;'> Dashboard de Metas - Horn Agência</h1>
    <hr style='border: 1px solid #FF9100;'/>""", unsafe_allow_html=True)

# === CONEXÃO COM GOOGLE SHEETS ===
info = st.secrets["google_credentials"]
credenciais = ServiceAccountCredentials.from_json_keyfile_dict(info, escopos)
cliente = gspread.authorize(credenciais)
planilha = cliente.open_by_key(sheet_id)
aba = planilha.worksheet(aba_nome)
dados = aba.get_all_values()

# === LIMPEZA ===
df_raw = pd.DataFrame(dados[1:], columns=dados[0])
df_raw.columns = df_raw.columns.str.strip().str.lower()

def limpar_valor(valor):
    valor = valor.strip()
    if valor in ["R$  -", "-", ""]:
        return 0.0
    return float(valor.replace("R$", "").replace(".", "").replace(",", "."))

col_meses = [col for col in df_raw.columns if "-24" in col]
df_valores = df_raw[col_meses].applymap(limpar_valor).fillna(0)

# === DATAS ===
meses_ordenados = ['jan.-24', 'fev.-24', 'mar.-24', 'abr.-24', 'mai.-24', 'jun.-24',
                   'jul.-24', 'ago.-24', 'set.-24', 'out.-24', 'nov.-24', 'dez.-24']

meses_em_en = {
    'jan.-24': 'Jan-24', 'fev.-24': 'Feb-24', 'mar.-24': 'Mar-24',
    'abr.-24': 'Apr-24', 'mai.-24': 'May-24', 'jun.-24': 'Jun-24',
    'jul.-24': 'Jul-24', 'ago.-24': 'Aug-24', 'set.-24': 'Sep-24',
    'out.-24': 'Oct-24', 'nov.-24': 'Nov-24', 'dez.-24': 'Dec-24'
}

meses_formatados = [meses_em_en[m] for m in meses_ordenados]
meses_formatados = pd.to_datetime(meses_formatados, format="%b-%y").strftime("%b/%y")

# === PREPARAR DADOS PARA GRÁFICOS ===
valores_mensais = df_valores[meses_ordenados].sum()
df = pd.DataFrame({
    "Mês": meses_formatados,
    "Realizado": valores_mensais.values
})
df["Acumulado"] = df["Realizado"].cumsum()

# === KPIs ===
total_anual = df["Realizado"].sum()
clientes_ativos = df_raw["cliente"].nunique()
tipos_servico = df_raw["tipo de serviço"].nunique()

st.markdown("""
<div style='display: flex; justify-content: space-around; margin: 1rem 0;'>
    <div style='background-color:#060D38; padding: 1rem; border-radius: 10px; color: white;'>
        <h3>Total Vendido</h3><h2>R$ {:,.0f}</h2>
    </div>
    <div style='background-color:#FF9100; padding: 1rem; border-radius: 10px; color: white;'>
        <h3>Clientes Ativos</h3><h2>{}</h2>
    </div>
    <div style='background-color:#060D38; padding: 1rem; border-radius: 10px; color: white;'>
        <h3>Tipos de Serviço</h3><h2>{}</h2>
    </div>
</div>
""".format(total_anual, clientes_ativos, tipos_servico), unsafe_allow_html=True)

# === GRÁFICO DE LINHAS ===
fig_linha = go.Figure()
fig_linha.add_trace(go.Scatter(x=df["Mês"], y=[1_000_000] * len(df),
    mode="lines", name="Meta Fixa R$ 1M", line=dict(color="#FF9100", dash="dash", width=3)))
fig_linha.add_trace(go.Scatter(x=df["Mês"], y=df["Acumulado"],
    mode="lines+markers", name="Acumulado Real", line=dict(color="#060D38", width=3)))
fig_linha.add_trace(go.Scatter(x=df["Mês"], y=df["Realizado"],
    mode="lines+markers", name="Vendas no Mês", line=dict(color="gray", dash="dot", width=2)))
fig_linha.update_layout(title="Vendas Acumuladas vs Meta Fixa + Vendas Mensais",
    xaxis_title="Mês", yaxis_title="Valor em R$", template="plotly_white")

# === GRÁFICO DE BARRAS ===
df_barras = df.copy()
df_barras.loc[len(df_barras.index)] = ["TOTAL DO ANO", df["Realizado"].sum(), None]
fig_barras = go.Figure()
fig_barras.add_trace(go.Bar(
    x=df_barras["Mês"],
    y=df_barras["Realizado"],
    text=[f"R$ {v:,.0f}".replace(",", ".") if pd.notna(v) else "" for v in df_barras["Realizado"]],
    textposition="auto",
    marker_color=["#060D38"] * (len(df_barras)-1) + ["#FF9100"]
))
fig_barras.update_layout(title="Vendas por Mês + Total Anual",
    xaxis_title="Mês", yaxis_title="Valor em R$", template="plotly_white")

# === MOSTRAR NO STREAMLIT ===
st.plotly_chart(fig_linha, use_container_width=True)
st.plotly_chart(fig_barras, use_container_width=True)

# === RODAPÉ ===
st.markdown("""
    <hr style='border: 0.5px solid #FF9100;' />
    <p style='text-align: center; color: #888;'>Powered by Horn Marketing © 2025</p>
""", unsafe_allow_html=True)
