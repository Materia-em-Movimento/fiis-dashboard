# ==========================================
# IMPORTAÇÃO DAS BIBLIOTECAS
# ==========================================

# Permite executar várias tarefas ao mesmo tempo (multithreading)
# No nosso caso: buscar dados de vários FIIs simultaneamente
from concurrent.futures import ThreadPoolExecutor

# Biblioteca principal para criar aplicações web rápidas em Python
# Ela transforma este script em um site interativo
import streamlit as st

# Biblioteca para fazer requisições HTTP (acessar sites)
import requests

# Biblioteca para "ler" e navegar no HTML de um site
from bs4 import BeautifulSoup

# Biblioteca para manipulação de tabelas (DataFrame)
import pandas as pd


# ==========================================
# CONFIGURAÇÃO DA PÁGINA DO STREAMLIT
# ==========================================

# Define o título da aba do navegador e usa layout largo
st.set_page_config(page_title="FIIs", layout="wide")


# ==========================================
# AJUSTE DE ESPAÇAMENTO DA PÁGINA (CSS)
# ==========================================

# Streamlit tem um padding grande no topo.
# Esse CSS reduz o espaço superior para deixar o título mais próximo do topo.
st.markdown("""
<style>
.block-container {
    padding-top: 1rem;
}
</style>
""", unsafe_allow_html=True)


# Título principal da página
st.title("📈 Nossos FIIs")


# ==========================================
# BASE DE DADOS DOS FUNDOS
# ==========================================

# Lista de dicionários contendo:
# - Ticker do fundo
# - Intervalo de datas "data com"
# - Intervalo de datas de pagamento

# Esses valores são estáticos (não vêm do site)
dados_fundos = [
    {"TICKER": "EGAF11", "DATA COM": "2 - 3 - 4 - 8", "DIA PAGAMENTO": "9 - 10 - 11 - 15"},
    {"TICKER": "RZAG11", "DATA COM": "28 - 30 - 30 - 31", "DIA PAGAMENTO": "13 - 14 - 14 - 15"},
    {"TICKER": "LIFE11", "DATA COM": "28 - 30 - 30 - 31", "DIA PAGAMENTO": "6 - 7 - 7 - 8"},
    {"TICKER": "RECR11", "DATA COM": "6 - 7 - 7 - 8", "DIA PAGAMENTO": "13 - 14 - 14 - 15"},
    {"TICKER": "HSAF11", "DATA COM": "28 - 30 - 30 - 31", "DIA PAGAMENTO": "6 - 7 - 7 - 8"},
    {"TICKER": "RZTR11", "DATA COM": "28 - 30 - 30 - 31", "DIA PAGAMENTO": "6 - 7 - 7 - 8"},
    {"TICKER": "HGCR11", "DATA COM": "28 - 30 - 30 - 31", "DIA PAGAMENTO": "13 - 14 - 14 - 15"},
    {"TICKER": "CPTS11", "DATA COM": "10 - 11 - 11 - 12", "DIA PAGAMENTO": "17 - 18 - 18 - 21"},
    {"TICKER": "PSEC11", "DATA COM": "8 - 8 - 9 - 9", "DIA PAGAMENTO": "15 - 16 - 16 - 18"},
    {"TICKER": "PCIP11", "DATA COM": "8 - 8 - 9 - 9", "DIA PAGAMENTO": "15 - 16 - 16 - 18"},
    {"TICKER": "KNSC11", "DATA COM": "28 - 30 - 30 - 31", "DIA PAGAMENTO": "11 - 12 - 12 - 13"},
    {"TICKER": "MXRF11", "DATA COM": "28 - 30 - 30 - 31", "DIA PAGAMENTO": "13 - 14 - 14 - 15"},
    {"TICKER": "RBRR11", "DATA COM": "9 - 10 - 10 - 11", "DIA PAGAMENTO": "16 - 17 - 17 - 19"},
    {"TICKER": "RBVA11", "DATA COM": "28 - 30 - 30 - 31", "DIA PAGAMENTO": "13 - 14 - 15 - 15"},
]


# ==========================================
# FUNÇÃO PARA SIMPLIFICAR INTERVALOS
# ==========================================

# Exemplo:
# "2 - 3 - 4 - 8"  →  "2 - 8"

def formatar_intervalo(texto):

    # separa os números usando "-"
    partes = [int(x.strip()) for x in texto.split("-")]

    # pega o menor e maior valor
    return f"{min(partes)} - {max(partes)}"


# ==========================================
# FUNÇÃO PARA CONVERTER TEXTO EM NÚMERO
# ==========================================

# Exemplo:
# "1.234,56" → 1234.56

def converter_numero(texto):
    return float(texto.replace(".", "").replace(",", "."))


# ==========================================
# FUNÇÃO PRINCIPAL DE SCRAPING
# ==========================================

# @st.cache_data guarda o resultado na memória
# TTL=600 → cache dura 10 minutos

@st.cache_data(ttl=600)
def obter_dados_fii(ticker):

    # monta a URL do fundo
    url = f"https://investidor10.com.br/fiis/{ticker.lower()}/"

    # headers ajudam a evitar bloqueio do site
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "pt-BR"
    }

    try:

        # acessa o site
        resp = requests.get(url, headers=headers, timeout=10)

        # transforma HTML em objeto navegável
        soup = BeautifulSoup(resp.text, "html.parser")

        # ==================================
        # EXTRAÇÃO DO PREÇO DA COTA
        # ==================================

        span = soup.find("span", class_="value")

        preco = None

        if span:
            texto = span.text.strip()

            # limpa formatação monetária
            texto = texto.replace("R$", "").replace(".", "").replace(",", ".")

            preco = float(texto)

        # ==================================
        # EXTRAÇÃO DOS DIVIDENDOS
        # ==================================

        elementos = soup.find_all(class_="text-center")

        soma = 0
        contador = 0

        # percorre posições específicas da tabela
        for i in range(16, 31):

            if i >= len(elementos):
                break

            texto = elementos[i].text.strip()

            # ignora datas
            if "/" not in texto:

                try:

                    valor = converter_numero(texto)

                    soma += valor
                    contador += 1

                    if contador == 4:
                        break

                except:
                    pass

        # média dos 4 últimos dividendos
        div_media = soma / 4 if contador == 4 else None

        return preco, div_media

    except:

        # se der erro na requisição
        return None, None


# ==========================================
# BOTÃO PARA LIMPAR CACHE
# ==========================================

# if st.button("🧹 Limpar cache"):
#     st.cache_data.clear()


# ==========================================
# BOTÃO PRINCIPAL DO APP
# ==========================================

if st.button("🔄 Atualizar valores"):

    # função que processa um fundo individual
    def processar_fundo(fundo):

        ticker = fundo["TICKER"]

        # busca dados no site
        preco, div = obter_dados_fii(ticker)

        # calcula ROI
        if preco and div:
            roi = round(div / preco * 100, 2)
        else:
            roi = None

        # retorna estrutura de dados
        return {
            "TICKER": ticker,
            "PREÇO": preco,
            "DIV": div,
            "ROI": roi,
            "D. COM": formatar_intervalo(fundo["DATA COM"]),
            "D. PAG.": formatar_intervalo(fundo["DIA PAGAMENTO"])
        }


    # ==================================
    # EXECUÇÃO PARALELA
    # ==================================

    # Processa vários FIIs ao mesmo tempo
    with ThreadPoolExecutor() as executor:
        resultado = list(executor.map(processar_fundo, dados_fundos))


    # transforma lista em tabela pandas
    df = pd.DataFrame(resultado)


    # ordena pelo maior ROI
    df = df.sort_values(by="ROI", ascending=False, na_position="last")

    # ==================================
    # EXIBIÇÃO DA TABELA NO APP
    # ==================================

    df = df.sort_values(by="ROI", ascending=False, na_position="last").reset_index(drop=True)


    def zebra_linhas(row):
        if row.name % 2 == 0:
            return ['background-color: #2f5093'] * len(row)
        else:
            return [''] * len(row)


    df_estilado = (
        df.style
        .apply(zebra_linhas, axis=1)
        #transforma em valor numérico
        .format({
            "PREÇO": "R$ {:.2f}",
            "DIV": "{:.3f}",
            "ROI": "{:.2f}%"
        })
        #era pra configurar cabeçalho, mas não está funcionando
        .set_table_styles([
            {
                "selector": "th",
                "props": [
                    ("background-color", "black"),
                    ("color", "white"),
                    ("font-weight", "bold")
                ]
            }
        ])
    )

    st.dataframe(
        df_estilado,
        use_container_width=True,
        hide_index=True,
        height=525
    )

# mensagem padrão antes da atualização
else:
    st.info("Clique no botão para atualizar preços e dividendos.")


