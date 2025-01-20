import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da fonte
fonte_texto = dict(
    family="Arial, serif",
    size=14,
    color="white"
)

fonte_titulo = dict(
    size=24,
    family="Old English Text MT, serif",
    color="white"
)

legenda = dict(
    title="Legenda",
    x=1,
    y=1,
    bgcolor="black",
    bordercolor="white",
    borderwidth=1
)

palette_colors = px.colors.sequential.Plasma

# Configuração da página
st.set_page_config(page_title="Análise de Leads", layout="wide", initial_sidebar_state="expanded")

# Título principal
st.title("📊 Dashboard de Leads")
st.write('=-=-=-=-=-=-=-=-=-=-=-=')

# Upload do arquivo
st.sidebar.header("Upload do Arquivo")
uploaded_file = st.sidebar.file_uploader("Solte o arquivo do hubspot aqui", type=["csv"])

if uploaded_file is not None:
    # Lê os dados
    base = pd.read_csv(uploaded_file)

    # Renomeia as colunas
    base.columns = ['id', 'cliente', 'etapa', 'origem', 'convenio', 'comissao_total',
                    'valor_pago', 'tipo_campanha', 'tag_campanha', 'telefone', 'cpf',
                    'vendedor_proprietario']

    # Limpa os dados
    base['etapa'] = base['etapa'].astype(str).str.replace(r" \( Pipeline de Vendas\)", "", regex=True)
    base['etapa'] = base['etapa'].astype(str).str.replace(r" \(Pipeline de Disparos?\)", "", regex=True).str.upper()
    base['cpf'] = base['cpf'].astype(str).str.replace(".0", "")
    base = base.loc[~base['origem'].isin(['HYPERFLOW', 'META - Whatsapp', 'TALLOS'])]
    bins = [0, 499, 800, 1200, 1500, float('inf')]
    labels = ['0-499', '500-800', '800-1200', '1200-1500', '1800+']
    base['faixa_comissao'] = pd.cut(base['comissao_total'], bins=bins, labels=labels, right=True, include_lowest=True)


    # Filtros na barra lateral
    st.sidebar.header("Filtros")
    etapas = st.sidebar.multiselect("Selecione a(s) etapa(s):", options=base['etapa'].unique(), default=base['etapa'].unique())
    tipo_campanha = st.sidebar.multiselect("Selecione o(s) tipo(s) de campanha:", options=base['tipo_campanha'].unique(), default=base['tipo_campanha'].unique())
    vendedores = st.sidebar.multiselect("Selecione o(s) vendedor(es):", options=base['vendedor_proprietario'].unique(), default=base['vendedor_proprietario'].unique())

    # Filtra os dados com base nos filtros selecionados
    base_filtrada = base[
        (base['etapa'].isin(etapas)) &
        (base['tipo_campanha'].isin(tipo_campanha)) &
        (base['vendedor_proprietario'].isin(vendedores))
    ]

    # Gera gráfico de leads por origem
    st.subheader("Quantidade de leads gerados")
    leads_por_origem = base_filtrada.groupby("origem")['id'].size().reset_index(name="quantidade").sort_values(by='quantidade', ascending=False)
    leads_por_origem = leads_por_origem.loc[leads_por_origem['quantidade'] > 2]

    if not leads_por_origem.empty:
        fig = px.bar(
            leads_por_origem,
            x='quantidade',
            y='origem',
            color='origem',
            barmode='group',
            color_discrete_sequence=palette_colors
        )
        fig.update_layout(
            title=dict(
                text="",
                x=0.5,
                xanchor='center',
                yanchor='top',
                font=fonte_titulo
            ),
            xaxis_title="Quantidade",
            yaxis_title="",
            font=fonte_texto,
            width=1080,
            height=500,
            template='plotly_dark',
            margin=dict(l=10, r=0, t=50, b=50),
            legend=legenda,
        )
        # Envolve o gráfico em uma div com classe para borda
        st.plotly_chart(fig, use_container_width=True)
        st.write("---")



        # Grafico 2:
        st.subheader("Distribuição das Etapas por Origem")
        distrib_funil_por_origem = base.groupby(['origem', 'etapa'])['id'].size().reset_index(name='quantidade')
        totais_por_origem = distrib_funil_por_origem.groupby('origem')['quantidade'].sum()
        origens_validas = totais_por_origem[totais_por_origem > 5].index
        distrib_funil_por_origem_filtrado = distrib_funil_por_origem[distrib_funil_por_origem['origem'].isin(origens_validas)]

        fig = px.bar(
            distrib_funil_por_origem_filtrado, 
            x='origem',               # Agrupamento no eixo X por origem
            y='quantidade',           # Quantidade no eixo Y
            color='etapa',            # Diferenciar pelas etapas (barra agrupada por cor)
            barmode='group',          # Configuração para barras agrupadas
            labels={
                'origem': 'Origem dos Leads',
                'quantidade': 'Quantidade',
                'etapa': 'Etapas do Funil'
            },
            color_discrete_sequence=palette_colors
        )

        fig.update_layout(title=dict(
                                text="",
                                x=0.5,                                # Centraliza o título
                                xanchor='center',
                                yanchor='top', 
                                font=fonte_titulo), 
                        xaxis_title="Origem", 
                        yaxis_title="Quantidade",
                        font=fonte_texto,
                        width=1080,
                        height=500,
                        margin=dict(l=10, r=0, t=50, b=50),
                        legend=legenda
                        )
        
        st.plotly_chart(fig, use_container_width=True)


        # Figura 3
        st.write("---")
        st.subheader("Distribuição dos Leads por Convênio e Origem")
        quantidade_maxima_convenios = st.number_input("Quantidade de convênios", min_value=1, max_value=None, value=5, step=1, key=1)

        leads_por_convenio = base.groupby(['convenio', 'origem'])['id'].size().reset_index(name='quantidade')
        leads_por_convenio = leads_por_convenio.loc[leads_por_convenio['quantidade'] > 5]

        totais_por_convenio = leads_por_convenio.groupby('convenio')['quantidade'].sum().sort_values(ascending=False)
        leads_por_convenio = leads_por_convenio.set_index('convenio')  # Define 'convenio' como índice temporariamente
        leads_por_convenio = leads_por_convenio.loc[totais_por_convenio.index]  # Reordena pelo índice
        leads_por_convenio = leads_por_convenio.reset_index()  # Restaura o índice padrão

        top_convenios = leads_por_convenio.groupby('convenio')['quantidade'].sum() \
                                  .nlargest(quantidade_maxima_convenios).index
        leads_por_convenio_filtrado = leads_por_convenio[leads_por_convenio['convenio'].isin(top_convenios)]

        fig = px.bar(
            leads_por_convenio_filtrado, 
            x='quantidade',               # Quantidade no eixo X
            y='convenio',                 # Convênio no eixo Y
            color='origem',               # Diferenciar pelas origens
            title="Distribuição dos Leads por Convênio e Origem",  # Título do gráfico
            labels={
                'origem': 'Origem dos Leads',
                'quantidade': 'Quantidade',
                'convenio': 'Convênio'
            },
            color_discrete_sequence=palette_colors
        )

        fig.update_layout(
            xaxis_title="Quantidade",
            yaxis_title="Convênios",
            font=fonte_texto,
            width=1080,
            height=500,
            margin=dict(l=10, r=0, t=50, b=50),
            legend=legenda
        )

        st.plotly_chart(fig, use_container_width=True)



        # Figura 4
        st.write("---")
        st.subheader("Quantidade de Leads por Convênio (Segmentado pela Comissão)")
        quantidade_maxima_convenios = st.number_input("Quantidade de convênios", min_value=1, max_value=None, value=5, step=1, key=2)
        leads_comissao = base.groupby(['convenio', 'faixa_comissao'], observed=True)['id'].size().reset_index(name='quantidade')

        top_convenios = leads_comissao.groupby('convenio')['quantidade'].sum() \
                              .nlargest(quantidade_maxima_convenios).index

        leads_comissao_filtrado = leads_comissao[leads_comissao['convenio'].isin(top_convenios)]

        fig = px.bar(
            leads_comissao_filtrado, 
            x='quantidade',               # Quantidade no eixo X
            y='convenio',                 # Convênio no eixo Y
            color='faixa_comissao',       # Diferenciar pelas faixas de comissão
            labels={
                'faixa_comissao': 'Faixa de Comissão',
                'quantidade': 'Quantidade',
                'convenio': 'Convênio'
            },
            color_discrete_sequence=palette_colors
        )

        fig.update_layout(
            xaxis_title="Quantidade",
            yaxis_title="Convênios",
            font=fonte_texto,
            width=1080,
            height=500,
            template='plotly_dark',
            margin=dict(l=10, r=0, t=50, b=50),
            legend=legenda,
        )

        st.plotly_chart(fig, use_container_width=True)









    else:
        st.warning("Nenhum dado disponível para os filtros selecionados.")
else:
    st.info("Por favor, faça o upload de um arquivo CSV para começar.")
