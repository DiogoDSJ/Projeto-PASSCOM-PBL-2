from flask import Flask, request, jsonify
import json
from pathlib import Path
import threading
import requests
import time

app = Flask(__name__)

# Caminhos dos arquivos JSON
CAMINHO_TRECHOS = Path(__file__).parent / "trechos_viagem_s1.json"
CAMINHO_CLIENTES = Path(__file__).parent / "clientes_servidor1.json"
CAMINHO_ROLLBACK = Path(__file__).parent / 'rollback_data.json'

# Lock para sincronização de acesso aos arquivos
lock = threading.Lock()


'''SERVER_1_URL = "http://172.16.103.244:3000" 
SERVER_2_URL = "http://172.16.103.244:4000" 
SERVER_3_URL = "http://172.16.103.244:6000" '''


SERVER_1_URL = "http://192.168.1.156:3000" # URL do servidor 1
SERVER_2_URL = "http://192.168.1.156:4000" # URL do servidor 2 
SERVER_3_URL = "http://192.168.1.156:6000"  # URL do servidor 3


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
   return "server1"

@app.route('/check_rollback', methods=['GET'])
def tem_rollback():
    try:
        # Abre e carrega o arquivo JSON
        with open(CAMINHO_ROLLBACK, 'r') as arquivo:
            dados = json.load(arquivo)
        
        # Verifica se o JSON contém alguma chave
        if dados:
            return jsonify({"status": "success", "message": "O arquivo JSON contém chaves.", "has_keys": True}), 200
        else:
            return jsonify({"status": "success", "message": "O arquivo JSON está vazio.", "has_keys": False}), 409
    except FileNotFoundError:
        # Retorna resposta JSON para arquivo não encontrado
        return jsonify({"status": "error", "message": "Arquivo não encontrado."}), 404
    except json.JSONDecodeError:
        # Retorna resposta JSON para JSON inválido
        return jsonify({"status": "error", "message": "Erro ao decodificar o arquivo JSON."}), 400

# Funções auxiliares para manipulação de JSON
def salvar_json(dados, caminho_arquivo):
    try:
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Erro ao salvar JSON em {caminho_arquivo}: {e}")


def carregar_json(caminho_arquivo):
    try:
        # Verifica se o arquivo existe. Se não existir, retorna um dicionário vazio.
        if not caminho_arquivo.exists():
            return {}
        # Abre o arquivo JSON no modo de leitura com codificação UTF-8.
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            # Carrega e retorna o conteúdo do arquivo como um dicionário.
            return json.load(f)
    # Trata erro caso o JSON tenha formato inválido.
    except json.JSONDecodeError:
        print(f"Erro: O arquivo {caminho_arquivo} contém JSON inválido.")
        return {}
    # Trata qualquer outro tipo de erro que possa ocorrer ao carregar o arquivo.
    except Exception as e:
        print(f"Erro ao carregar JSON de {caminho_arquivo}: {e}")
        return {}


# Função para salvar uma lista de clientes em um arquivo JSON
def salvar_clientes(clientes):
    # Converte cada cliente para um dicionário usando o método to_dict()
    dados = [cliente.to_dict() for cliente in clientes]
    # Salva os dados no arquivo especificado em CAMINHO_CLIENTES
    salvar_json(dados, CAMINHO_CLIENTES)


def carregar_clientes():
    # Carrega os dados do arquivo JSON de clientes
    dados = carregar_json(CAMINHO_CLIENTES)
    # Retorna uma lista vazia se não houver clientes ou se os dados não forem uma lista válida
    if not isinstance(dados, list):
        print(f"Erro: O arquivo {CAMINHO_CLIENTES} não contém uma lista válida de clientes.")
        return []
    # Converte cada dicionário de cliente em um objeto Cliente
    return [Cliente.from_dict(cliente) for cliente in dados]

def encontrar_cliente(cpf):
    # Carrega a lista de clientes
    clientes = carregar_clientes()
    # Procura um cliente com o CPF correspondente
    for cliente in clientes:
        if cliente.cpf == cpf:
            return cliente
    # Retorna None se o cliente não for encontrado
    return None



@app.route('/encontrar_cliente', methods=['POST'])
def encontrar_cliente_endpoint():
    # Carrega a lista de clientes
    clientes = carregar_clientes()
    # Obtém o CPF a partir dos parâmetros da requisição
    cpf = request.args.get('cpf')
    # Procura um cliente com o CPF correspondente
    for cliente in clientes:
        if cliente.cpf == cpf:
            # Retorna o cliente encontrado em formato JSON
            return jsonify(cliente.to_dict())
    # Retorna uma mensagem de erro se o cliente não for encontrado
    return jsonify({"msg": "Cliente nao encontrado"}), 400

def adicionar_cliente(cliente):
    # Carrega a lista de clientes
    clientes = carregar_clientes()
    # Adiciona o novo cliente à lista
    clientes.append(cliente)
    # Salva a lista atualizada de clientes no arquivo JSON
    salvar_clientes(clientes)


def atualizar_cliente(cliente_atualizado):
    # Carrega a lista de clientes
    clientes = carregar_clientes()
    # Procura o cliente pelo CPF
    for idx, cliente in enumerate(clientes):
        if cliente.cpf == cliente_atualizado.cpf:
            # Atualiza o cliente encontrado com as novas informações
            clientes[idx] = cliente_atualizado
            # Salva a lista atualizada de clientes
            salvar_clientes(clientes)
            return
    # Adiciona o cliente se ele não for encontrado
    adicionar_cliente(cliente_atualizado)

@app.route('/atualizar_cliente', methods=['POST'])
def atualizar_cliente_endpoint():
    # Carrega a lista de clientes
    clientes = carregar_clientes()
    # Obtém os dados do cliente atualizado a partir do JSON da requisição
    data = request.json
    # Cria um objeto Cliente usando os dados recebidos
    cliente_atualizado = Cliente(**data)
    # Procura o cliente pelo CPF
    for idx, cliente in enumerate(clientes):
        if cliente.cpf == cliente_atualizado.cpf:
            # Atualiza o cliente encontrado
            clientes[idx] = cliente_atualizado
            # Salva a lista atualizada de clientes
            salvar_clientes(clientes)
            return jsonify({"msg": "Cliente atualizado"}), 200
    # Adiciona o cliente se ele não for encontrado
    adicionar_cliente(cliente_atualizado)
    return jsonify({"msg": "Cliente adicionado"}), 200



@app.route('/remover_vaga', methods=['POST'])
def remover_uma_vaga():
    # Obtém os dados da requisição em formato JSON
    data = request.get_json()
    # Extrai a origem e o destino do trecho a partir dos dados recebidos
    origem = data.get("origem")
    destino = data.get("destino")
    # Carrega os trechos de viagem e os dados de rollback
    trechos_viagem = carregar_trechos()
    trechos_rollback = carregar_json(CAMINHO_ROLLBACK)
    
    # Verifica se o trecho existe e se há vagas disponíveis
    if origem in trechos_viagem and destino in trechos_viagem[origem] and trechos_viagem[origem][destino]["vagas"] > 0:
        # Salva o estado atual do trecho no arquivo de rollback
        trechos_rollback[origem] = trechos_viagem[origem]
        salvar_json(trechos_rollback, CAMINHO_ROLLBACK)
        # Reduz o número de vagas disponíveis no trecho específico
        trechos_viagem[origem][destino]["vagas"] -= 1
        # Salva os trechos de viagem atualizados
        salvar_trechos(trechos_viagem)
        return jsonify({"msg": "Vaga removida com sucesso"}), 200
    else:
        # Retorna um erro se não foi possível remover a vaga
        return jsonify({"msg": "Erro na remocao da vaga"}), 400

# Função para carregar trechos locais
@app.route('/carregar_trecho_local', methods=['GET'])
def carregar_trechos_locais():
    # Carrega os dados dos trechos a partir do arquivo JSON
    dados = carregar_json(CAMINHO_TRECHOS)
    # Retorna apenas os dados de trechos, ou um dicionário vazio se não houver
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
        servidores_externos = [SERVER_2_URL, SERVER_3_URL]
    if("server2") in servidores_externos:
        url_servidores.append(SERVER_2_URL)
    if("server3") in servidores_externos:
        url_servidores.append(SERVER_3_URL)
    # Obter trechos de cada servidor externo
    for url in url_servidores:
        if(url == SERVER_1_URL):
            pass
        try:
            response = requests.get(f"{url}/carregar_trecho_local")
            if response.status_code == 200:
                trechos_externos = response.json()
                #print(f"trechos externos{trechos_externos}")
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
    # Envolve os dados dos trechos em um dicionário e salva no arquivo JSON especificado
    dados = {"trechos": trechos}
    salvar_json(dados, CAMINHO_TRECHOS)

@app.route('/obter_cidades', methods=['GET'])
def obter_cidades_endpoint():
    try:
        # Carrega os dados de trechos dos três servidores
        dados_servidor1 = carregar_trechos("server1")
        dados_servidor2 = carregar_trechos("server2")
        dados_servidor3 = carregar_trechos("server3")

        # Conjunto para armazenar todas as cidades sem duplicatas
        todas_cidades = set()
        
        # Itera sobre os dados de cada servidor para coletar cidades de origem e destino
        for dados in [dados_servidor1, dados_servidor2, dados_servidor3]:
            todas_cidades.update(dados.keys())  # Adiciona as cidades de origem
            for destinos in dados.values():
                todas_cidades.update(destinos.keys())  # Adiciona as cidades de destino

        # Retorna a lista de cidades ordenada em formato JSON
        return jsonify(sorted(todas_cidades)), 200

    except Exception as e:
        # Retorna uma mensagem de erro e o detalhe do erro em caso de falha
        return jsonify({"msg": "Erro ao obter cidades", "erro": str(e)}), 500


# Endpoint para cadastro de cliente (sem senha)
@app.route('/cadastro', methods=['POST'])
def cadastro():
    # Obtém os dados da requisição em formato JSON
    data = request.get_json()
    # Extrai o CPF dos dados recebidos
    cpf = data.get('cpf')

    # Verifica se o CPF foi fornecido
    if not cpf:
        return jsonify({"msg": "CPF é obrigatório"}), 400

    # Valida o formato do CPF (deve conter exatamente 11 dígitos numéricos)
    if not cpf.isdigit() or len(cpf) != 11:
        return jsonify({"msg": "CPF inválido. Deve conter exatamente 11 dígitos."}), 400

    with lock:
        # Verifica se o cliente já está cadastrado
        if encontrar_cliente(cpf):
            return jsonify({"msg": "Cliente já existe [servidor1]"}), 409

        # Cria um novo cliente com o CPF fornecido e o adiciona ao sistema
        cliente = Cliente(cpf=cpf)
        adicionar_cliente(cliente)

    # Retorna uma mensagem de sucesso se o cliente foi cadastrado
    return jsonify({"msg": "Cadastro realizado com sucesso [servidor1]"}), 200

# Endpoint para listar todos os trechos disponíveis
@app.route('/trechos', methods=['GET'])
def listar_trechos():
    # Carrega os dados dos trechos disponíveis
    trechos = carregar_trechos()
    # Retorna os trechos em formato JSON
    return jsonify(trechos), 200


# Endpoint para preparar a compra da passagem
@app.route('/comprar', methods=['POST'])
def preparar_compra():
    data = request.get_json()  # Obtém os dados do corpo da requisição
    caminho = data.get('caminho')  # Lista de cidades, ex: ["CidadeA", "CidadeB", "CidadeC"]
    cpf = data.get('cpf')  # CPF do cliente
    servidores = data.get('servidores')  # Lista de servidores envolvidos na compra
    
    # Validação do caminho (listagem de cidades)
    if not caminho or not isinstance(caminho, list) or len(caminho) < 2:
        return jsonify({"msg": "Caminho inválido"}), 400

    # Validação do CPF
    if not cpf:
        return jsonify({"msg": "CPF é obrigatório"}), 400

    if not cpf.isdigit() or len(cpf) != 11:
        return jsonify({"msg": "CPF inválido. Deve conter exatamente 11 dígitos."}), 400
    
    print(f"servidores1{servidores}")
    
    # Carrega os trechos de viagem do(s) servidor(es) especificado(s)
    if servidores:
        trechos_viagem = carregar_trechos(servidores)  # Passa a lista de servidores
    else:
        trechos_viagem = carregar_trechos()  # Carrega apenas trechos locais
    
    # Encontra o cliente no sistema
    cliente = encontrar_cliente(cpf)
    
    # Flags para indicar se os servidores estão envolvidos
    server1 = False
    server2 = False
    server3 = False
    
    # Verificar a disponibilidade de passagens
    trecho_copy = caminho.copy()  # Cria uma cópia do caminho para iteração
    sucesso = True  # Flag para indicar o sucesso da verificação dos trechos
    
    # Verificação dos trechos no caminho
    for i in range(len(trecho_copy)-1):
        origem = trecho_copy[i]  # Cidade de origem
        destino = trecho_copy[i+1]  # Cidade de destino
        
        if origem not in trechos_viagem or destino not in trechos_viagem[origem]:
            sucesso = False
            break
        if trechos_viagem[origem][destino]["vagas"] < 1:
            sucesso = False
            break
        
        # Verificar de que servidor vieram os trechos que fazem o caminho

    # Marcar os servidores envolvidos na transação
    for servidor in servidores:
        if(servidor == "server1"):
            server1 = True
            
        elif(servidor == "server2"):
            server2 = True

        elif(servidor == "server3"):
            server3 = True
    
    # Verificar o status dos servidores e realizar rollback se necessário
    if server1:
        response = requests.get(f"{SERVER_1_URL}/check_rollback")  # Checa se tem rollback
        status_code = response.status_code
        data = response.json()  # Obtém a resposta JSON
        if status_code == 200:
            print("Rollback encontrado, fazendo rollback antes da compra.")
            requests.post(f"{SERVER_1_URL}/rollback")  # Se houver, realiza rollback
            
        resposta1 = requests.post(f"{SERVER_1_URL}/cadastro", json={"cpf": cpf})
        if resposta1.status_code not in [200,409]:
            return jsonify({"msg": "Não foi possivel cadastrar o cliente em todos os servidores envolvidos na rota"}), 400

    if server2:
        response = requests.get(f"{SERVER_2_URL}/check_rollback")  # Checa se tem rollback
        status_code = response.status_code
        data = response.json()  # Obtém a resposta JSON
        if status_code == 200:
            print("Rollback encontrado, fazendo rollback antes da compra.")
            requests.post(f"{SERVER_2_URL}/rollback")  # Se houver, realiza rollback
            
        resposta2 = requests.post(f"{SERVER_2_URL}/cadastro", json={"cpf": cpf})
        if resposta2.status_code not in [200,409]:
            return jsonify({"msg": "Não foi possivel cadastrar o cliente em todos os servidores envolvidos na rota"}), 400
    
    if server3:
        response = requests.get(f"{SERVER_3_URL}/check_rollback")  # Checa se tem rollback
        status_code = response.status_code
        data = response.json()  # Obtém a resposta JSON
        if status_code == 200:
            print("Rollback encontrado, fazendo rollback antes da compra.")
            requests.post(f"{SERVER_3_URL}/rollback")  # Se houver, realiza rollback
            
        resposta3 = requests.post(f"{SERVER_3_URL}/cadastro", json={"cpf": cpf})
        if resposta3.status_code not in [200,409]:
            return jsonify({"msg": "Não foi possivel cadastrar o cliente em todos os servidores envolvidos na rota"}), 400

    # Se os trechos estiverem disponíveis, prepara para a transação
    if sucesso:
        try:
            prepare_responses = []  # Lista para armazenar as respostas de preparação

            # Envia a preparação para os servidores envolvidos
            if(server1):
                response = requests.post(f"{SERVER_1_URL}/prepare", json={"caminho": caminho, "servidores" : servidores})
            elif(server2):
                response = requests.post(f"{SERVER_2_URL}/prepare", json={"caminho": caminho, "servidores" : servidores})
                prepare_responses.append(response)
            elif(server3):
                response = requests.post(f"{SERVER_3_URL}/prepare", json={"caminho": caminho, "servidores" : servidores})
                prepare_responses.append(response)
            
            print(prepare_responses)
            
            # Verificar se todos os servidores responderam com sucesso
            if len(prepare_responses) == 0 or all(resp.status_code == 200 for resp in prepare_responses): 
                # Fase de commit

                params = {"caminho" : caminho}
                    
                rotas_server1 = [] 
                rotas_server2 = [] 
                rotas_server3 = [] 

                # Divide os trechos para cada servidor
                for i in range(len(servidores)):
                    lista_server1 = [] 
                    lista_server2 = [] 
                    lista_server3 = [] 

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

                # Envia o commit para os servidores envolvidos
                if server1:
                    requests.post(f"{SERVER_1_URL}/commit", json={"caminho": caminho, "rotas_server" : rotas_server1, "cpf": cpf})

                if server2:
                    requests.post(f"{SERVER_2_URL}/commit", json={"caminho": caminho, "rotas_server" : rotas_server2, "cpf": cpf})

                if server3:
                    requests.post(f"{SERVER_3_URL}/commit", json={"caminho": caminho, "rotas_server" : rotas_server3, "cpf": cpf})

                print(server1, server2, server3) 
                return jsonify({"msg": "Passagem comprada com sucesso"}), 200
                
            else:
                # Se alguma preparação falhar, faz rollback nos servidores
                if(server1):
                    requests.post(f"{SERVER_1_URL}/rollback")
                if(server2):
                    requests.post(f"{SERVER_2_URL}/rollback")
                if(server3):
                    requests.post(f"{SERVER_3_URL}/rollback")
                
                return jsonify({"msg": "Compra cancelada, não foi possível concluir a transação"}), 400

        except requests.RequestException:
            return jsonify({"msg": "Erro ao comunicar com os servidores externos."}), 500
    else:
        return jsonify({"msg": "Passagem não disponível"}), 400

# Endpoint para visualizar as passagens compradas de um cliente
@app.route('/passagens', methods=['GET'])
def ver_passagens():
    cpf = request.args.get('cpf')  # Obtém o CPF do cliente da query string
    if not cpf:
        return jsonify({"msg": "CPF é obrigatório"}), 400  # Verifica se o CPF foi informado

    # Verifica se o CPF possui 11 dígitos e é numérico
    if not cpf.isdigit() or len(cpf) != 11:
        return jsonify({"msg": "CPF inválido. Deve conter exatamente 11 dígitos."}), 400  # CPF inválido

    cliente = encontrar_cliente(cpf)  # Busca o cliente no sistema
    if not cliente:
        return jsonify({"msg": "Cliente não encontrado"}), 404  # Retorna erro se o cliente não for encontrado

    return jsonify(cliente.trechos), 200  # Retorna os trechos comprados pelo cliente

# Endpoint para buscar rotas entre cidades
@app.route('/buscar', methods=['GET'])
def buscar_rotas():
    origem = request.args.get('origem')  # Obtém a cidade de origem da query string
    destino = request.args.get('destino')  # Obtém a cidade de destino da query string

    if not origem or not destino:
        return jsonify({"msg": "Origem e destino são obrigatórios"}), 400  # Verifica se as duas cidades foram informadas
    
    trechos_viagem = {}  # Dicionário para armazenar os trechos de viagem
    servidores_externos = [SERVER_1_URL, SERVER_2_URL, SERVER_3_URL]  # URLs dos servidores externos

    # Coleta os trechos de viagem de todos os servidores
    trechos_viagem = coletar_trechos(trechos_viagem, servidores_externos)
    
    rotas = {}  # Dicionário para armazenar as rotas encontradas
    id_rota = 1  # ID inicial para a rota

    # Função DFS para buscar rotas recursivamente
    def dfs(cidade_atual, caminho, visitados, preco_total, servidores_incluidos):
        nonlocal id_rota
        caminho.append(cidade_atual)  # Adiciona a cidade atual ao caminho
        visitados.add(cidade_atual)  # Marca a cidade como visitada

        if cidade_atual == destino:
            # Se a cidade atual for o destino, registra a rota
            rotas[id_rota] = {
                "caminho": caminho[:],  # Caminho percorrido
                "preco_total": preco_total,  # Preço total da rota
                "servidores_incluidos": servidores_incluidos[:]  # Lista de servidores usados
            }
            id_rota += 1  # Incrementa o ID da rota
        else:
            # Percorre todos os vizinhos da cidade atual
            for vizinho, info in trechos_viagem.get(cidade_atual, {}).items():
                # Verifica se há vagas e se o vizinho ainda não foi visitado
                if info["vagas"] > 0 and vizinho not in visitados:
                    # Adiciona o server_id à lista de servidores incluídos
                    servidores_incluidos.append(info["server_id"])

                    # Soma o preço do trecho atual ao preço total e chama a recursão
                    dfs(vizinho, caminho[:], visitados, preco_total + info["preco"], servidores_incluidos)

                    # Remove o último server_id após a recursão
                    servidores_incluidos.pop()

        caminho.pop()  # Remove a cidade atual do caminho
        visitados.remove(cidade_atual)  # Marca a cidade como não visitada

    # Inicia a busca DFS a partir da origem
    dfs(origem, [], set(), 0, [])

    return jsonify(rotas), 200  # Retorna todas as rotas encontradas no formato JSON





def coletar_trechos(trechos_viagem, servidores_externos):
    """
    Coleta e mescla os trechos de todos os servidores, incluindo os locais e externos.
    """
    trechos_mesclados = trechos_viagem.copy()  # Começa com os trechos locais

    servidores_visitados = set()  # Conjunto para controlar quais servidores já foram visitados

    # Coleta trechos dos servidores externos
    for url in servidores_externos:
        if url not in servidores_visitados:  # Evita que o mesmo servidor seja visitado várias vezes
            try:
                servidores_visitados.add(url)  # Marca o servidor como visitado
                response = requests.get(f"{url}/carregar_trecho_local", timeout=10)  # Solicita os trechos do servidor externo
                if response.status_code == 200:  # Verifica se a resposta foi bem-sucedida
                    trechos_externos = response.json()  # Converte a resposta para JSON

                    # Mescla os trechos externos nos trechos locais
                    for cidade, info in trechos_externos.items():
                        if cidade not in trechos_mesclados:  # Se a cidade não estiver nos trechos locais, adiciona
                            trechos_mesclados[cidade] = info
                        else:
                            # Mescla as informações, adicionando novos dados caso já exista
                            trechos_mesclados[cidade].update(info)  # `info` é um dicionário com as informações do trecho
            except requests.RequestException:
                continue  # Se houver erro na requisição, ignora e passa para o próximo servidor
    print(f"trechos mesclados {trechos_mesclados}")  # Exibe os trechos mesclados no console
    for origem in trechos_mesclados:
        print(f"origem:{origem} | destino{trechos_mesclados[origem]}")  # Exibe cada origem e destino dos trechos
    return trechos_mesclados  # Retorna os trechos mesclados


# Fase de preparação (para outros servidores) - Solicitação POST para preparar a transação
@app.route('/prepare', methods=['POST'])
def prepare():
    data = request.get_json()  # Obtém os dados enviados no corpo da requisição
    caminho = data.get('caminho')  # Lista de cidades no caminho da viagem
    servidores_incluidos = data.get('servidores')  # Lista de servidores envolvidos no caminho

    # Itera sobre os trechos do caminho para verificar a disponibilidade de vagas
    for i in range(len(caminho) - 1):
        origem = caminho[i]  # Cidade de origem do trecho
        destino = caminho[i + 1]  # Cidade de destino do trecho
        
        # Identifica o servidor que gerencia o trecho (correspondente ao i-ésimo trecho)
        server_index = servidores_incluidos[i]
        if server_index == 'server1':
            server_url = SERVER_1_URL  # URL do servidor 1
        elif server_index == 'server2':
            server_url = SERVER_2_URL  # URL do servidor 2
        elif server_index == 'server3':
            server_url = SERVER_3_URL  # URL do servidor 3
        else:
            continue  # Pula se o servidor não for reconhecido

        # Mensagens a serem retornadas dependendo do sucesso ou falha na operação
        msg1 = (f"Pronto para o commit.")
        msg2 = (f"Prepare falhou, desistir do commit.")

        try:
            if(server_url is None):  # Verifica se a URL do servidor é inválida
                print("URL Invalido")
                return 400  # Retorna erro 400 se a URL for inválida

            # Solicita ao servidor para remover a vaga do trecho de viagem
            response = requests.post(f"{server_url}/remover_vaga", json={"origem": origem, "destino": destino})
            if response.status_code == 200:
                print(f"Vaga removida com sucesso.")  # Exibe mensagem de sucesso
            else:
                # Se não conseguir remover a vaga, exibe erro e retorna uma mensagem de falha
                print(f"Erro remover vaga do trecho: {response.json().get('msg', '')}")
                return jsonify({"msg": msg1}), 409  # Retorna conflito (409) em caso de erro

        except requests.exceptions.RequestException as e:
            print(f"Erro de conexão: {e}")  # Exibe erro de conexão se houver problemas na requisição
        except TimeoutError:
            return jsonify({"msg": msg1}), 409  # Retorna erro em caso de timeout

    return jsonify({"msg": msg2}), 200  # Retorna sucesso após a preparação dos trechos



# Fase de commit (para outros servidores)
@app.route('/commit', methods=['POST'])
def commit():
    data = request.get_json()  # Obtém os dados enviados no corpo da requisição
    rotas_server = data.get("rotas_server")  # Lista de rotas a serem comprometidas
    cpf = data.get("cpf")  # CPF do cliente
    clientecopy = encontrar_cliente(cpf)  # Encontra o cliente no sistema

    # Itera sobre as rotas fornecidas pelo servidor para adicioná-las ao cliente
    for i in rotas_server:
        novo_id = max(map(int, clientecopy.trechos.keys()), default=0) + 1  # Calcula o novo ID para o trecho
        clientecopy.trechos[str(novo_id)] = i  # Adiciona a rota ao cliente, usando o novo ID

    # Atualiza as informações do cliente no sistema
    atualizar_cliente(clientecopy)

    # Salva um arquivo JSON vazio para rollback (rollback inicial)
    salvar_json({}, CAMINHO_ROLLBACK)


# Fase de rollback (para outros servidores)
@app.route('/rollback', methods=['POST'])
def rollback():
    lock.acquire()  # Adquire o lock para garantir acesso exclusivo aos recursos compartilhados
    try:
        rollback_arquivo = carregar_json(CAMINHO_ROLLBACK)  # Carrega o arquivo de rollback
        trechos_viagem = carregar_trechos_locais  # Carrega os trechos locais

        # Itera sobre o arquivo de rollback para restaurar os trechos
        for origem, destinos in rollback_arquivo.items():
            for destino, detalhes in destinos.items():
                # Verifica se o trecho pertence ao servidor atual
                if detalhes['server_id'] == get_server():
                    # Restaura a quantidade de vagas para o valor do rollback
                    trechos_viagem[origem][destino]["vagas"] = rollback_arquivo[origem][destino]["vagas"]
                    # Remove o trecho do arquivo de rollback após a restauração
                    rollback_arquivo.pop(origem)

        # Salva os trechos restaurados
        salvar_trechos(trechos_viagem)
        # Salva o arquivo de rollback atualizado
        salvar_json(rollback_arquivo, CAMINHO_ROLLBACK)
    finally:
        lock.release()  # Libera o lock, permitindo que outros processos acessem os recursos compartilhados

    # Retorna uma resposta indicando que o rollback foi realizado com sucesso
    return jsonify({"msg": "Rollback realizado"}), 200


# Função para inicializar os arquivos
def inicializar_arquivos():
    if not CAMINHO_TRECHOS.exists():  # Verifica se o arquivo de trechos não existe
        salvar_trechos({  # Salva dados de trechos padrão
            "São Paulo-SP": {
                "Rio de Janeiro-RJ": {"vagas": 8, "preco": 100, "server_id": "server1"},
                "Brasília-DF": {"vagas": 5, "preco": 150, "server_id": "server1"}
            },
            "Rio de Janeiro-RJ": {
                "Brasília-DF": {"vagas": 2, "preco": 80, "server_id": "server1"},
                "Salvador-BA": {"vagas": 5, "preco": 120, "server_id": "server1"}
            },
            "Brasília-DF": {
                "Salvador-BA": {"vagas": 3, "preco": 90, "server_id": "server1"},
                "São Paulo-SP": {"vagas": 4, "preco": 160, "server_id": "server1"}
            },
            "Salvador-BA": {
                "Fortaleza-CE": {"vagas": 2, "preco": 110, "server_id": "server1"},
                "Rio de Janeiro-RJ": {"vagas": 6, "preco": 140, "server_id": "server1"}
            },
            "Fortaleza-CE": {
                "Recife-PE": {"vagas": 5, "preco": 70, "server_id": "server1"},
                "Salvador-BA": {"vagas": 3, "preco": 90, "server_id": "server1"}
            },
            "Recife-PE": {
                "Porto Alegre-RS": {"vagas": 1, "preco": 130, "server_id": "server1"},
                "Fortaleza-CE": {"vagas": 4, "preco": 80, "server_id": "server1"}
            },
            "Porto Alegre-RS": {
                "Curitiba-PR": {"vagas": 4, "preco": 95, "server_id": "server1"},
                "Recife-PE": {"vagas": 1, "preco": 150, "server_id": "server1"}
            },
            "Curitiba-PR": {
                "Manaus-AM": {"vagas": 0, "preco": 200, "server_id": "server1"},
                "Porto Alegre-RS": {"vagas": 3, "preco": 60, "server_id": "server1"}
            },
            "Manaus-AM": {
                "Belo Horizonte-MG": {"vagas": 3, "preco": 160, "server_id": "server1"},
                "Curitiba-PR": {"vagas": 2, "preco": 220, "server_id": "server1"}
            },
            "Belo Horizonte-MG": {
                "São Paulo-SP": {"vagas": 7, "preco": 85, "server_id": "server1"},
                "Manaus-AM": {"vagas": 4, "preco": 180, "server_id": "server1"}
            }
        })

    if not CAMINHO_CLIENTES.exists():  # Verifica se o arquivo de clientes não existe
        salvar_clientes([])  # Salva lista vazia de clientes

# Inicializa os arquivos ao iniciar o servidor
inicializar_arquivos()

if __name__ == '__main__':  # Inicia o servidor Flask
    app.run(debug=True, port=3000, host='0.0.0.0', threaded=True)
