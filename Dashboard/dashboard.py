#python -m streamlit run dashboard.py
import streamlit as st 
import pandas as pd
import glob
import plotly.express as px
import os

fixedIncomeOrExpenseIds = ["01000000", "01010000", "01020000", "01030000", "01040000", "01050000", "02000000", "02010000", "02020000", "02030000", "02030001", "02030002", "02030003", "02040000", "03000000", "03010000", "03020000", "03030000", "03040000", "03050000", "03060000", "03070000", "04000000", "04010000", "04020000", "04030000", "05000000", "05010000", "05020000", "05030000", "05040000", "05050000", "05060000", "05070000", "05080000", "05090000", "05090001", "05090002", "05090003", "05090004", "05090005", "05100000", "06000000", "06010000", "06020000", "07000000", "07010000", "07010001", "07010002", "07010003", "07020000", "07020001", "07020002", "07020003", "07020004", "07030000", "07030001", "07030002", "07030003", "07040000", "07040001", "07040002", "07040003", "08000000", "08010000", "08020000", "08030000", "08040000", "08050000", "08060000", "08070000", "08080000", "08090000", "09000000", "09010000", "09020000", "09030000", "10000000", "11000000", "11010000", "11020000", "12000000", "12010000", "12020000", "12030000", "12040000", "13000000", "14000000", "14010000", "14020000", "15000000", "15010000", "15020000", "15030000", "16000000", "16010000", "16020000", "16030000", "17000000", "17010000", "17020000", "17020001", "17020002", "17020003", "17030000", "17040000", "18000000", "18010000", "18020000", "18030000", "18040000", "19000000", "19010000", "19020000", "19030000", "19040000", "19050000", "19050001", "19050002", "19050003", "19050004", "19050005", "19050006", "20000000", "200100000", "200200000", "200300000", "200400000", "21000000", "99999999"]

st.write('''# Relatório de Transações Financeiras''')

image = os.getenv('IMAGEM')
st.sidebar.image(image, use_column_width=True)

LOCAL = os.getenv('LOCAL_DOS_ARQUIVOS')

df_extrato = pd.read_csv(os.path.join(LOCAL, 'Extrato.csv'), sep=',', decimal='.')
cartao_files = glob.glob(os.path.join(LOCAL, 'Cartão*.csv'))

selected_file = st.sidebar.selectbox('Selecione o arquivo para gerar o gráfico', ['Extrato'] + [f'Cartão{i+1}' for i in range(len(cartao_files))])

df_cartao_dict = {f'Cartão{i+1}': pd.read_csv(file, sep=',', decimal='.') for i, file in enumerate(cartao_files)}
df_cartao = pd.concat(df_cartao_dict.values())
df_combined = pd.concat([df_extrato, df_cartao])


if selected_file == 'Extrato':
    df_filtered = df_extrato
else:
    df_filtered = df_cartao_dict[selected_file]


date_range = st.sidebar.slider(
    'Selecione o intervalo de tempo',
    min_value=pd.to_datetime(df_filtered['date']).min().date(),
    max_value=pd.to_datetime(df_filtered['date']).max().date(),
    value=(pd.to_datetime(df_filtered['date']).min().date(), pd.to_datetime(df_filtered['date']).max().date())
)


df_filtered = df_filtered[
    (pd.to_datetime(df_filtered['date']).dt.date >= date_range[0]) &
    (pd.to_datetime(df_filtered['date']).dt.date <= date_range[1])
]


df_filtered = df_filtered.rename(columns={
    'amount': 'quantia',
    'description': 'descrição',
    'amountInAccountCurrency': 'quantiaEmMoedaDaConta',
    'currencyCode': 'codigoDaMoeda',
    'category': 'categoria',
    'categoryId': 'idDaCategoria',
    'type': 'tipo',
    'date': 'data'
})


df_filtered['tipo_despesa'] = df_filtered['idDaCategoria'].apply(lambda x: 'Despesa Fixa' if x in fixedIncomeOrExpenseIds else 'Despesa Variável')
df_tipo_despesa = df_filtered.groupby('tipo_despesa')['quantia'].sum().reset_index()

# Criar um gráfico de barras
df_grouped = df_filtered.groupby('categoria')['quantia'].sum().reset_index()
fig = px.bar(df_grouped, x='categoria', y='quantia', title=f'TOTAL POR CATEGORIA - {selected_file}'.upper())
st.plotly_chart(fig)

selected_category = st.selectbox('Selecione a categoria', df_grouped['categoria'].unique())

# Filtrar o DataFrame com base na categoria selecionada
df_category_filtered = df_filtered[df_filtered['categoria'] == selected_category]
df_category_filtered = df_category_filtered.drop(columns=['idDaCategoria', 'quantiaEmMoedaDaConta', 'tipo', 'tipo_despesa'])
df_category_filtered['data'] = pd.to_datetime(df_category_filtered['data']).dt.date
df_category_filtered['quantia'] = df_category_filtered['quantia'].apply(lambda x: f"{x:,.2f}".replace(',', 'v').replace('.', ',').replace('v', '.'))

st.write(f'## Gastos na Categoria: {selected_category}')
st.dataframe(df_category_filtered, height=800, width=1400)

# Criar o gráfico de pizza
fig_pie = px.pie(df_tipo_despesa, names='tipo_despesa', values='quantia', title='Distribuição de Despesas Fixas e Variáveis')
st.plotly_chart(fig_pie)