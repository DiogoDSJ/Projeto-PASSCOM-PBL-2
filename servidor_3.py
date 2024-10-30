from flask import Flask, request, jsonify
import json
from pathlib import Path
import threading

app = Flask(__name__)

# Caminhos dos arquivos JSON
CAMINHO_TRECHOS = Path(__file__).parent / "trechos_viagem_s3.json"
CAMINHO_CLIENTES = Path(__file__).parent / "clientes.json"

SERVER_1_URL = "http://localhost:3000"

# Lock para sincronização de acesso aos arquivos
lock = threading.Lock()

# Classe Cliente
class Cliente:
    def __init__(self, cpf, trechos=None):
        self.cpf = cpf
        self.trechos = trechos if trechos is not None else {}

    def to_dict(self):
        return {
            'cpf': self.cpf,
            'trechos': self.trechos
        }

    @staticmethod
    def from_dict(data):
        return Cliente(
            cpf=data['cpf'],
            trechos=data.get('trechos', {})
        )

# Funções auxiliares para manipulação de JSON
def salvar_json(dados, caminho_arquivo):
    try:
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Erro ao salvar JSON em {caminho_arquivo}: {e}")

def carregar_json(caminho_arquivo):
    try:
        if not caminho_arquivo.exists():
            return {}
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Erro: O arquivo {caminho_arquivo} contém JSON inválido.")
        return {}
    except Exception as e:
        print(f"Erro ao carregar JSON de {caminho_arquivo}: {e}")
        return {}

# Funções para clientes
def salvar_clientes(clientes):
    dados = [cliente.to_dict() for cliente in clientes]
    salvar_json(dados, CAMINHO_CLIENTES)

def carregar_clientes():
    dados = carregar_json(CAMINHO_CLIENTES)
    # Retorna uma lista vazia se não houver clientes
    if not isinstance(dados, list):
        print(f"Erro: O arquivo {CAMINHO_CLIENTES} não contém uma lista válida de clientes.")
        return []
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

# Rota que lista trechos do Servidor 1
@app.route('/listar_trechos', methods=['GET'])
def listar_trechos_s1():
    # Fazendo a chamada GET para o Servidor 1 para listar trechos
    response = request.get(f"{SERVER_1_URL}/trechos")

    # Retorna a resposta do Servidor 1
    return jsonify(response.json()), response.status_code

# Endpoint de Cadastro (sem senha)
@app.route('/cadastro', methods=['POST'])
def cadastro():
    data = request.get_json()
    cpf = data.get('cpf')

    if not cpf:
        return jsonify({"msg": "CPF é obrigatório"}), 400

    if not cpf.isdigit() or len(cpf) != 11:
        return jsonify({"msg": "CPF inválido. Deve conter exatamente 11 dígitos."}), 400

    with lock:
        if encontrar_cliente(cpf):
            return jsonify({"msg": "Cliente já existe"}), 409

        cliente = Cliente(cpf=cpf)
        adicionar_cliente(cliente)

    return jsonify({"msg": "Cadastro realizado com sucesso"}), 201

# Endpoint para listar trechos disponíveis
@app.route('/trechos', methods=['GET'])
def listar_trechos():
    trechos = carregar_trechos()
    return jsonify(trechos), 200

# Endpoint para comprar passagem (solicita CPF no momento da compra)
@app.route('/comprar', methods=['POST'])
def comprar_passagem():
    data = request.get_json()
    caminho = data.get('caminho')  # Lista de cidades, ex: ["CidadeA", "CidadeB", "CidadeC"]
    cpf = data.get('cpf')

    if not caminho or not isinstance(caminho, list) or len(caminho) < 2:
        return jsonify({"msg": "Caminho inválido"}), 400

    if not cpf:
        return jsonify({"msg": "CPF é obrigatório"}), 400

    if not cpf.isdigit() or len(cpf) != 11:
        return jsonify({"msg": "CPF inválido. Deve conter exatamente 11 dígitos."}), 400

    with lock:
        trechos_viagem = carregar_trechos()
        cliente = encontrar_cliente(cpf)
        if not cliente:
            return jsonify({"msg": "Cliente não encontrado. Faça o cadastro primeiro."}), 404

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
def ver_passagens():
    cpf = request.args.get('cpf')
    if not cpf:
        return jsonify({"msg": "CPF é obrigatório"}), 400

    if not cpf.isdigit() or len(cpf) != 11:
        return jsonify({"msg": "CPF inválido. Deve conter exatamente 11 dígitos."}), 400

    cliente = encontrar_cliente(cpf)
    if not cliente:
        return jsonify({"msg": "Cliente não encontrado"}), 404
    return jsonify(cliente.trechos), 200

# Endpoint para buscar possibilidades de rotas
@app.route('/buscar', methods=['GET'])
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
        # Criação do arquivo clientes.json se não existir
        if not CAMINHO_CLIENTES.exists():
            try:
                salvar_json([], CAMINHO_CLIENTES)
                print(f"Arquivo {CAMINHO_CLIENTES} criado com sucesso.")
            except Exception as e:
                print(f"Erro ao criar {CAMINHO_CLIENTES}: {e}")

        # Criação do arquivo trechos_viagem.json se não existir
        if not CAMINHO_TRECHOS.exists():
            trechos_exemplo = {
                "São Paulo-SP": {
                    "Rio de Janeiro-RJ": {"vagas": 10, "preco": 100},
                    "Brasília-DF": {"vagas": 5, "preco": 150}
                },
                "Rio de Janeiro-RJ": {
                    "Brasília-DF": {"vagas": 8, "preco": 80},
                    "Salvador-BA": {"vagas": 2, "preco": 120}
                },
                "Brasília-DF": {
                    "Salvador-BA": {"vagas": 4, "preco": 90}
                },
                "Salvador-BA": {
                    "Fortaleza-CE": {"vagas": 3, "preco": 110}
                },
                "Fortaleza-CE": {
                    "Recife-PE": {"vagas": 6, "preco": 70}
                },
                "Recife-PE": {
                    "Porto Alegre-RS": {"vagas": 2, "preco": 130}
                },
                "Porto Alegre-RS": {
                    "Curitiba-PR": {"vagas": 5, "preco": 95}
                },
                "Curitiba-PR": {
                    "Manaus-AM": {"vagas": 1, "preco": 200}
                },
                "Manaus-AM": {
                    "Belo Horizonte-MG": {"vagas": 4, "preco": 160}
                },
                "Belo Horizonte-MG": {
                    "São Paulo-SP": {"vagas": 7, "preco": 85}
                }
            }
            try:
                salvar_trechos(trechos_exemplo)
                print(f"Arquivo {CAMINHO_TRECHOS} criado com sucesso com trechos de exemplo.")
            except Exception as e:
                print(f"Erro ao criar {CAMINHO_TRECHOS}: {e}")




# Executa a inicialização dos arquivos
inicializar_arquivos()

# Executar a aplicação
if __name__ == '__main__':
    app.run(debug=True, port=5000)
