from flask import Flask, request, jsonify
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)
import json
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash
import threading

app = Flask(__name__)

# Configuração do JWT
app.config['JWT_SECRET_KEY'] = 'sua_chave_secreta'  # Substitua por uma chave segura
jwt = JWTManager(app)

# Caminhos dos arquivos JSON
CAMINHO_TRECHOS = Path(__file__).parent / "trechos_viagem.json"
CAMINHO_CLIENTES = Path(__file__).parent / "clientes.json"

# Lock para sincronização de acesso aos arquivos
lock = threading.Lock()

# Classe Cliente
class Cliente:
    def __init__(self, cpf, senha, trechos=None):
        self.cpf = cpf
        self.senha = senha  # Senha hash
        self.trechos = trechos if trechos is not None else {}

    def to_dict(self):
        return {
            'cpf': self.cpf,
            'senha': self.senha,
            'trechos': self.trechos
        }

    @staticmethod
    def from_dict(data):
        return Cliente(
            cpf=data['cpf'],
            senha=data['senha'],
            trechos=data.get('trechos', {})
        )

# Funções auxiliares para manipulação de JSON
def salvar_json(dados, caminho_arquivo):
    with open(caminho_arquivo, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

def carregar_json(caminho_arquivo):
    if not caminho_arquivo.exists():
        return {}
    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        return json.load(f)

# Funções para clientes
def salvar_clientes(clientes):
    dados = [cliente.to_dict() for cliente in clientes]
    salvar_json(dados, CAMINHO_CLIENTES)

def carregar_clientes():
    dados = carregar_json(CAMINHO_CLIENTES)
    return [Cliente.from_dict(cliente) for cliente in dados]

def encontrar_cliente(cpf):
    clientes = carregar_clientes()
    for cliente in clientes:
        if cliente.cpf == cpf:
            return cliente
    return None

def adicionar_cliente(cliente):
    clientes = carregar_clientes()
    clientes.append(cliente)
    salvar_clientes(clientes)

def atualizar_cliente(cliente_atualizado):
    clientes = carregar_clientes()
    for idx, cliente in enumerate(clientes):
        if cliente.cpf == cliente_atualizado.cpf:
            clientes[idx] = cliente_atualizado
            salvar_clientes(clientes)
            return
    # Se não encontrar, adicionar
    adicionar_cliente(cliente_atualizado)

# Funções para trechos
def carregar_trechos():
    dados = carregar_json(CAMINHO_TRECHOS)
    return dados.get("trechos", {})

def salvar_trechos(trechos):
    dados = {"trechos": trechos}
    salvar_json(dados, CAMINHO_TRECHOS)

# Endpoint de Cadastro
@app.route('/cadastro', methods=['POST'])
def cadastro():
    data = request.get_json()
    cpf = data.get('cpf')
    senha = data.get('senha')

    if not cpf or not senha:
        return jsonify({"msg": "CPF e senha são obrigatórios"}), 400

    with lock:
        if encontrar_cliente(cpf):
            return jsonify({"msg": "Cliente já existe"}), 409

        senha_hash = generate_password_hash(senha)
        cliente = Cliente(cpf=cpf, senha=senha_hash)
        adicionar_cliente(cliente)

    return jsonify({"msg": "Cadastro realizado com sucesso"}), 201

# Endpoint de Login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    cpf = data.get('cpf')
    senha = data.get('senha')

    if not cpf or not senha:
        return jsonify({"msg": "CPF e senha são obrigatórios"}), 400

    cliente = encontrar_cliente(cpf)
    if not cliente or not check_password_hash(cliente.senha, senha):
        return jsonify({"msg": "CPF ou senha inválidos"}), 401

    access_token = create_access_token(identity=cpf)
    return jsonify(access_token=access_token), 200

# Endpoint para listar trechos disponíveis
@app.route('/trechos', methods=['GET'])
@jwt_required()
def listar_trechos():
    trechos = carregar_trechos()
    return jsonify(trechos), 200

# Endpoint para comprar passagem
@app.route('/comprar', methods=['POST'])
@jwt_required()
def comprar_passagem():
    data = request.get_json()
    caminho = data.get('caminho')  # Lista de cidades, ex: ["CidadeA", "CidadeB", "CidadeC"]

    if not caminho or not isinstance(caminho, list) or len(caminho) < 2:
        return jsonify({"msg": "Caminho inválido"}), 400

    cpf = get_jwt_identity()

    with lock:
        trechos_viagem = carregar_trechos()
        clientes = carregar_clientes()
        cliente = encontrar_cliente(cpf)
        if not cliente:
            return jsonify({"msg": "Cliente não encontrado"}), 404

        # Verificar e atualizar vagas
        trecho_copy = caminho.copy()
        sucesso = True
        for i in range(len(trecho_copy)-1):
            origem = trecho_copy[i]
            destino = trecho_copy[i+1]
            if origem not in trechos_viagem or destino not in trechos_viagem[origem]:
                sucesso = False
                break
            if trechos_viagem[origem][destino]["vagas"] < 1:
                sucesso = False
                break
            trechos_viagem[origem][destino]["vagas"] -= 1

        if sucesso:
            salvar_trechos(trechos_viagem)
            # Adicionar passagem ao cliente
            novo_id = int(max(cliente.trechos.keys(), default=0)) + 1
            cliente.trechos[str(novo_id)] = caminho
            atualizar_cliente(cliente)
            return jsonify({"msg": "Passagem comprada com sucesso"}), 200
        else:
            return jsonify({"msg": "Passagem não disponível"}), 400

# Endpoint para ver passagens compradas
@app.route('/passagens', methods=['GET'])
@jwt_required()
def ver_passagens():
    cpf = get_jwt_identity()
    cliente = encontrar_cliente(cpf)
    if not cliente:
        return jsonify({"msg": "Cliente não encontrado"}), 404
    return jsonify(cliente.trechos), 200

# Endpoint para buscar possibilidades de rotas
@app.route('/buscar', methods=['GET'])
@jwt_required()
def buscar_rotas():
    origem = request.args.get('origem')
    destino = request.args.get('destino')

    if not origem or not destino:
        return jsonify({"msg": "Origem e destino são obrigatórios"}), 400

    trechos_viagem = carregar_trechos()

    rotas = {}
    id_rota = 1

    def dfs(cidade_atual, caminho, visitados, preco_total):
        nonlocal id_rota
        caminho.append(cidade_atual)
        visitados.add(cidade_atual)

        if cidade_atual == destino:
            rotas[id_rota] = {"caminho": caminho.copy(), "preco_total": preco_total}
            id_rota += 1
        else:
            for vizinho, info in trechos_viagem.get(cidade_atual, {}).items():
                if info["vagas"] > 0 and vizinho not in visitados:
                    dfs(vizinho, caminho, visitados, preco_total + info.get("preco", 0))  # Supondo que há um campo 'preco'

        caminho.pop()
        visitados.remove(cidade_atual)

    dfs(origem, [], set(), 0)
    return jsonify(rotas), 200

# Inicialização dos arquivos JSON se não existirem
def inicializar_arquivos():
    with lock:
        if not CAMINHO_CLIENTES.exists():
            salvar_json([], CAMINHO_CLIENTES)
        if not CAMINHO_TRECHOS.exists():
            # Exemplo de estrutura de trechos
            trechos_exemplo = {
                "CidadeA": {
                    "CidadeB": {"vagas": 10, "preco": 100},
                    "CidadeC": {"vagas": 5, "preco": 150}
                },
                "CidadeB": {
                    "CidadeC": {"vagas": 8, "preco": 80},
                    "CidadeD": {"vagas": 2, "preco": 120}
                },
                "CidadeC": {
                    "CidadeD": {"vagas": 4, "preco": 90}
                }
            }
            salvar_trechos(trechos_exemplo)

# Executa a inicialização dos arquivos
inicializar_arquivos()

# Executar a aplicação
if __name__ == '__main__':
    app.run(debug=True, port=3000)
