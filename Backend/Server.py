from flask import Flask, request, jsonify
from src import fetchTransactions, fetchAccounts

app = Flask(__name__)

#Rotas

@app.route('/',methods=['GET'])
def get():
    return jsonify({'msg': 'Server running'})

@app.route('/', methods=['POST'])
def post():
    data = request.json
    itemid = data.get('itemId')
    if not itemid:
        return jsonify({'error': 'itemId is required'}), 400
    
    return jsonify(fetchTransactions(fetchAccounts(itemid)))

@app.route('/fetchAccounts', methods=['POST'])
def fetchAccounts():
    data = request.json
    itemid = data.get('itemId')
    if not itemid:
        return jsonify({'error': 'itemid is required'}), 400

    return jsonify(fetchAccounts(itemid))


@app.route('/fetchTransactions', methods=['POST'])
def fetchTransactions():
    data = request.json
    accounts = data.get('accounts')
    if not accounts:
        return jsonify({'error': 'accounts are required'}), 400

    return jsonify(fetchTransactions(accounts))
    

if __name__ == '__main__':
    app.run(port=5000, debug=True)
