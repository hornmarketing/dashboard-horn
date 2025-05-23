import pandas as pd
import plotly.graph_objects as go
import gspread
import streamlit as st
import json
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Painel de Metas", layout="wide")

st.title("📊 Dashboard de Metas - Horn Agência")

# === CONEXÃO COM GOOGLE SHEETS ===
escopos = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

# Corrige o uso do segredo como dicionário
info = st.secrets["google_credentials"]
credenciais = ServiceAccountCredentials.from_json_keyfile_dict(info, escopos)

sheet_id = "1BJ6gwg0uyIg7nP3NV1CSIsCa14rrXlF-bbfOyHLC1Gg"
aba_nome = "entrada"

cliente = gspread.authorize(credenciais)
planilha = cliente.open_by_key(sheet_id)
aba = planilha.worksheet(aba_nome)
dados = aba.get_all_values()

df_raw = pd.DataFrame(dados[1:], columns=dados[0])
df_raw.columns = df_raw.columns.str.strip().str.lower()

# === LIMPEZA DOS VALORES ===
def limpar_valor(valor):
    valor = valor.strip()
    if valor in ["R$  -", "-", ""]:
        return 0.0
    return float(valor.replace("R$", "").replace(".", "").replace(",", ".").strip())

col_meses = [col for col in df_raw.columns if "-24" in col]
df_valores = df_raw[col_meses].applymap(limpar_valor).fillna(0)

# === TRATAMENTO DE DATAS ===
meses_ordenados = ['jan.-24', 'fev.-24', 'mar.-24', 'abr.-24', 'mai.-24', 'jun.-24',
                   'jul.-24', 'ago.-24', 'set.-24', 'out.-24', 'nov.-24', 'dez.-24']

# Substituir nomes para parsing
meses_formatados = [m.replace("jan.", "Jan").replace("fev.", "Feb").replace("mar.", "Mar")
                    .replace("abr.", "Apr").replace("mai.", "May").replace("jun.", "Jun")
                    .replace("jul.", "Jul").replace("ago.", "Aug").replace("set.", "Sep")
                    .replace("out.", "Oct").replace("nov.", "Nov").replace("dez.", "Dec")
                    for m in meses_ordenados]

meses_formatados = pd.to_datetime(meses_formatados, format="%b-%y").strftime("%b/%y")

# === CONSTRUÇÃO DO DATAFRAME ===
valores_mensais = df_valores[meses_ordenados].sum()
df = pd.DataFrame({
    "Mês": meses_formatados,
    "Realizado": valores_mensais.values
})
df["Acumulado"] = df["Realizado"].cumsum()

# === GRÁFICO DE LINHAS ===
fig_linha = go.Figure()
fig_linha.add_trace(go.Scatter(
    x=df["Mês"], y=[1_000_000] * len(df),
    mode="lines", name="Meta Fixa R$ 1M",
    line=dict(color="red", dash="dash", width=3)
))
fig_linha.add_trace(go.Scatter(
    x=df["Mês"], y=df["Acumulado"],
    mode="lines+markers", name="Acumulado Real",
    line=dict(color="blue", width=3)
))
fig_linha.add_trace(go.Scatter(
    x=df["Mês"], y=df["Realizado"],
    mode="lines+markers", name="Vendas no Mês",
    line=dict(color="green", dash="dot", width=2)
))
fig_linha.update_layout(
    title="📈 Vendas Acumuladas vs Meta Fixa + Vendas Mensais",
    xaxis_title="Mês", yaxis_title="Valor em R$",
    template="plotly_white"
)

# === GRÁFICO DE BARRAS ===
df_barras = df.copy()
total = df_barras["Realizado"].sum()
df_barras.loc[len(df_barras)] = ["TOTAL DO ANO", total, None]

fig_barras = go.Figure()
fig_barras.add_trace(go.Bar(
    x=df_barras["Mês"],
    y=df_barras["Realizado"],
    text=[f"R$ {v:,.0f}".replace(",", ".") if pd.notna(v) else "" for v in df_barras["Realizado"]],
    textposition="auto",
    marker_color=["green"] * (len(df_barras) - 1) + ["orange"]
))
fig_barras.update_layout(
    title="📊 Vendas por Mês + TOTAL DO ANO",
    xaxis_title="Mês", yaxis_title="Valor em R$",
    template="plotly_white"
)

# === MOSTRAR NO APP ===
st.plotly_chart(fig_linha, use_container_width=True)
st.plotly_chart(fig_barras, use_container_width=True)
