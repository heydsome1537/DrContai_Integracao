from flask import Flask, request, jsonify
import requests
import json
import pandas as pd
from pandas import json_normalize 
import os

app = Flask(__name__)

PLUGGY_CLIENT_ID = os.getenv('PLUGGY_CLIENT_ID')
PLUGGY_CLIENT_SECRET = os.getenv('PLUGGY_CLIENT_SECRET')



            ###################
            #    Funções      # 
            ###################


def categoriesRemap(category_id, categories):
    
    #mas podemos por API em criar regras de categorias
    #caso adicionarmos, temos que adicionar dois campos (description e descriptionTranslated)
    #por enquanto não possuimos regras de categorias da contabiliza
    #Por enquanto o remap ta sendo por descriptionTranslated
    
    for category in categories:
        if category['id'] == category_id:
            return category['descriptionTranslated'] 
    return 'Outros'
    
def fetchCategories():  #Pensei em exportar o arquivo (usar o categoriesRemap.json), mas achei melhor para manter atualizado caso criassem novas regras
        url = "https://api.pluggy.ai/categories"
        headers = {
            "accept": "application/json",
            "X-API-KEY": apiKeyauth()
        }
        response = requests.get(url,headers = headers)
        data = response.json()['results']
        return data
    
def apiKeyauth (): 
    url = "https://api.pluggy.ai/auth"
    
    payload = {
        "clientId": PLUGGY_CLIENT_ID, 
        "clientSecret": PLUGGY_CLIENT_SECRET
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    data = response.json()
    return data["apiKey"]


                #########
                # Rotas #
                #########

@app.route('/',methods=['GET'])
def get():
    return jsonify({'msg': 'Server running'})


@app.route('/', methods=['POST'])
def post():
    data = request.json
    itemid = data.get('itemId')
    if not itemid:
        return jsonify({'error': 'itemId is required'}), 400

    # Fetch accounts using the itemId
    url = f"https://api.pluggy.ai/accounts?itemId={itemid}"
    headers = {
        "accept": "application/json",
        "X-API-KEY": apiKeyauth()
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return jsonify({'error': 'Failed to fetch accounts', 'details': str(e)}), 500

    try:
        accounts = response.json().get('results', [])
    except (ValueError, KeyError) as e:
        return jsonify({'error': 'Invalid response format', 'details': str(e)}), 500

    account_ids = [account['id'] for account in accounts]

    # Fetch transactions using the account ids
    apiKey = apiKeyauth()
    categories_list = fetchCategories()
    dfs = {}
    i = 0

    for account_id in account_ids:
        url = f"https://api.pluggy.ai/transactions?accountId={account_id}"
        headers = {
            "accept": "application/json",
            "X-API-KEY": apiKey
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return jsonify({'error': 'Failed to fetch transactions', 'details': str(e)}), 500

        try:
            results = response.json().get('results', [])
        except (ValueError, KeyError) as e:
            return jsonify({'error': 'Invalid response format', 'details': str(e)}), 500

        df = pd.DataFrame(results)
        if df.empty:
            continue

        df_spliced = df[['amount', 'amountInAccountCurrency', 'currencyCode', 'category', 'categoryId', 'type', 'date','description']]
        df_spliced['category'] = df_spliced['categoryId'].apply(lambda category_id: categoriesRemap(category_id, categories_list) if pd.notna(category_id) else 'Outros')
        if i == 0:
            dfs['Extrato'] = df_spliced
        else:
            dfs[f'Cartão{i}'] = df_spliced
        i += 1
        grouped_dfs = {}
        
    for key, df in dfs.items():
        df['year_month'] = pd.to_datetime(df['date']).dt.to_period('M')
        grouped_df = df.groupby(['category', 'year_month']).sum(numeric_only=True)
        grouped_dfs[key] = {f"{category}_{year_month}": data for (category, year_month), data in grouped_df.to_dict(orient='index').items()}

    # Ensure the directory exists
    output_dir = os.path.join(os.getcwd(), 'Dashboard')
    os.makedirs(output_dir, exist_ok=True)

    # Export to CSV
    for key, df in dfs.items():
        df.to_csv(os.path.join(output_dir, f'{key}.csv'), index=False)

    
    return jsonify(grouped_dfs)


##################
#  Rotas Teste   #
##################
@app.route('/fetchAccounts', methods=['POST'])
def fetchAccounts():
    data = request.json
    itemid = data.get('itemId')
    if not itemid:
        return jsonify({'error': 'itemid is required'}), 400

    url = f"https://api.pluggy.ai/accounts?itemId={itemid}"

    headers = {
        "accept": "application/json",
        "X-API-KEY": apiKeyauth()
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return jsonify({'error': 'Failed to fetch accounts', 'details': str(e)}), 500

    try:
        accounts = response.json().get('results', [])

        
    except (ValueError, KeyError) as e:
        return jsonify({'error': 'Invalid response format', 'details': str(e)}), 500
       
    
    result = [account['id'] for account in accounts]
    return jsonify(result)


@app.route('/fetchTransactions', methods=['POST'])
def fetchTransactions():
    data = request.json
    accounts = data.get('accounts')
    if not accounts:
        return jsonify({'error': 'accounts are required'}), 400

    apiKey = apiKeyauth()
    categories_list = fetchCategories()
    dfs = {}
    i = 0

    for account in accounts:
        url = f"https://api.pluggy.ai/transactions?accountId={account}"
        headers = {
            "accept": "application/json",
            "X-API-KEY": apiKey
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return jsonify({'error': 'Failed to fetch transactions', 'details': str(e)}), 500

        try:
            results = response.json().get('results', [])
        except (ValueError, KeyError) as e:
            return jsonify({'error': 'Invalid response format', 'details': str(e)}), 500

        df = pd.DataFrame(results)
        if df.empty:
            continue

        df_spliced = df[['amount', 'amountInAccountCurrency','description', 'currencyCode', 
                         'category', 'categoryId', 'type', 'date']]
        df_spliced['category'] = df_spliced['categoryId'].apply(lambda category_id: categoriesRemap(category_id, categories_list))
        if i == 0:
            dfs['Extrato'] = df_spliced
        else:
            dfs[f'Cartão{i}'] = df_spliced
        i += 1

    grouped_dfs = {}
    for key, df in dfs.items():
        grouped_df = df.groupby('category').sum()
        grouped_dfs[key] = grouped_df.to_dict(orient='index')

    return jsonify(grouped_dfs)
    

if __name__ == '__main__':
    app.run(port=5000, debug=True)