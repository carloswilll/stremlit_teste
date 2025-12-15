import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Dashboard Cartola 2025", layout="wide")

# 🎨 Estilo customizado para roxo nos multiselects e modo escuro/claro
st.markdown("""
    <style>
    .stMultiSelect [data-baseweb="select"] span {
        background-color: #7e57c2 !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# SIDEBAR
st.sidebar.title("⚙️ Filtros e Configurações")

# Carregar dados da API
@st.cache_data(show_spinner="Carregando dados da API...")
def carregar_dados_api():
    url_scouts = 'https://api.cartola.globo.com/atletas/mercado'
    res_scouts = requests.get(url_scouts).json()

    jogadores = res_scouts['atletas']
    clubes = res_scouts['clubes']
    posicoes = res_scouts['posicoes']

    scouts_data = []
    for jogador in jogadores:
        clube = clubes[str(jogador['clube_id'])]['nome']
        posicao = posicoes[str(jogador['posicao_id'])]['nome']
        scouts = jogador.get('scout', {})

        dados_jogador = {
            'Nome': jogador['apelido'],
            'Clube': clube,
            'Posição': posicao,
            'Preço (C$)': jogador['preco_num'],
            'Pontos Média': jogador['media_num'],
            'Partidas': jogador['jogos_num'],
        }
        dados_jogador.update(scouts)
        scouts_data.append(dados_jogador)

    df = pd.DataFrame(scouts_data)
    df.columns = df.columns.str.strip()
    return df.convert_dtypes().infer_objects()

# Título principal
df = carregar_dados_api()
df["Preço (C$)"] = pd.to_numeric(df["Preço (C$)"], errors="coerce").fillna(0.0)
df["Pontos Média"] = pd.to_numeric(df["Pontos Média"], errors="coerce").fillna(0.0)
df["Custo-Benefício"] = df["Pontos Média"] / df["Preço (C$)"].replace(0, 0.1)

# Filtros laterais dinâmicos
posicoes = df["Posição"].unique().tolist()
clubes = df["Clube"].unique().tolist()

posicao_selecionada = st.sidebar.multiselect("🧩 Posição", posicoes, default=posicoes)
clube_selecionado = st.sidebar.multiselect("🏳️ Clube", clubes, default=clubes)

preco_max = st.sidebar.slider("💰 Preço máximo (C$)", float(df["Preço (C$)"].min()), float(df["Preço (C$)"].max()), float(df["Preço (C$)"].max()))
media_max = st.sidebar.slider("📉 Pontos Média máxima", float(df["Pontos Média"].min()), float(df["Pontos Média"].max()), float(df["Pontos Média"].max()))

# 🆕 NOVO FILTRO DE PARTIDAS
partidas_min, partidas_max = st.sidebar.slider(
    "🎯 Intervalo de Partidas Jogadas",
    int(df["Partidas"].min()),
    int(df["Partidas"].max()),
    (int(df["Partidas"].min()), int(df["Partidas"].max()))
)

st.sidebar.markdown(f"🕒 Dados atualizados em: `{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}`")

# Aplicar filtros
df_filtrado = df[
    (df["Posição"].isin(posicao_selecionada)) &
    (df["Clube"].isin(clube_selecionado)) &
    (df["Preço (C$)"] <= preco_max) &
    (df["Pontos Média"] <= media_max) &
    (df["Partidas"] >= partidas_min) &
    (df["Partidas"] <= partidas_max)
].copy()

df_filtrado["Custo-Benefício"] = df_filtrado["Pontos Média"] / df_filtrado["Preço (C$)"].replace(0, 0.1)

# 🏆 Título
st.title("⚽ Top Jogadores - Cartola FC 2025")
st.markdown("Visualize os melhores jogadores da rodada com base em pontuação e custo-benefício.")

# 🔢 Painéis de Estatísticas
col_a, col_b, col_c, col_d = st.columns(4)

col_a.metric("📋 Jogadores filtrados", len(df_filtrado))
col_b.metric("🪙 Preço médio (C$)", f"{df_filtrado['Preço (C$)'].mean():.2f}")
col_c.metric("📊 Pontuação média", f"{df_filtrado['Pontos Média'].mean():.2f}")
col_d.metric("💸 Custo-Benefício médio", f"{df_filtrado['Custo-Benefício'].mean():.2f}")

# 🔝 Destaques
st.markdown("---")
st.subheader("🏅 Destaques da Rodada")
col1, col2 = st.columns(2)

with col1:
    st.markdown("🔝 **Top 10 por Pontos Média**")
    st.dataframe(df_filtrado.sort_values("Pontos Média", ascending=False).head(10), use_container_width=True, height=300)

with col2:
    st.markdown("💸 **Top 10 por Custo-Benefício**")
    st.dataframe(df_filtrado.sort_values("Custo-Benefício", ascending=False).head(10), use_container_width=True, height=300)

# 📊 Gráfico de Dispersão
st.markdown("---")
st.subheader("📊 Relação entre Preço e Pontos")
fig = px.scatter(
    df_filtrado,
    x="Preço (C$)",
    y="Pontos Média",
    color="Clube",
    hover_name="Nome",
    size_max=15,
    color_discrete_sequence=px.colors.qualitative.Safe,
    labels={"Preço (C$)": "Preço (C$)", "Pontos Média": "Pontos Média"},
)
fig.update_traces(marker=dict(size=10, opacity=0.75))
fig.update_layout(height=600, title_font_size=20)
st.plotly_chart(fig, use_container_width=True)

# 🧍 Buscar Jogador
st.markdown("---")
st.subheader("📄 Lista Completa")
nome_jogador = st.text_input("🔍 Buscar por nome do jogador", placeholder="Ex: Pedro, Hulk, Gerson...")

if nome_jogador:
    df_filtrado = df_filtrado[df_filtrado["Nome"].str.contains(nome_jogador, case=False, na=False)]

st.dataframe(df_filtrado.sort_values("Pontos Média", ascending=False), use_container_width=True, height=400)

st.caption("Desenvolvido por Carlos Willian - Cartola FC 2025")

