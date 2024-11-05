from flask import Flask, request, jsonify
import json
from pathlib import Path
import threading
import requests

app = Flask(__name__)

# Caminhos dos arquivos JSON
CAMINHO_TRECHOS = Path(__file__).parent / "trechos_viagem_s2.json"
CAMINHO_CLIENTES = Path(__file__).parent / "clientes.json"

SERVER_1_URL = "http://localhost:3000"
SERVER_2_URL = "http://localhost:4000"
SERVER_3_URL = "http://localhost:5000"

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
        
# saber em qual servidor está
def get_server():
   return "server2"

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
    adicionar_cliente(cliente_atualizado)

@app.route('/remover_vaga', methods=['POST'])
def remover_uma_vaga():
    data = request.get_json()
    origem = data.get("origem")
    destino = data.get("destino")
    
    trechos_viagem = carregar_trechos()
    if(trechos_viagem[origem][destino]["vagas"] > 0):
        trechos_viagem[origem][destino]["vagas"] -= 1
        salvar_trechos(trechos_viagem)
        return jsonify({"msg": "Vaga removida com sucesso"}), 200
    else:
        return jsonify({"msg": "Erro na remocao da vaga"}), 400

# Funções para trechos
def carregar_trechos():
    dados = carregar_json(CAMINHO_TRECHOS)
    return dados.get("trechos", {})

def salvar_trechos(trechos):
    dados = {"trechos": trechos}
    salvar_json(dados, CAMINHO_TRECHOS)

def obter_cidades(dados):
    cidades = set()

    for origem, destinos in dados["trechos"].items():
        cidades.add(origem)
        for destino in destinos.keys():
            cidades.add(destino)

    return sorted(cidades)

@app.route('/obter_cidades', methods=['GET'])
def obter_cidades_endpoint():
    try:
        with open("trechos_viagem_s2.json", "r", encoding="utf-8") as file:
            dados = json.load(file)

        cidades = obter_cidades(dados)
        return jsonify(cidades), 200

    except Exception as e:
        return jsonify({"msg": "Erro ao obter cidades", "erro": str(e)}), 500

@app.route('/listar_trechos', methods=['GET'])
def listar_trechos_s1():
    response = request.get(f"{SERVER_1_URL}/trechos")
    return jsonify(response.json()), response.status_code

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

@app.route('/trechos', methods=['GET'])
def listar_trechos():
    trechos = carregar_trechos()
    return jsonify(trechos), 200

# Endpoint para preparar a compra da passagem
@app.route('/comprar', methods=['POST'])
def preparar_compra():
    data = request.get_json()
    caminho = data.get('caminho')  # Lista de cidades, ex: ["CidadeA", "CidadeB", "CidadeC"]
    cpf = data.get('cpf')
    servidores = data.get('servidores')
    if not caminho or not isinstance(caminho, list) or len(caminho) < 2:
        return jsonify({"msg": "Caminho inválido"}), 400

    if not cpf:
        return jsonify({"msg": "CPF é obrigatório"}), 400

    if not cpf.isdigit() or len(cpf) != 11:
        return jsonify({"msg": "CPF inválido. Deve conter exatamente 11 dígitos."}), 400
    print(f"servidores2{servidores}")
    with lock:
        trechos_viagem = carregar_trechos()
        cliente = encontrar_cliente(cpf)
        server1 = False
        server2 = False
        server3 = False
        # Verificar a disponibilidade de passagens
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
        # Verificar de que servidor vieram os trechos que fazem o caminho
        for servidor in servidores:
            if(servidor == "server1"):
                server1 = True
            elif(servidor == "server2"):
                server2 = True
            elif(servidor == "server3"):
                server3 = True
        if sucesso:
            # Fase de preparação: notificar outros servidores
            try:
                prepare_responses = []
                if(server1): # somente se usa
                    response = requests.post(f"{SERVER_1_URL}/prepare", json={"caminho": caminho, "cpf": cpf})
                    prepare_responses.append(response)
                if(server3): # somente se usa
                    response = requests.post(f"{SERVER_3_URL}/prepare", json={"caminho": caminho, "cpf": cpf})
                    prepare_responses.append(response)

                # Verificar se todos os servidores responderam com sucesso
                if len(prepare_responses) == 0 or all(resp.status_code == 200 for resp in prepare_responses):
                    # Fase de commit
                    if(server1): # somente se usa
                        requests.post(f"{SERVER_1_URL}/commit", json={"caminho": caminho, "cpf": cpf}) #manda compra nos outros servidores
                    if(server2): # somente se usa
                        requests.post(f"{SERVER_2_URL}/commit", json={"caminho": caminho, "cpf": cpf}) #manda compra nos outros servidores
                    if(server3): # somente se usa
                        requests.post(f"{SERVER_3_URL}/commit", json={"caminho": caminho, "cpf": cpf}) #manda compra nos outros servidores
                    # Adicionar passagem ao cliente
                    novo_id = int(max(cliente.trechos.keys(), default=0)) + 1
                    cliente.trechos[str(novo_id)] = caminho
                    atualizar_cliente(cliente)
                    return jsonify({"msg": "Passagem comprada com sucesso"}), 200
                else:
                    # Se algum servidor falhar, faz rollback
                    if(server1): # somente se usa
                        requests.post(f"{SERVER_1_URL}/rollback", json={"caminho": caminho, "cpf": cpf})
                    if(server3): # somente se usa
                        requests.post(f"{SERVER_3_URL}/rollback", json={"caminho": caminho, "cpf": cpf})
                    return jsonify({"msg": "Compra cancelada, não foi possível concluir a transação"}), 400

            except requests.RequestException:
                return jsonify({"msg": "Erro ao comunicar com os servidores externos."}), 500
        else:
            return jsonify({"msg": "Passagem não disponível"}), 400

@app.route('/passagens', methods=['GET'])
def ver_passagens():
    cpf = request.args.get('cpf')
    if not cpf:
        return jsonify({"msg": "CPF é obrigatório"}), 400

    if not cpf.isdigit() or len(cpf) != 11:
        return jsonify({"msg": "CPF inválido. Deve conter exatamente 11 dígitos."}), 400

    cliente = encontrar_cliente(cpf)
    if not cliente:
        return jsonify({"msg": "Cliente não encontrado."}), 404

    return jsonify(cliente.trechos), 200

@app.route('/buscar', methods=['GET'])
def buscar_rotas():
    origem = request.args.get('origem')
    destino = request.args.get('destino')

    if not origem or not destino:
        return jsonify({"msg": "Origem e destino são obrigatórios"}), 400

    trechos_viagem = carregar_trechos()
    servidores_externos = [SERVER_2_URL, SERVER_3_URL]  # URLs dos servidores externos

    rotas = {}
    id_rota = 1
    
    def dfs(cidade_atual, caminho, visitados, preco_total, servidores_incluidos):
        nonlocal id_rota
        caminho.append(cidade_atual)
        visitados.add(cidade_atual)

        if cidade_atual == destino:
            # Quando alcança o destino, armazena a rota
            rotas[id_rota] = {
                "caminho": caminho.copy(),
                "preco_total": preco_total,
                "servidores_incluidos": list(servidores_incluidos)
            }
            id_rota += 1
        else:
            trechos_disponiveis = obter_trechos_plus(cidade_atual, trechos_viagem, servidores_externos)

            for vizinho, info in trechos_disponiveis.items():
                if info["vagas"] > 0 and vizinho not in visitados:
                    server_id = info.get("server_id", "local")
                    
                    # Executa a DFS sem modificar `servidores_incluidos` ainda
                    if server_id != "local":
                        dfs(vizinho, caminho, visitados, preco_total + info.get("preco", 0), servidores_incluidos | {server_id})
                    else:
                        dfs(vizinho, caminho, visitados, preco_total + info.get("preco", 0), servidores_incluidos)

        caminho.pop()
        visitados.remove(cidade_atual)

    # Chama a DFS inicial
    dfs(origem, [], set(), 0, set())
    return jsonify(rotas), 200


@app.route('/obter_trechos', methods=['GET'])
def obter_trechos():
    cidade_atual = request.args.get('cidade')
    if not cidade_atual:
        return jsonify({"msg": "Cidade não informada"}), 400

    trechos_viagem = carregar_trechos()
    servidores_externos = [SERVER_1_URL, SERVER_3_URL]

    trechos_disponiveis = obter_trechos_plus(cidade_atual, trechos_viagem, servidores_externos)
    return jsonify(trechos_disponiveis), 200

def obter_trechos_plus(cidade_atual, trechos_viagem, servidores_externos):
    # Tenta obter trechos locais primeiro
    trechos_disponiveis = trechos_viagem.get(cidade_atual, {})

    # Se não houver trechos locais, tenta buscar em servidores externos
    if not trechos_disponiveis:
        for url in servidores_externos:
            try:
                response = requests.get(f"{url}/obter_trechos", params={"cidade": cidade_atual})
                if response.status_code == 200:
                    trechos_disponiveis = response.json()
                    if trechos_disponiveis:
                        break
            except requests.RequestException:
                continue

    return trechos_disponiveis



# Fase de preparação (para outros servidores)
@app.route('/prepare', methods=['POST'])
def prepare():
    data = request.get_json()
    caminho = data.get('caminho')
    cpf = data.get('cpf')

    # Verificar disponibilidade e preparar a compra
    trechos_viagem = carregar_trechos()
    sucesso = True

    try :

        if lock.acquire(blocking=False):
            return jsonify({"status": "prepare"}), 200
        else:
            return jsonify({"status": "Passagem não disponível"}), 400
    finally:
        lock.release()  # Libera o lock após a verificação

# Fase de commit (para outros servidores)
@app.route('/commit', methods=['POST'])
def commit():
    data = request.get_json()
    caminho = data.get('caminho')
    cpf = data.get('cpf')
    server_url = None
    # Aqui seria a lógica para efetivamente reservar as passagens
    trechos_viagem = carregar_trechos()
    for i in range(len(caminho) - 1):
        origem = caminho[i]
        destino = caminho[i + 1]
        server = trechos_viagem[origem][destino]["server_id"]
        if(server == "server1"):
            server_url = SERVER_1_URL
        elif(server == "server2"):
            server_url = SERVER_2_URL
        elif(server == "server3"):
            server_url = SERVER_3_URL
        if (origem in trechos_viagem and destino in trechos_viagem[origem]) :
            #remover_uma_vaga(origem, destino, trechos_viagem[origem][destino]["server_id"])
            try:
                if(server_url == None):
                    print("URL Invalido")
                    return 400
                response = requests.post(f"{server_url}/remover_vaga", json={"origem": origem, "destino": destino})
                if response.status_code == 200:
                    print(f"Vaga removida com sucesso.")
                else:
                    print(f"Erro remover vaga do trecho: {response.json().get('msg', '')}")
            except requests.exceptions.RequestException as e:
                print(f"Erro de conexão: {e}")

            #removendo pra testar trechos_viagem[origem][destino]["vagas"] -= 1

    return jsonify({"msg": "Compra confirmada"}), 200

# Fase de rollback (para outros servidores)
@app.route('/rollback', methods=['POST'])
def rollback():
    data = request.get_json()
    caminho = data.get('caminho')
    cpf = data.get('cpf')

    # Aqui seria a lógica para desfazer a operação, se necessário.
    return jsonify({"msg": "Rollback realizado"}), 200

def inicializar_arquivos():
    if not CAMINHO_TRECHOS.exists():
        salvar_trechos({
                "São Paulo-SP": {
                    "Rio de Janeiro-RJ": {"vagas": 10, "preco": 100, "server_id": "server2"},
                    "Brasília-DF": {"vagas": 5, "preco": 150, "server_id": "server2"}
                },
                "Rio de Janeiro-RJ": {
                    "Brasília-DF": {"vagas": 8, "preco": 80, "server_id": "server2"},
                    "Salvador-BA": {"vagas": 2, "preco": 120, "server_id": "server2"}
                },
                "Brasília-DF": {
                    "Salvador-BA": {"vagas": 4, "preco": 90, "server_id": "server2"}
                },
                "Salvador-BA": {
                    "Fortaleza-CE": {"vagas": 3, "preco": 110, "server_id": "server2"}
                },
                "Fortaleza-CE": {
                    "Recife-PE": {"vagas": 6, "preco": 70, "server_id": "server2"}
                },
                "Recife-PE": {
                    "Porto Alegre-RS": {"vagas": 2, "preco": 130, "server_id": "server2"}
                },
                "Porto Alegre-RS": {
                    "Curitiba-PR": {"vagas": 5, "preco": 95, "server_id": "server2"}
                },
                "Curitiba-PR": {
                    "Manaus-AM": {"vagas": 1, "preco": 200, "server_id": "server2"}
                },
                "Manaus-AM": {
                    "Belo Horizonte-MG": {"vagas": 4, "preco": 160, "server_id": "server2"}
                },
                "Belo Horizonte-MG": {
                    "São Paulo-SP": {"vagas": 7, "preco": 85, "server_id": "server2"}
                }
            })
    if not CAMINHO_CLIENTES.exists():
        salvar_clientes([])

# Inicializa os arquivos ao iniciar o servidor
inicializar_arquivos()

if __name__ == '__main__':
    inicializar_arquivos()  # Inicializa os arquivos ao iniciar o servidor
    app.run(port=4000, debug=True)
