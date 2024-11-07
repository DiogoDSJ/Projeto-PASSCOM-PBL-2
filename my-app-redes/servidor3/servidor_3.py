from flask import Flask, request, jsonify
import json
from pathlib import Path
import threading
import requests
import time

app = Flask(__name__)

# Caminhos dos arquivos JSON
CAMINHO_TRECHOS = Path(__file__).parent / "trechos_viagem_s3.json"
CAMINHO_CLIENTES = Path(__file__).parent / "clientes.json"

'''
SERVER_1_URL = "http://localhost:3000" 
SERVER_2_URL = "http://localhost:4000"
SERVER_3_URL = "http://localhost:6000"
'''


SERVER_1_URL = "http://servidor1:3000" #para conectar conteiners de pcs diferentes, basta trocar "servidor1" e demais pelo ip da maquina do servidor
SERVER_2_URL = "http://servidor2:4000"
SERVER_3_URL = "http://servidor3:6000"



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
   return "server3"

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
    if origem in trechos_viagem and destino in trechos_viagem[origem] and trechos_viagem[origem][destino]["vagas"] > 0:
        trechos_viagem[origem][destino]["vagas"] -= 1
        salvar_trechos(trechos_viagem)
        return jsonify({"msg": "Vaga removida com sucesso"}), 200
    else:
        return jsonify({"msg": "Erro na remocao da vaga"}), 400
# Funções para trechos
@app.route('/carregar_trecho_local', methods=['GET'])
def carregar_trechos_locais():
    dados = carregar_json(CAMINHO_TRECHOS)
    return dados.get("trechos", {})

# Funções para trechos
def carregar_trechos(servidores_externos=None):
    # Carregar trechos do servidor local
    dados = carregar_json(CAMINHO_TRECHOS)
    #print(f"get{dados.get("trechos", {})}")
    trechos_locais = dados.get("trechos", {})
    # Inicializa o dicionário para armazenar os trechos combinados
    trechos_combinados = trechos_locais.copy()
    url_servidores = []
    # Se não for fornecida uma lista de servidores, use os padrões
    if servidores_externos is None:
        servidores_externos = [SERVER_1_URL, SERVER_2_URL]
    if("server1") in servidores_externos:
        url_servidores.append(SERVER_1_URL)
    if("server2") in servidores_externos:
        url_servidores.append(SERVER_2_URL)
    # Obter trechos de cada servidor externo
    for url in url_servidores:
        if(url == SERVER_3_URL):
            pass
        try:
            response = requests.get(f"{url}/carregar_trecho_local")
            if response.status_code == 200:
                trechos_externos = response.json()
                # Mesclar os trechos externos no dicionário combinado
                for origem, destinos in trechos_externos.items():
                    if origem not in trechos_combinados:
                        trechos_combinados[origem] = destinos
                    else:
                        trechos_combinados[origem].update(destinos)  # Atualiza com novos destinos
        except requests.RequestException:
            continue  # Se não conseguir obter os dados, apenas continue
    #print(f"trechos return   {trechos_combinados}")
    return trechos_combinados


def salvar_trechos(trechos):
    dados = {"trechos": trechos}
    salvar_json(dados, CAMINHO_TRECHOS)

@app.route('/obter_cidades', methods=['GET'])
def obter_cidades_endpoint():
    try:
        # Carrega os trechos de cada servidor
        dados_servidor1 = carregar_trechos("server1")
        dados_servidor2 = carregar_trechos("server2")
        dados_servidor3 = carregar_trechos("server3")

        # Combina os dados de todos os servidores
        todas_cidades = set()
        
        for dados in [dados_servidor1, dados_servidor2, dados_servidor3]:
            todas_cidades.update(dados.keys())  # Adiciona as cidades de origem
            for destinos in dados.values():
                todas_cidades.update(destinos.keys())  # Adiciona as cidades de destino

        return jsonify(sorted(todas_cidades)), 200

    except Exception as e:
        return jsonify({"msg": "Erro ao obter cidades", "erro": str(e)}), 500


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
        if servidores:
            trechos_viagem = carregar_trechos(servidores)  # Passa a lista de servidores
        else:
            trechos_viagem = carregar_trechos()  # Carrega apenas trechos locais
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
                if(server2): # somente se usa
                    response = requests.post(f"{SERVER_2_URL}/prepare", json={"caminho": caminho, "cpf": cpf})
                    prepare_responses.append(response)

                # Verificar se todos os servidores responderam com sucesso
                if len(prepare_responses) == 0 or all(resp.status_code == 200 for resp in prepare_responses):
                    # Fase de commit
                    if(server1): # somente se usa
                        response1 = requests.post(f"{SERVER_1_URL}/commit", json={"caminho": caminho, "servidores" : servidores}) #manda compra nos outros servidores
                    elif(server2): # somente se usa
                        response1 = requests.post(f"{SERVER_2_URL}/commit", json={"caminho": caminho, "servidores" : servidores}) #manda compra nos outros servidores
                    elif(server3): # somente se usa
                        response1 = requests.post(f"{SERVER_3_URL}/commit", json={"caminho": caminho, "servidores" : servidores}) #manda compra nos outros servidores
                    # Adicionar passagem ao cliente
                    response1res = response1.status_code

                    if response1res == 200:

                        print(server1, server2, server3)
                        novo_id = int(max(cliente.trechos.keys(), default=0)) + 1
                        cliente.trechos[str(novo_id)] = caminho
                        atualizar_cliente(cliente)
                        return jsonify({"msg": "Passagem comprada com sucesso"}), 200
                    
                    else:

                        # Se algum servidor falhar, faz rollback
                        if(server1): # somente se usa
                            requests.post(f"{SERVER_1_URL}/rollback", json={"caminho": caminho, "cpf": cpf})
                        if(server2): # somente se usa
                            requests.post(f"{SERVER_2_URL}/rollback", json={"caminho": caminho, "cpf": cpf})
                        return jsonify({"msg": "Compra cancelada, não foi possível concluir a transação"}), 400

                    
                else:
                    # Se algum servidor falhar, faz rollback
                    if(server1): # somente se usa
                        requests.post(f"{SERVER_1_URL}/rollback", json={"caminho": caminho, "cpf": cpf})
                    if(server2): # somente se usa
                        requests.post(f"{SERVER_2_URL}/rollback", json={"caminho": caminho, "cpf": cpf})
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
    
    trechos_viagem = {}
    servidores_externos = [SERVER_1_URL, SERVER_2_URL, SERVER_3_URL]  # URLs dos servidores externos

    trechos_viagem = coletar_trechos(trechos_viagem, servidores_externos)
    
    rotas = {}
    id_rota = 1

    def dfs(cidade_atual, caminho, visitados, preco_total, servidores_incluidos):
        nonlocal id_rota
        caminho.append(cidade_atual)
        visitados.add(cidade_atual)

        if cidade_atual == destino:
            # Registrar a rota e os servidores incluídos
            rotas[id_rota] = {
                "caminho": caminho[:],
                "preco_total": preco_total,  # Preço total
                "servidores_incluidos": servidores_incluidos[:]  # Lista dos servidores usados na ordem
            }
            id_rota += 1
        else:
            for vizinho, info in trechos_viagem.get(cidade_atual, {}).items():
                if info["vagas"] > 0 and vizinho not in visitados:
                    # Adicionar o server_id à lista de servidores incluídos
                    servidores_incluidos.append(info["server_id"])  # Adiciona o server_id ao caminho

                    # Somar o preço da viagem atual ao preço total e chamar a recursão
                    dfs(vizinho, caminho[:], visitados, preco_total + info["preco"], servidores_incluidos)

                    # Remover o último server_id ao voltar da recursão
                    servidores_incluidos.pop()

        caminho.pop()
        visitados.remove(cidade_atual)


    # Iniciar a DFS a partir da origem com lista para servidores_incluidos
    dfs(origem, [], set(), 0, [])

    return jsonify(rotas), 200




def coletar_trechos(trechos_viagem, servidores_externos):
    """
    Coleta e mescla os trechos de todos os servidores, incluindo os locais e externos.
    """
    trechos_mesclados = trechos_viagem.copy()  # Começa com os trechos locais

    servidores_visitados = set()

    # Coleta trechos dos servidores externos
    for url in servidores_externos:
        if url not in servidores_visitados:
            try:
                servidores_visitados.add(url)
                response = requests.get(f"{url}/carregar_trecho_local", timeout=10)
                if response.status_code == 200:
                    trechos_externos = response.json()

                    # Mescla os trechos externos nos trechos locais
                    for cidade, info in trechos_externos.items():
                        if cidade not in trechos_mesclados:
                            trechos_mesclados[cidade] = info
                        else:
                            # Mescla as informações (adiciona se não existir)
                            trechos_mesclados[cidade].update(info)  # Supondo que `info` seja um dicionário
            except requests.RequestException:
                continue  # Se houver erro, ignora e passa para o próximo servidor
    print(f"trechos mesclados {trechos_mesclados}")
    for origem in trechos_mesclados:
        print(f"origem:{origem} | destino{trechos_mesclados[origem]}")
    return trechos_mesclados









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
        
        
@app.route('/commit', methods=['POST'])
def commit():
    data = request.get_json()
    caminho = data.get('caminho')
    servidores_incluidos = data.get('servidores')
    for i in range(len(caminho) - 1):
        origem = caminho[i]
        destino = caminho[i + 1]
        
        # Identifica o servidor que gerencia o trecho
        server_index = servidores_incluidos[i]  # i-ésimo servidor para o i-ésimo trecho
        if server_index == 'server1':
            server_url = SERVER_1_URL
        elif server_index == 'server2':
            server_url = SERVER_2_URL
        elif server_index == 'server3':
            server_url = SERVER_3_URL
        else:
            continue  # Pula se o servidor não for reconhecido
        
        try:
            if(server_url is None):
                print("URL Invalido")
                return 400
            response = requests.post(f"{server_url}/remover_vaga", json={"origem": origem, "destino": destino})
            if response.status_code == 200:
                print(f"Vaga removida com sucesso.")
            else:
                print(f"Erro remover vaga do trecho: {response.json().get('msg', '')}")
        except requests.exceptions.RequestException as e:
            print(f"Erro de conexão: {e}")
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
                "Rio de Janeiro-RJ": {"vagas": 10, "preco": 120, "server_id": "server3"},
                "Curitiba-PR": {"vagas": 8, "preco": 90, "server_id": "server3"}
            },
            "Rio de Janeiro-RJ": {
                "Belo Horizonte-MG": {"vagas": 10, "preco": 80, "server_id": "server3"},
                "Salvador-BA": {"vagas": 5, "preco": 150, "server_id": "server3"}
            },
            "Curitiba-PR": {
                "Florianópolis-SC": {"vagas": 12, "preco": 60, "server_id": "server3"}
            },
            "Belo Horizonte-MG": {
                "Recife-PE": {"vagas": 4, "preco": 200, "server_id": "server3"}
            },
            "Salvador-BA": {
                "Fortaleza-CE": {"vagas": 3, "preco": 110, "server_id": "server3"}
            },
            "Fortaleza-CE": {
                "Natal-RN": {"vagas": 6, "preco": 75, "server_id": "server3"}
            },
            "Recife-PE": {
                "João Pessoa-PB": {"vagas": 5, "preco": 50, "server_id": "server3"}
            },
            "Natal-RN": {
                "São Luís-MA": {"vagas": 2, "preco": 180, "server_id": "server3"}
            },
            "São Luís-MA": {
                "Belém-PA": {"vagas": 4, "preco": 150, "server_id": "server3"}
            },
            "Belém-PA": {
                "São Luís-MA": {"vagas": 3, "preco": 160, "server_id": "server3"}
            },
            "Florianópolis-SC": {
                "Curitiba-PR": {"vagas": 5, "preco": 70, "server_id": "server3"}
            },
            "João Pessoa-PB": {
                "Recife-PE": {"vagas": 4, "preco": 40, "server_id": "server3"}
            }
        })

    if not CAMINHO_CLIENTES.exists():
        salvar_clientes([])

# Inicializa os arquivos ao iniciar o servidor
inicializar_arquivos()

if __name__ == '__main__':
    inicializar_arquivos()  # Inicializa os arquivos ao iniciar o servidor
    app.run(port=6000, debug=True,host = '0.0.0.0')