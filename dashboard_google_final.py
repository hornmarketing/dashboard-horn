
import pandas as pd
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pathlib import Path

# === CONFIGURAÇÕES ===
json_path = "dashboard-horn-0e6dfbc7b05b.json"
sheet_id = "1BJ6gwg0uyIg7nP3NV1CSIsCa14rrXlF-bbfOyHLC1Gg"
aba_nome = "entrada"
saida = "/Users/samillyteixeirafernandesferreira/Desktop/Horn Agência/"

# === CONEXÃO COM GOOGLE SHEETS ===
escopos = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credenciais = ServiceAccountCredentials.from_json_keyfile_name(json_path, escopos)
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
df_valores = df_raw[col_meses].applymap(limpar_valor)
df_valores = df_valores.fillna(0)

# === TRATAMENTO DE DATAS ===
meses_ordenados = ['jan.-24', 'fev.-24', 'mar.-24', 'abr.-24', 'mai.-24', 'jun.-24',
                   'jul.-24', 'ago.-24', 'set.-24', 'out.-24', 'nov.-24', 'dez.-24']
meses_formatados = pd.to_datetime(
    [m.replace("jan.", "jan").replace("fev.", "fev").replace("mar.", "mar")
     .replace("abr.", "abr").replace("mai.", "mai").replace("jun.", "jun")
     .replace("jul.", "jul").replace("ago.", "ago").replace("set.", "set")
     .replace("out.", "out").replace("nov.", "nov").replace("dez.", "dez")
     for m in meses_ordenados], format="%b-%y"
).strftime("%b/%y")

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
    title="Vendas Acumuladas vs Meta Fixa + Vendas Mensais",
    xaxis_title="Mês", yaxis_title="Valor em R$",
    template="plotly_white"
)

# === GRÁFICO DE BARRAS ===
df_barras = df.copy()
total = df_barras["Realizado"].sum()
df_barras.loc[len(df_barras.index)] = ["TOTAL DO ANO", total, None]

fig_barras = go.Figure()
fig_barras.add_trace(go.Bar(
    x=df_barras["Mês"],
    y=df_barras["Realizado"],
    text=[f"R$ {v:,.0f}".replace(",", ".") if pd.notna(v) else "" for v in df_barras["Realizado"]],
    textposition="auto",
    marker_color=["green"] * (len(df_barras) - 1) + ["orange"]
))

fig_barras.update_layout(
    title="Vendas por Mês + TOTAL DO ANO",
    xaxis_title="Mês", yaxis_title="Valor em R$",
    template="plotly_white"
)

# === EXPORTAÇÃO ===
Path(saida).mkdir(parents=True, exist_ok=True)
fig_linha.write_html(saida + "grafico_linha_corrigido.html")
fig_barras.write_html(saida + "grafico_coluna_corrigido.html")

print("✅ Gráficos atualizados com sucesso a partir do Google Sheets!")
