from flask import Flask, request, jsonify
import requests
import json
import pandas as pd
from pandas import json_normalize 
import os
from flask import  jsonify

PLUGGY_CLIENT_ID = os.getenv('PLUGGY_CLIENT_ID')
PLUGGY_CLIENT_SECRET = os.getenv('PLUGGY_CLIENT_SECRET')

def categoriesRemap(category_id, categories): 
    for category in categories:
        if category['id'] == category_id:
            return category['descriptionTranslated'] 
    return 'Outros'
       
    
    
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


    
def fetchCategories():  
        url = "https://api.pluggy.ai/categories"
        headers = {
            "accept": "application/json",
            "X-API-KEY": apiKeyauth()
        }
        response = requests.get(url,headers = headers)
        data = response.json()['results']
        return data
    
    

def fetchAccounts(itemid):
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
        return response.json().get('results', [])
    except (ValueError, KeyError) as e:
        return jsonify({'error': 'Invalid response format', 'details': str(e)}), 500



def fetchTransactions(accounts):
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

    return grouped_dfs
