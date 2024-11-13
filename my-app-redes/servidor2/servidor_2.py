from flask import Flask, request, jsonify
import json
from pathlib import Path
import threading
import requests
import time
app = Flask(__name__)

# Caminhos dos arquivos JSON
CAMINHO_TRECHOS = Path(__file__).parent / "trechos_viagem_s2.json"
CAMINHO_CLIENTES = Path(__file__).parent / "clientes_servidor2.json"
CAMINHO_ROLLBACK = Path(__file__).parent / 'rollback_data.json'

# URLs dos servidores
SERVER_1_URL = "http://192.168.1.156:3000"  # URL do servidor 1
SERVER_2_URL = "http://192.168.1.156:4000"  # URL do servidor 2 (o atual)
SERVER_3_URL = "http://192.168.1.156:6000"  # URL do servidor 3

# Lock para sincronização de acesso aos arquivos
lock = threading.Lock()

# Classe Cliente: Representa um cliente com seu CPF e os trechos de viagem que ele selecionou
class Cliente:
    def __init__(self, cpf, trechos=None):
        self.cpf = cpf  # Identificador único do cliente
        self.trechos = trechos if trechos is not None else {}  # Dicionário de trechos de viagem

    def to_dict(self):
        # Converte a instância de Cliente para um dicionário (usado para salvar em JSON)
        return {
            'cpf': self.cpf,
            'trechos': self.trechos
        }

    @staticmethod
    def from_dict(data):
        # Converte um dicionário para uma instância de Cliente
        return Cliente(
            cpf=data['cpf'],
            trechos=data.get('trechos', {})
        )
        
# Função para verificar qual servidor está ativo (no caso, "server2")
def get_server():
   return "server2"

# Endpoint para verificar se existe rollback no servidor
@app.route('/check_rollback', methods=['GET'])
def tem_rollback():
    try:
        # Abre e carrega o arquivo JSON de rollback
        with open(CAMINHO_ROLLBACK, 'r') as arquivo:
            dados = json.load(arquivo)
        
        # Verifica se o arquivo contém alguma chave
        if dados:
            return jsonify({"status": "success", "message": "O arquivo JSON contém chaves.", "has_keys": True}), 200
        else:
            return jsonify({"status": "success", "message": "O arquivo JSON está vazio.", "has_keys": False}), 400
    except FileNotFoundError:
        # Retorna resposta caso o arquivo não seja encontrado
        return jsonify({"status": "error", "message": "Arquivo não encontrado."}), 404
    except json.JSONDecodeError:
        # Retorna erro caso o JSON seja inválido
        return jsonify({"status": "error", "message": "Erro ao decodificar o arquivo JSON."}), 400

# Funções auxiliares para manipulação de JSON
def salvar_json(dados, caminho_arquivo):
    try:
        # Salva dados em formato JSON no arquivo especificado
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Erro ao salvar JSON em {caminho_arquivo}: {e}")

def carregar_json(caminho_arquivo):
    try:
        # Carrega dados JSON de um arquivo
        if not caminho_arquivo.exists():
            return {}
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        # Retorna um erro caso o JSON seja inválido
        print(f"Erro: O arquivo {caminho_arquivo} contém JSON inválido.")
        return {}
    except Exception as e:
        print(f"Erro ao carregar JSON de {caminho_arquivo}: {e}")
        return {}

# Funções para manipulação dos clientes
def salvar_clientes(clientes):
    # Salva a lista de clientes em um arquivo JSON
    dados = [cliente.to_dict() for cliente in clientes]
    salvar_json(dados, CAMINHO_CLIENTES)

def carregar_clientes():
    # Carrega a lista de clientes a partir de um arquivo JSON
    dados = carregar_json(CAMINHO_CLIENTES)
    if not isinstance(dados, list):
        print(f"Erro: O arquivo {CAMINHO_CLIENTES} não contém uma lista válida de clientes.")
        return []
    return [Cliente.from_dict(cliente) for cliente in dados]

def encontrar_cliente(cpf):
    # Encontra um cliente pelo CPF
    clientes = carregar_clientes()
    for cliente in clientes:
        if cliente.cpf == cpf:
            return cliente
    return None

@app.route('/encontrar_cliente', methods=['POST'])
def encontrar_cliente_endpoint():
    # Endpoint para encontrar um cliente via CPF
    clientes = carregar_clientes()
    cpf = request.args.get('cpf')
    for cliente in clientes:
        if cliente.cpf == cpf:
            return jsonify(cliente.to_dict())
    return jsonify({"msg": "Cliente nao encontrado"}), 400

def adicionar_cliente(cliente):
    # Adiciona um novo cliente à lista de clientes e salva
    clientes = carregar_clientes()
    clientes.append(cliente)
    salvar_clientes(clientes)

def atualizar_cliente(cliente_atualizado):
    # Atualiza os dados de um cliente existente ou adiciona um novo cliente
    clientes = carregar_clientes()
    for idx, cliente in enumerate(clientes):
        if cliente.cpf == cliente_atualizado.cpf:
            clientes[idx] = cliente_atualizado
            salvar_clientes(clientes)
            return
    adicionar_cliente(cliente_atualizado)

@app.route('/atualizar_cliente', methods=['POST'])
def atualizar_cliente_endpoint():
    # Endpoint para atualizar ou adicionar um cliente
    clientes = carregar_clientes()
    data = request.json
    cliente_atualizado = Cliente(**data)
    for idx, cliente in enumerate(clientes):
        if cliente.cpf == cliente_atualizado.cpf:
            clientes[idx] = cliente_atualizado
            salvar_clientes(clientes)
            return jsonify({"msg": "Cliente atualizado"}), 200
    # Se não encontrar, adicionar
    adicionar_cliente(cliente_atualizado)
    return jsonify({"msg": "Cliente adicionado"}), 200


@app.route('/remover_vaga', methods=['POST'])
def remover_uma_vaga():
    # Endpoint para remover uma vaga de um trecho específico de viagem
    data = request.get_json()
    origem = data.get("origem")
    destino = data.get("destino")
    trechos_viagem = carregar_trechos()
    trechos_rollback = carregar_json(CAMINHO_ROLLBACK)
    if origem in trechos_viagem and destino in trechos_viagem[origem] and trechos_viagem[origem][destino]["vagas"] > 0:
        # Se o trecho e a vaga estiverem disponíveis, realiza a remoção
        trechos_rollback[origem] = trechos_viagem[origem]
        salvar_json(trechos_rollback, CAMINHO_ROLLBACK)
        trechos_viagem[origem][destino]["vagas"] -= 1
        salvar_trechos(trechos_viagem)
        return jsonify({"msg": "Vaga removida com sucesso"}), 200
    else:
        return jsonify({"msg": "Erro na remocao da vaga"}), 400

# Funções para manipulação de trechos
@app.route('/carregar_trecho_local', methods=['GET'])
def carregar_trechos_locais():
    # Endpoint para carregar os trechos locais do arquivo
    dados = carregar_json(CAMINHO_TRECHOS)
    return dados.get("trechos", {})

def carregar_trechos(servidores_externos=None):
    # Carrega os trechos de viagem de servidores locais e externos
    dados = carregar_json(CAMINHO_TRECHOS)
    trechos_locais = dados.get("trechos", {})
    trechos_combinados = trechos_locais.copy()
    url_servidores = []
    # Se não for fornecida uma lista de servidores, usa os servidores padrão
    if servidores_externos is None:
        servidores_externos = [SERVER_1_URL, SERVER_3_URL]
    if "server1" in servidores_externos:
        url_servidores.append(SERVER_1_URL)
    if "server3" in servidores_externos:
        url_servidores.append(SERVER_3_URL)
    # Obter trechos de cada servidor externo
    for url in url_servidores:
        if(url == SERVER_2_URL):
            pass
        try:
            response = requests.get(f"{url}/carregar_trecho_local")
            if response.status_code == 200:
                trechos_externos = response.json()
                for origem, destinos in trechos_externos.items():
                    if origem not in trechos_combinados:
                        trechos_combinados[origem] = destinos
                    else:
                        trechos_combinados[origem].update(destinos)
        except requests.RequestException:
            continue  # Se não conseguir obter os dados, apenas continue
    return trechos_combinados

# Função para salvar os trechos de viagem no arquivo JSON
def salvar_trechos(trechos):
    dados = {"trechos": trechos}
    salvar_json(dados, CAMINHO_TRECHOS)  # Chama a função salvar_json para gravar os dados no arquivo

# Endpoint para obter todas as cidades disponíveis a partir dos trechos dos servidores
@app.route('/obter_cidades', methods=['GET'])
def obter_cidades_endpoint():
    try:
        # Carrega os trechos de viagem de três servidores diferentes
        dados_servidor1 = carregar_trechos("server1")
        dados_servidor2 = carregar_trechos("server2")
        dados_servidor3 = carregar_trechos("server3")

        todas_cidades = set()  # Um set para armazenar todas as cidades, garantindo que não haja duplicatas
        
        # Adiciona todas as cidades de origem e destino de todos os servidores
        for dados in [dados_servidor1, dados_servidor2, dados_servidor3]:
            todas_cidades.update(dados.keys())  # Adiciona as cidades de origem
            for destinos in dados.values():
                todas_cidades.update(destinos.keys())  # Adiciona as cidades de destino

        return jsonify(sorted(todas_cidades)), 200  # Retorna as cidades ordenadas em formato JSON

    except Exception as e:
        return jsonify({"msg": "Erro ao obter cidades", "erro": str(e)}), 500  # Retorna erro se algo falhar

# Endpoint para cadastro de um novo cliente
@app.route('/cadastro', methods=['POST'])
def cadastro():
    data = request.get_json()  # Recebe os dados do cliente enviados no corpo da requisição
    cpf = data.get('cpf')

    if not cpf:
        return jsonify({"msg": "CPF é obrigatório"}), 400  # Retorna erro caso o CPF não seja enviado

    if not cpf.isdigit() or len(cpf) != 11:
        return jsonify({"msg": "CPF inválido. Deve conter exatamente 11 dígitos."}), 400  # Valida o CPF

    with lock:  # Usa o lock para garantir acesso exclusivo à manipulação de clientes
        if encontrar_cliente(cpf):
            return jsonify({"msg": "Cliente já existe [servidor2]"}), 409  # Se o cliente já existe, retorna erro

        cliente = Cliente(cpf=cpf)  # Cria um novo cliente
        adicionar_cliente(cliente)  # Adiciona o cliente ao sistema

    return jsonify({"msg": "Cadastro realizado com sucesso [servidor2]"}), 200  # Sucesso no cadastro

# Endpoint para listar todos os trechos de viagem
@app.route('/trechos', methods=['GET'])
def listar_trechos():
    trechos = carregar_trechos()  # Carrega os trechos disponíveis
    return jsonify(trechos), 200  # Retorna os trechos em formato JSON

# Endpoint para iniciar a compra de uma passagem
@app.route('/comprar', methods=['POST'])
def preparar_compra():
    data = request.get_json()  # Recebe os dados necessários para a compra
    caminho = data.get('caminho')  # Lista de cidades a serem percorridas, ex: ["CidadeA", "CidadeB", "CidadeC"]
    cpf = data.get('cpf')
    servidores = data.get('servidores')  # Lista de servidores envolvidos na compra
    
    # Validações dos dados recebidos
    if not caminho or not isinstance(caminho, list) or len(caminho) < 2:
        return jsonify({"msg": "Caminho inválido"}), 400  # Verifica se o caminho tem pelo menos 2 cidades

    if not cpf:
        return jsonify({"msg": "CPF é obrigatório"}), 400

    if not cpf.isdigit() or len(cpf) != 11:
        return jsonify({"msg": "CPF inválido. Deve conter exatamente 11 dígitos."}), 400

    print(f"servidores1{servidores}")
    if servidores:
        trechos_viagem = carregar_trechos(servidores)  # Carrega os trechos dos servidores envolvidos
    else:
        trechos_viagem = carregar_trechos()  # Carrega apenas os trechos locais se nenhum servidor for especificado

    cliente = encontrar_cliente(cpf)  # Busca o cliente pelo CPF
    server1 = server2 = server3 = False  # Flags para verificar em quais servidores a compra ocorrerá
    sucesso = True  # Flag para determinar se a compra pode ser realizada

    trecho_copy = caminho.copy()  # Cria uma cópia do caminho para verificar a disponibilidade dos trechos

    # Verifica se todos os trechos do caminho estão disponíveis
    for i in range(len(trecho_copy)-1):
        origem = trecho_copy[i]
        destino = trecho_copy[i+1]
        if origem not in trechos_viagem or destino not in trechos_viagem[origem]:
            sucesso = False  # Se o trecho não existir, a compra falha
            break
        if trechos_viagem[origem][destino]["vagas"] < 1:
            sucesso = False  # Se não houver vagas, a compra falha
            break

    # Verifica se os servidores envolvidos na compra estão configurados corretamente
    for servidor in servidores:
        if servidor == "server1":
            server1 = True
        elif servidor == "server2":
            server2 = True
        elif servidor == "server3":
            server3 = True

    # Verifica rollback nos servidores antes de realizar a compra
    if server1:
        response = requests.get(f"{SERVER_1_URL}/check_rollback")  # Verifica se o servidor 1 possui rollback
        status_code = response.status_code
        if status_code == 200:
            print("Rollback encontrado, fazendo rollback antes da compra.")
            requests.post(f"{SERVER_1_URL}/rollback")  # Se houver rollback, faz rollback no servidor 1

        resposta1 = requests.post(f"{SERVER_1_URL}/cadastro", json={"cpf": cpf})  # Cadastra o cliente no servidor 1
        if resposta1.status_code not in [200, 409]:
            return jsonify({"msg": "Não foi possível cadastrar o cliente em todos os servidores envolvidos na rota"}), 400

    if server2:
        response = requests.get(f"{SERVER_2_URL}/check_rollback")  # Verifica se o servidor 2 possui rollback
        status_code = response.status_code
        if status_code == 200:
            print("Rollback encontrado, fazendo rollback antes da compra.")
            requests.post(f"{SERVER_2_URL}/rollback")  # Se houver rollback, faz rollback no servidor 2

        resposta2 = requests.post(f"{SERVER_2_URL}/cadastro", json={"cpf": cpf})  # Cadastra o cliente no servidor 2
        if resposta2.status_code not in [200, 409]:
            return jsonify({"msg": "Não foi possível cadastrar o cliente em todos os servidores envolvidos na rota"}), 400

    if server3:
        response = requests.get(f"{SERVER_3_URL}/check_rollback")  # Verifica se o servidor 3 possui rollback
        status_code = response.status_code
        if status_code == 200:
            print("Rollback encontrado, fazendo rollback antes da compra.")
            requests.post(f"{SERVER_3_URL}/rollback")  # Se houver rollback, faz rollback no servidor 3

        resposta3 = requests.post(f"{SERVER_3_URL}/cadastro", json={"cpf": cpf})  # Cadastra o cliente no servidor 3
        if resposta3.status_code not in [200, 409]:
            return jsonify({"msg": "Não foi possível cadastrar o cliente em todos os servidores envolvidos na rota"}), 400

    # Se os trechos estão disponíveis, prepara a compra
    if sucesso:
        try:
            prepare_responses = []  # Lista para armazenar as respostas dos servidores durante a fase de preparação

            # Envia a preparação da compra para cada servidor envolvido
            if server1:
                response = requests.post(f"{SERVER_1_URL}/prepare", json={"caminho": caminho, "servidores": servidores})
            if server2:
                response = requests.post(f"{SERVER_2_URL}/prepare", json={"caminho": caminho, "servidores": servidores})
                prepare_responses.append(response)
            if server3:
                response = requests.post(f"{SERVER_3_URL}/prepare", json={"caminho": caminho, "servidores": servidores})
                prepare_responses.append(response)

            # Verifica se todos os servidores responderam com sucesso
            if len(prepare_responses) == 0 or all(resp.status_code == 200 for resp in prepare_responses):
                # Fase de commit, envia a confirmação de compra para todos os servidores
                rotas_server1 = rotas_server2 = rotas_server3 = []

                # Organiza as rotas para cada servidor
                for i in range(len(servidores)):
                    lista_server1 = lista_server2 = lista_server3 = []
                    if servidores[i] == "server1":
                        lista_server1.append(caminho[i])
                        lista_server1.append(caminho[i + 1])
                        rotas_server1.append(lista_server1)
                    elif servidores[i] == "server2":
                        lista_server2.append(caminho[i])
                        lista_server2.append(caminho[i + 1])
                        rotas_server2.append(lista_server2)
                    elif servidores[i] == "server3":
                        lista_server3.append(caminho[i])
                        lista_server3.append(caminho[i + 1])
                        rotas_server3.append(lista_server3)

                # Envia as rotas para os servidores confirmarem a compra
                if server1:
                    requests.post(f"{SERVER_1_URL}/commit", json={"caminho": caminho, "rotas_server": rotas_server1, "cpf": cpf})
                if server2:
                    requests.post(f"{SERVER_2_URL}/commit", json={"caminho": caminho, "rotas_server": rotas_server2, "cpf": cpf})
                if server3:
                    requests.post(f"{SERVER_3_URL}/commit", json={"caminho": caminho, "rotas_server": rotas_server3, "cpf": cpf})

                return jsonify({"msg": "Passagem comprada com sucesso"}), 200  # Retorna sucesso se a compra foi concluída

            else:
                # Se algum servidor falhou, realiza o rollback em todos
                if server1:
                    requests.post(f"{SERVER_1_URL}/rollback")
                if server2:
                    requests.post(f"{SERVER_2_URL}/rollback")
                if server3:
                    requests.post(f"{SERVER_3_URL}/rollback")
                return jsonify({"msg": "Compra cancelada, não foi possível concluir a transação"}), 400  # Cancelamento da compra

        except requests.RequestException:
            return jsonify({"msg": "Erro ao comunicar com os servidores externos."}), 500  # Erro de comunicação com os servidores
    else:
        return jsonify({"msg": "Passagem não disponível"}), 400  # Se os trechos não estão disponíveis
    
# Endpoint para visualizar as passagens de um cliente específico
@app.route('/passagens', methods=['GET'])
def ver_passagens():
    cpf = request.args.get('cpf')  # Obtém o CPF do cliente passado como parâmetro de consulta na URL
    if not cpf:
        return jsonify({"msg": "CPF é obrigatório"}), 400  # Retorna erro se o CPF não for fornecido

    if not cpf.isdigit() or len(cpf) != 11:
        return jsonify({"msg": "CPF inválido. Deve conter exatamente 11 dígitos."}), 400  # Valida o CPF

    cliente = encontrar_cliente(cpf)  # Procura o cliente com o CPF fornecido
    if not cliente:
        return jsonify({"msg": "Cliente não encontrado."}), 404  # Retorna erro se o cliente não for encontrado

    return jsonify(cliente.trechos), 200  # Retorna os trechos (passagens) do cliente

# Endpoint para buscar rotas de viagem entre duas cidades (origem e destino)
@app.route('/buscar', methods=['GET'])
def buscar_rotas():
    origem = request.args.get('origem')  # Obtém a cidade de origem da consulta
    destino = request.args.get('destino')  # Obtém a cidade de destino da consulta

    if not origem or not destino:
        return jsonify({"msg": "Origem e destino são obrigatórios"}), 400  # Retorna erro se origem ou destino não forem fornecidos
    
    # Inicializa o dicionário de trechos de viagem
    trechos_viagem = {}
    servidores_externos = [SERVER_1_URL, SERVER_2_URL, SERVER_3_URL]  # URLs dos servidores externos

    # Coleta os trechos de viagem dos servidores externos e os adiciona aos trechos locais
    trechos_viagem = coletar_trechos(trechos_viagem, servidores_externos)
    
    rotas = {}  # Dicionário para armazenar as rotas encontradas
    id_rota = 1  # Identificador único para as rotas

    # Função recursiva de busca em profundidade (DFS) para encontrar todas as rotas possíveis
    def dfs(cidade_atual, caminho, visitados, preco_total, servidores_incluidos):
        nonlocal id_rota  # Permite modificar a variável id_rota dentro da função recursiva
        caminho.append(cidade_atual)  # Adiciona a cidade atual ao caminho
        visitados.add(cidade_atual)  # Marca a cidade atual como visitada

        if cidade_atual == destino:
            # Quando o destino é alcançado, registra a rota e os servidores envolvidos
            rotas[id_rota] = {
                "caminho": caminho[:],  # Cópia do caminho
                "preco_total": preco_total,  # Preço total da rota
                "servidores_incluidos": servidores_incluidos[:]  # Lista de servidores usados
            }
            id_rota += 1  # Incrementa o ID da rota
        else:
            # Busca recursivamente pelos destinos a partir da cidade atual
            for vizinho, info in trechos_viagem.get(cidade_atual, {}).items():
                if info["vagas"] > 0 and vizinho not in visitados:
                    # Verifica se há vagas e se a cidade vizinha não foi visitada
                    servidores_incluidos.append(info["server_id"])  # Adiciona o servidor à lista de servidores usados
                    dfs(vizinho, caminho[:], visitados, preco_total + info["preco"], servidores_incluidos)  # Chama recursão para o próximo destino
                    servidores_incluidos.pop()  # Remove o último servidor ao voltar da recursão

        caminho.pop()  # Remove a cidade atual do caminho
        visitados.remove(cidade_atual)  # Marca a cidade atual como não visitada

    # Inicia a busca a partir da origem
    dfs(origem, [], set(), 0, [])

    return jsonify(rotas), 200  # Retorna as rotas encontradas

# Função para coletar os trechos de viagem de todos os servidores, mesclando-os com os locais
def coletar_trechos(trechos_viagem, servidores_externos):
    """
    Coleta e mescla os trechos de todos os servidores, incluindo os locais e externos.
    """
    trechos_mesclados = trechos_viagem.copy()  # Começa com os trechos locais

    servidores_visitados = set()

    # Coleta os trechos dos servidores externos
    for url in servidores_externos:
        if url not in servidores_visitados:
            try:
                servidores_visitados.add(url)  # Marca o servidor como visitado
                response = requests.get(f"{url}/carregar_trecho_local", timeout=10)  # Faz a requisição para obter os trechos
                if response.status_code == 200:
                    trechos_externos = response.json()  # Extrai os dados dos trechos externos

                    # Mescla os trechos externos com os locais
                    for cidade, info in trechos_externos.items():
                        if cidade not in trechos_mesclados:
                            trechos_mesclados[cidade] = info
                        else:
                            trechos_mesclados[cidade].update(info)  # Atualiza os trechos se já existir a cidade
            except requests.RequestException:
                continue  # Ignora erros de requisição e continua com o próximo servidor
    print(f"trechos mesclados {trechos_mesclados}")  # Exibe os trechos mesclados no log
    for origem in trechos_mesclados:
        print(f"origem:{origem} | destino{trechos_mesclados[origem]}")  # Exibe as origens e destinos dos trechos
    return trechos_mesclados  # Retorna os trechos mesclados

# Fase de preparação para a compra da passagem (para outros servidores)
@app.route('/prepare', methods=['POST'])
def prepare():
    data = request.get_json()  # Recebe os dados da requisição (caminho e servidores)
    caminho = data.get('caminho')
    servidores_incluidos = data.get('servidores')
    
    # Para cada trecho no caminho, tenta remover uma vaga do servidor responsável
    for i in range(len(caminho) - 1):
        origem = caminho[i]
        destino = caminho[i + 1]
        
        # Identifica o servidor que gerencia o trecho
        server_index = servidores_incluidos[i]
        if server_index == 'server1':
            server_url = SERVER_1_URL
        elif server_index == 'server2':
            server_url = SERVER_2_URL
        elif server_index == 'server3':
            server_url = SERVER_3_URL
        else:
            continue  # Pula se o servidor não for reconhecido
        
        msg1 = (f"Pronto para o commit.")  # Mensagem para o sucesso
        msg2 = (f"Prepare falhou, desistir do commit.")  # Mensagem para falha na preparação

        try:
            if(server_url is None):
                print("URL Invalido")
                return 400
            response = requests.post(f"{server_url}/remover_vaga", json={"origem": origem, "destino": destino}, timeout=10)  # Solicita remoção de vaga
            if response.status_code == 200:
                print(f"Vaga removida com sucesso.")  # Exibe sucesso na remoção da vaga
            else:
                print(f"Erro remover vaga do trecho: {response.json().get('msg', '')}")  # Exibe erro ao tentar remover a vaga
                return jsonify({"msg": msg1}), 409  # Retorna erro caso falhe
        except requests.exceptions.RequestException as e:
            print(f"Erro de conexão: {e}")  # Exibe erro de conexão
        except TimeoutError:
            return jsonify({"msg": msg1}), 409  # Retorna erro em caso de timeout
    return jsonify({"msg": msg2}), 200  # Retorna sucesso na preparação

# Fase de commit para a compra da passagem (para outros servidores)
@app.route('/commit', methods=['POST'])
def commit():
    data = request.get_json()  # Recebe os dados da requisição (rotas e CPF)
    rotas_server = data.get("rotas_server")
    cpf = data.get("cpf")
    clientecopy = encontrar_cliente(cpf)  # Encontra o cliente pelo CPF
    for i in rotas_server:
        # Cria um novo ID para o trecho e adiciona no histórico de passagens do cliente
        novo_id = max(map(int, clientecopy.trechos.keys()), default=0) + 1
        clientecopy.trechos[str(novo_id)] = i
    
    atualizar_cliente(clientecopy)  # Atualiza o cliente no sistema
    salvar_json({}, CAMINHO_ROLLBACK)  # Limpa o arquivo de rollback

# Fase de rollback para reverter alterações em caso de falha
@app.route('/rollback', methods=['POST'])
def rollback():
    lock.acquire()  # Adquire o lock para evitar condições de corrida
    try:
        rollback_arquivo = carregar_json(CAMINHO_ROLLBACK)  # Carrega o arquivo de rollback
        trechos_viagem = carregar_trechos_locais  # Carrega os trechos locais
        for origem, destinos in rollback_arquivo.items():
            for destino, detalhes in destinos.items():
                if detalhes['server_id'] == get_server():  # Verifica se o trecho foi alterado pelo servidor atual
                    trechos_viagem[origem][destino]["vagas"] = rollback_arquivo[origem][destino]["vagas"]  # Restaura as vagas
                    rollback_arquivo.pop(origem)  # Remove a origem do arquivo de rollback
        
        salvar_trechos(trechos_viagem)  # Salva os trechos atualizados
        salvar_json(rollback_arquivo, CAMINHO_ROLLBACK)  # Salva o arquivo de rollback atualizado
    finally:
        lock.release()  # Libera o lock
    return jsonify({"msg": "Rollback realizado"}), 200  # Retorna sucesso no rollback

# Função para inicializar os arquivos de trechos e clientes, caso não existam
def inicializar_arquivos():
    if not CAMINHO_TRECHOS.exists():
        salvar_trechos({
            "Belo Horizonte-MG": {
                "Vitória-ES": {"vagas": 10, "preco": 95, "server_id": "server2"},
                "São Paulo-SP": {"vagas": 7, "preco": 130, "server_id": "server2"}
            },
            "Vitória-ES": {
                "Rio de Janeiro-RJ": {"vagas": 2, "preco": 70, "server_id": "server2"},
                "Salvador-BA": {"vagas": 5, "preco": 160, "server_id": "server2"},
                "Belo Horizonte-MG": {"vagas": 8, "preco": 100, "server_id": "server2"}
            },
            "São Paulo-SP": {
                "Curitiba-PR": {"vagas": 12, "preco": 100, "server_id": "server2"},
                "Porto Alegre-RS": {"vagas": 3, "preco": 180, "server_id": "server2"},
                "Belo Horizonte-MG": {"vagas": 6, "preco": 120, "server_id": "server2"}
            },
            "Curitiba-PR": {
                "Florianópolis-SC": {"vagas": 6, "preco": 80, "server_id": "server2"},
                "São Paulo-SP": {"vagas": 5, "preco": 110, "server_id": "server2"}
            },
            "Porto Alegre-RS": {
                "Canoas-RS": {"vagas": 4, "preco": 30, "server_id": "server2"},
                "São Paulo-SP": {"vagas": 2, "preco": 150, "server_id": "server2"}
            },
            "Salvador-BA": {
                "Aracaju-SE": {"vagas": 2, "preco": 90, "server_id": "server2"},
                "Vitória-ES": {"vagas": 3, "preco": 100, "server_id": "server2"}
            },
            "Aracaju-SE": {
                "Maceió-AL": {"vagas": 4, "preco": 65, "server_id": "server2"},
                "Salvador-BA": {"vagas": 3, "preco": 80, "server_id": "server2"}
            },
            "Maceió-AL": {
                "Recife-PE": {"vagas": 7, "preco": 55, "server_id": "server2"},
                "Aracaju-SE": {"vagas": 5, "preco": 70, "server_id": "server2"}
            },
            "Recife-PE": {
                "João Pessoa-PB": {"vagas": 6, "preco": 45, "server_id": "server2"},
                "Maceió-AL": {"vagas": 4, "preco": 60, "server_id": "server2"}
            },
            "João Pessoa-PB": {
                "Recife-PE": {"vagas": 5, "preco": 40, "server_id": "server2"}
            },
            "Florianópolis-SC": {
                "Curitiba-PR": {"vagas": 5, "preco": 50, "server_id": "server2"}
            }
        })

    if not CAMINHO_CLIENTES.exists():
        salvar_clientes([])  # Se não houver clientes, inicializa uma lista vazia

# Inicializa os arquivos ao iniciar o servidor
inicializar_arquivos()

if __name__ == '__main__':
    inicializar_arquivos()  # Inicializa os arquivos ao iniciar o servidor
    app.run(port=4000, debug=True,host = '0.0.0.0', threaded=True)  # Inicia o servidor Flask

