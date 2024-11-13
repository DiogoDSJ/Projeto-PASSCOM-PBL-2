from flask import Flask, request, jsonify
import json
from pathlib import Path
import threading
import requests
import time

app = Flask(__name__)

# Caminhos dos arquivos JSON
CAMINHO_TRECHOS = Path(__file__).parent / "trechos_viagem_s3.json"
CAMINHO_CLIENTES = Path(__file__).parent / "clientes_servidor3.json"
CAMINHO_ROLLBACK = Path(__file__).parent / 'rollback_data.json'




SERVER_1_URL = "http://192.168.1.156:3000" #para conectar conteiners de pcs diferentes, basta trocar "servidor1" e demais pelo ip da maquina do servidor
SERVER_2_URL = "http://192.168.1.156:4000"
SERVER_3_URL = "http://192.168.1.156:6000"



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
            return jsonify({"status": "success", "message": "O arquivo JSON está vazio.", "has_keys": False}), 400
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

# Função para carregar dados JSON de um arquivo
def carregar_json(caminho_arquivo):
    try:
        if not caminho_arquivo.exists():  # Verifica se o arquivo existe
            return {}  # Retorna dicionário vazio caso não exista
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:  # Abre o arquivo para leitura
            return json.load(f)  # Carrega e retorna os dados JSON
    except json.JSONDecodeError:
        print(f"Erro: O arquivo {caminho_arquivo} contém JSON inválido.")  # Erro de formato JSON inválido
        return {}  # Retorna dicionário vazio
    except Exception as e:
        print(f"Erro ao carregar JSON de {caminho_arquivo}: {e}")  # Erro genérico ao carregar o arquivo
        return {}  # Retorna dicionário vazio

# Função para salvar clientes
def salvar_clientes(clientes):
    dados = [cliente.to_dict() for cliente in clientes]  # Converte lista de clientes para dicionários
    salvar_json(dados, CAMINHO_CLIENTES)  # Salva os dados no arquivo de clientes

# Função para carregar os clientes
def carregar_clientes():
    dados = carregar_json(CAMINHO_CLIENTES)  # Carrega os dados dos clientes
    if not isinstance(dados, list):  # Verifica se os dados são uma lista
        print(f"Erro: O arquivo {CAMINHO_CLIENTES} não contém uma lista válida de clientes.")  # Erro de formato
        return []  # Retorna lista vazia
    return [Cliente.from_dict(cliente) for cliente in dados]  # Converte os dados para objetos Cliente

# Função para encontrar um cliente pelo CPF
def encontrar_cliente(cpf):
    clientes = carregar_clientes()  # Carrega a lista de clientes
    for cliente in clientes:  # Itera sobre os clientes
        if cliente.cpf == cpf:  # Verifica se o CPF corresponde
            return cliente  # Retorna o cliente encontrado
    return None  # Retorna None caso o cliente não seja encontrado

# Endpoint para encontrar um cliente via requisição POST
@app.route('/encontrar_cliente', methods=['POST'])
def encontrar_cliente_endpoint():
    clientes = carregar_clientes()  # Carrega a lista de clientes
    cpf = request.args.get('cpf')  # Obtém o CPF da requisição
    for cliente in clientes:  # Itera sobre os clientes
        if cliente.cpf == cpf:  # Verifica se o CPF corresponde
            return jsonify(cliente.to_dict())  # Retorna os dados do cliente encontrado
    return jsonify({"msg": "Cliente nao encontrado"}), 400  # Retorna mensagem de erro caso não encontrado


# Função para adicionar um novo cliente
def adicionar_cliente(cliente):
    clientes = carregar_clientes()  # Carrega a lista de clientes
    clientes.append(cliente)  # Adiciona o novo cliente
    salvar_clientes(clientes)  # Salva a lista atualizada de clientes

# Função para atualizar os dados de um cliente existente ou adicionar um novo cliente
def atualizar_cliente(cliente_atualizado):
    clientes = carregar_clientes()  # Carrega a lista de clientes
    for idx, cliente in enumerate(clientes):  # Itera sobre os clientes
        if cliente.cpf == cliente_atualizado.cpf:  # Verifica se o CPF corresponde
            clientes[idx] = cliente_atualizado  # Atualiza os dados do cliente
            salvar_clientes(clientes)  # Salva a lista de clientes atualizada
            return  # Finaliza a função após atualizar
    adicionar_cliente(cliente_atualizado)  # Se não encontrado, adiciona como novo cliente



# Endpoint para atualizar ou adicionar um cliente
@app.route('/atualizar_cliente', methods=['POST'])
def atualizar_cliente_endpoint():
    clientes = carregar_clientes()  # Carrega a lista de clientes
    data = request.json  # Obtém os dados enviados na requisição
    cliente_atualizado = Cliente(**data)  # Cria um objeto Cliente com os dados recebidos
    for idx, cliente in enumerate(clientes):  # Itera sobre os clientes
        if cliente.cpf == cliente_atualizado.cpf:  # Verifica se o CPF corresponde
            clientes[idx] = cliente_atualizado  # Atualiza os dados do cliente
            salvar_clientes(clientes)  # Salva a lista de clientes atualizada
            return jsonify({"msg": "Cliente atualizado"}), 200  # Retorna resposta de sucesso
    # Se não encontrar, adiciona como novo cliente
    adicionar_cliente(cliente_atualizado)  
    return jsonify({"msg": "Cliente adicionado"}), 200  # Retorna resposta de sucesso

# Endpoint para remover uma vaga de um trecho de viagem
@app.route('/remover_vaga', methods=['POST'])
def remover_uma_vaga():
    data = request.get_json()  # Obtém os dados enviados na requisição
    origem = data.get("origem")  # Recupera a origem do trecho
    destino = data.get("destino")  # Recupera o destino do trecho
    trechos_viagem = carregar_trechos()  # Carrega os trechos de viagem
    trechos_rollback = carregar_json(CAMINHO_ROLLBACK)  # Carrega os dados de rollback
    if origem in trechos_viagem and destino in trechos_viagem[origem] and trechos_viagem[origem][destino]["vagas"] > 0:
        trechos_rollback[origem] = trechos_viagem[origem]  # Armazena o estado atual para rollback
        salvar_json(trechos_rollback, CAMINHO_ROLLBACK)  # Salva os dados de rollback
        trechos_viagem[origem][destino]["vagas"] -= 1  # Diminui o número de vagas
        salvar_trechos(trechos_viagem)  # Salva os trechos de viagem atualizados
        return jsonify({"msg": "Vaga removida com sucesso"}), 200  # Retorna resposta de sucesso
    else:
        return jsonify({"msg": "Erro na remocao da vaga"}), 400  # Retorna erro se não houver vaga

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


# Função para salvar os trechos de viagem no arquivo
def salvar_trechos(trechos):
    dados = {"trechos": trechos}  # Organiza os dados em um dicionário
    salvar_json(dados, CAMINHO_TRECHOS)  # Chama a função para salvar os dados no arquivo

# Endpoint para obter todas as cidades disponíveis
@app.route('/obter_cidades', methods=['GET'])
def obter_cidades_endpoint():
    try:
        # Carrega os trechos de cada servidor
        dados_servidor1 = carregar_trechos("server1")
        dados_servidor2 = carregar_trechos("server2")
        dados_servidor3 = carregar_trechos("server3")

        # Combina os dados de todos os servidores
        todas_cidades = set()  # Cria um conjunto para armazenar as cidades sem repetições
        
        for dados in [dados_servidor1, dados_servidor2, dados_servidor3]:
            todas_cidades.update(dados.keys())  # Adiciona as cidades de origem
            for destinos in dados.values():
                todas_cidades.update(destinos.keys())  # Adiciona as cidades de destino

        return jsonify(sorted(todas_cidades)), 200  # Retorna a lista ordenada de cidades

    except Exception as e:
        return jsonify({"msg": "Erro ao obter cidades", "erro": str(e)}), 500  # Retorna erro se ocorrer exceção


# Endpoint para cadastro de clientes
@app.route('/cadastro', methods=['POST'])
def cadastro():
    data = request.get_json()  # Obtém os dados da requisição
    cpf = data.get('cpf')  # Recupera o CPF do cliente

    if not cpf:  # Verifica se o CPF foi fornecido
        return jsonify({"msg": "CPF é obrigatório"}), 400  # Retorna erro se o CPF não for fornecido

    if not cpf.isdigit() or len(cpf) != 11:  # Valida se o CPF é composto apenas por números e tem 11 dígitos
        return jsonify({"msg": "CPF inválido. Deve conter exatamente 11 dígitos."}), 400

    with lock:  # Bloqueia o acesso para garantir que o cadastro seja feito sem concorrência
        if encontrar_cliente(cpf):  # Verifica se o cliente já existe
            return jsonify({"msg": "Cliente já existe [servidor3]"}), 409  # Retorna erro se o cliente já estiver cadastrado

        cliente = Cliente(cpf=cpf)  # Cria um novo cliente
        adicionar_cliente(cliente)  # Adiciona o cliente à lista de clientes

    return jsonify({"msg": "Cadastro realizado com sucesso [servidor3]"}), 200  # Retorna sucesso

# Endpoint para listar os trechos disponíveis
@app.route('/trechos', methods=['GET'])
def listar_trechos():
    trechos = carregar_trechos()  # Carrega os trechos de viagem
    return jsonify(trechos), 200  # Retorna os trechos em formato JSON

# Endpoint para preparar a compra da passagem
@app.route('/comprar', methods=['POST'])
def preparar_compra():
    data = request.get_json()  # Obtém os dados da requisição (json)
    caminho = data.get('caminho')  # Lista de cidades, ex: ["CidadeA", "CidadeB", "CidadeC"]
    cpf = data.get('cpf')  # CPF do cliente
    servidores = data.get('servidores')  # Lista de servidores a serem usados na compra

    # Valida se o caminho é uma lista válida e tem pelo menos 2 cidades
    if not caminho or not isinstance(caminho, list) or len(caminho) < 2:
        return jsonify({"msg": "Caminho inválido"}), 400

    # Valida o CPF
    if not cpf:
        return jsonify({"msg": "CPF é obrigatório"}), 400

    if not cpf.isdigit() or len(cpf) != 11:
        return jsonify({"msg": "CPF inválido. Deve conter exatamente 11 dígitos."}), 400

    print(f"servidores1{servidores}")

    # Carrega os trechos de viagem dos servidores se fornecido
    if servidores:
        trechos_viagem = carregar_trechos(servidores)  # Passa a lista de servidores
    else:
        trechos_viagem = carregar_trechos()  # Carrega apenas trechos locais

    # Encontra o cliente pelo CPF
    cliente = encontrar_cliente(cpf)

    # Flags para indicar quais servidores estão envolvidos
    server1 = False
    server2 = False
    server3 = False

    # Verifica a disponibilidade de passagens nos trechos fornecidos
    trecho_copy = caminho.copy()
    sucesso = True
    for i in range(len(trecho_copy)-1):
        origem = trecho_copy[i]
        destino = trecho_copy[i+1]
        
        # Verifica se o trecho está disponível
        if origem not in trechos_viagem or destino not in trechos_viagem[origem]:
            sucesso = False
            break
        if trechos_viagem[origem][destino]["vagas"] < 1:
            sucesso = False
            break

    # Verifica quais servidores foram incluídos na requisição
    for servidor in servidores:
        if(servidor == "server1"):
            server1 = True
        elif(servidor == "server2"):
            server2 = True
        elif(servidor == "server3"):
            server3 = True
    
    # Verifica se o servidor 1 está envolvido e realiza rollback se necessário
    if server1:
        response = requests.get(f"{SERVER_1_URL}/check_rollback")  # Checa se há rollback no servidor 1
        status_code = response.status_code
        data = response.json()  # Obtém a resposta JSON
        if status_code == 200:
            print("Rollback encontrado, fazendo rollback antes da compra.")
            requests.post(f"{SERVER_1_URL}/rollback")  # Se houver rollback, faz o rollback
            
        resposta1 = requests.post(f"{SERVER_1_URL}/cadastro", json={"cpf": cpf})  # Tenta cadastrar o cliente
        if resposta1.status_code not in [200, 409]:  # Se não for sucesso ou conflito, retorna erro
            return jsonify({"msg": "Não foi possível cadastrar o cliente em todos os servidores envolvidos na rota"}), 400

    # Verifica se o servidor 2 está envolvido e realiza rollback se necessário
    if server2:
        response = requests.get(f"{SERVER_2_URL}/check_rollback")  # Checa se há rollback no servidor 2
        status_code = response.status_code
        data = response.json()  # Obtém a resposta JSON
        if status_code == 200:
            print("Rollback encontrado, fazendo rollback antes da compra.")
            requests.post(f"{SERVER_2_URL}/rollback")  # Se houver rollback, faz o rollback
            
        resposta2 = requests.post(f"{SERVER_2_URL}/cadastro", json={"cpf": cpf})  # Tenta cadastrar o cliente
        if resposta2.status_code not in [200, 409]:  # Se não for sucesso ou conflito, retorna erro
            return jsonify({"msg": "Não foi possível cadastrar o cliente em todos os servidores envolvidos na rota"}), 400
    
    # Verifica se o servidor 3 está envolvido e realiza rollback se necessário
    if server3:
        response = requests.get(f"{SERVER_3_URL}/check_rollback")  # Checa se há rollback no servidor 3
        status_code = response.status_code
        data = response.json()  # Obtém a resposta JSON
        if status_code == 200:
            print("Rollback encontrado, fazendo rollback antes da compra.")
            requests.post(f"{SERVER_3_URL}/rollback")  # Se houver rollback, faz o rollback
            
        resposta3 = requests.post(f"{SERVER_3_URL}/cadastro", json={"cpf": cpf})  # Tenta cadastrar o cliente
        if resposta3.status_code not in [200, 409]:  # Se não for sucesso ou conflito, retorna erro
            return jsonify({"msg": "Não foi possível cadastrar o cliente em todos os servidores envolvidos na rota"}), 400

    # Verifica se os trechos são válidos antes de prosseguir
    if sucesso:
        # Fase de preparação: notificar outros servidores
        try:
            prepare_responses = []
            
            # Envia preparação para o servidor 1, caso esteja envolvido
            if(server1): 
                response = requests.post(f"{SERVER_1_URL}/prepare", json={"caminho": caminho, "servidores": servidores})
            # Envia preparação para o servidor 2, caso esteja envolvido
            elif(server2): 
                response = requests.post(f"{SERVER_2_URL}/prepare", json={"caminho": caminho, "servidores": servidores})
                prepare_responses.append(response)
            # Envia preparação para o servidor 3, caso esteja envolvido
            elif(server3): 
                response = requests.post(f"{SERVER_3_URL}/prepare", json={"caminho": caminho, "servidores": servidores})
                prepare_responses.append(response)

            # Verifica se todos os servidores responderam com sucesso
            if len(prepare_responses) == 0 or all(resp.status_code == 200 for resp in prepare_responses): 
                # Fase de commit
                params = {"caminho" : caminho}
                rotas_server1 = [] 
                rotas_server2 = [] 
                rotas_server3 = [] 

                # Organiza as rotas por servidor
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

                # Envia o commit para cada servidor envolvido
                if server1:
                    requests.post(f"{SERVER_1_URL}/commit", json={"caminho": caminho, "rotas_server": rotas_server1, "cpf": cpf})

                if server2:
                    requests.post(f"{SERVER_2_URL}/commit", json={"caminho": caminho, "rotas_server": rotas_server2, "cpf": cpf})

                if server3:
                    requests.post(f"{SERVER_3_URL}/commit", json={"caminho": caminho, "rotas_server": rotas_server3, "cpf": cpf})

                print(server1, server2, server3) 
                return jsonify({"msg": "Passagem comprada com sucesso"}), 200

            else:
                # Caso algum servidor tenha falhado, faz rollback nos servidores envolvidos
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
# Endpoint para visualizar passagens do cliente
@app.route('/passagens', methods=['GET'])
def ver_passagens():
    cpf = request.args.get('cpf')  # Obtém o CPF da requisição
    if not cpf:
        return jsonify({"msg": "CPF é obrigatório"}), 400  # Retorna erro caso o CPF não seja fornecido

    # Valida o CPF
    if not cpf.isdigit() or len(cpf) != 11:
        return jsonify({"msg": "CPF inválido. Deve conter exatamente 11 dígitos."}), 400

    cliente = encontrar_cliente(cpf)  # Encontra o cliente baseado no CPF
    if not cliente:
        return jsonify({"msg": "Cliente não encontrado."}), 404  # Retorna erro caso o cliente não seja encontrado

    return jsonify(cliente.trechos), 200  # Retorna os trechos de viagem do cliente com sucesso


# Endpoint para buscar rotas entre duas cidades
@app.route('/buscar', methods=['GET'])
def buscar_rotas():
    origem = request.args.get('origem')  # Obtém a cidade de origem da requisição
    destino = request.args.get('destino')  # Obtém a cidade de destino da requisição

    # Verifica se origem e destino foram fornecidos
    if not origem or not destino:
        return jsonify({"msg": "Origem e destino são obrigatórios"}), 400

    trechos_viagem = {}  # Dicionário para armazenar os trechos de viagem
    servidores_externos = [SERVER_1_URL, SERVER_2_URL, SERVER_3_URL]  # URLs dos servidores externos

    # Coleta os trechos de viagem dos servidores externos
    trechos_viagem = coletar_trechos(trechos_viagem, servidores_externos)
    
    rotas = {}  # Dicionário para armazenar as rotas encontradas
    id_rota = 1  # ID para identificar cada rota

    # Função recursiva DFS (busca em profundidade) para encontrar todas as rotas possíveis
    def dfs(cidade_atual, caminho, visitados, preco_total, servidores_incluidos):
        nonlocal id_rota  # Usa o id_rota global da função principal
        caminho.append(cidade_atual)  # Adiciona a cidade atual ao caminho
        visitados.add(cidade_atual)  # Marca a cidade atual como visitada

        # Se a cidade atual for o destino, registra a rota encontrada
        if cidade_atual == destino:
            rotas[id_rota] = {
                "caminho": caminho[:],  # Copia o caminho para não ser alterado
                "preco_total": preco_total,  # Armazena o preço total da viagem
                "servidores_incluidos": servidores_incluidos[:]  # Armazena os servidores usados
            }
            id_rota += 1  # Incrementa o ID da rota
        else:
            # Percorre os vizinhos da cidade atual
            for vizinho, info in trechos_viagem.get(cidade_atual, {}).items():
                # Verifica se há vagas no trecho e se a cidade vizinha não foi visitada
                if info["vagas"] > 0 and vizinho not in visitados:
                    # Adiciona o servidor atual à lista de servidores incluídos
                    servidores_incluidos.append(info["server_id"])

                    # Soma o preço da viagem ao preço total e chama recursivamente a DFS
                    dfs(vizinho, caminho[:], visitados, preco_total + info["preco"], servidores_incluidos)

                    # Remove o servidor da lista ao voltar da recursão
                    servidores_incluidos.pop()

        caminho.pop()  # Remove a cidade atual do caminho ao voltar da recursão
        visitados.remove(cidade_atual)  # Marca a cidade atual como não visitada

    # Inicia a busca DFS a partir da origem
    dfs(origem, [], set(), 0, [])

    return jsonify(rotas), 200  # Retorna as rotas encontradas com sucesso




# Função que coleta e mescla os trechos de todos os servidores, locais e externos
def coletar_trechos(trechos_viagem, servidores_externos):
    """
    Coleta e mescla os trechos de todos os servidores, incluindo os locais e externos.
    """
    trechos_mesclados = trechos_viagem.copy()  # Começa com os trechos locais

    servidores_visitados = set()  # Conjunto para evitar visitas repetidas aos servidores externos

    # Coleta trechos dos servidores externos
    for url in servidores_externos:
        if url not in servidores_visitados:  # Verifica se o servidor já foi visitado
            try:
                servidores_visitados.add(url)  # Marca o servidor como visitado
                response = requests.get(f"{url}/carregar_trecho_local", timeout=10)  # Faz a requisição ao servidor externo
                if response.status_code == 200:
                    trechos_externos = response.json()  # Converte a resposta em JSON

                    # Mescla os trechos externos nos trechos locais
                    for cidade, info in trechos_externos.items():
                        if cidade not in trechos_mesclados:  # Se a cidade não estiver nos trechos locais
                            trechos_mesclados[cidade] = info
                        else:
                            # Mescla as informações (adiciona se não existir)
                            trechos_mesclados[cidade].update(info)  # Supondo que `info` seja um dicionário
            except requests.RequestException:
                continue  # Se houver erro na requisição, ignora e passa para o próximo servidor
    print(f"trechos mesclados {trechos_mesclados}")  # Exibe os trechos mesclados no terminal
    for origem in trechos_mesclados:
        print(f"origem:{origem} | destino{trechos_mesclados[origem]}")  # Exibe cada origem e seus destinos
    return trechos_mesclados  # Retorna os trechos mesclados


# Fase de preparação (para outros servidores) no protocolo de commit em duas fases
@app.route('/prepare', methods=['POST'])
def prepare():
    data = request.get_json()  # Obtém os dados da requisição JSON
    caminho = data.get('caminho')  # Lista de cidades no caminho
    servidores_incluidos = data.get('servidores')  # Lista de servidores envolvidos no caminho

    # Itera sobre os trechos do caminho para realizar a preparação nos servidores
    for i in range(len(caminho) - 1):
        origem = caminho[i]  # Cidade de origem
        destino = caminho[i + 1]  # Cidade de destino
        
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

        msg1 = (f"Pronto para o commit.")  # Mensagem de sucesso na preparação
        msg2 = (f"Prepare falhou, desistir do commit.")  # Mensagem de falha na preparação
        
        try:
            if(server_url is None):  # Verifica se a URL do servidor é inválida
                print("URL Invalida")
                return 400  # Retorna erro 400 se a URL for inválida
            response = requests.post(f"{server_url}/remover_vaga", json={"origem": origem, "destino": destino}, timeout=10)  # Envia requisição POST para remover a vaga
            if response.status_code == 200:
                print(f"Vaga removida com sucesso.")  # Exibe sucesso no terminal
            else:
                print(f"Erro remover vaga do trecho: {response.json().get('msg', '')}")  # Exibe erro caso não consiga remover a vaga
                return jsonify({"msg": msg1}), 409  # Retorna erro 409 caso falhe na remoção
        except requests.exceptions.RequestException as e:
            print(f"Erro de conexão: {e}")  # Exibe erro de conexão
        except TimeoutError:
            return jsonify({"msg": msg1}), 409  # Retorna erro 409 em caso de timeout
    return jsonify({"msg": msg2}), 200  # Retorna mensagem de sucesso se tudo estiver correto

        
# Fase de commit (para outros servidores) no protocolo de commit em duas fases
@app.route('/commit', methods=['POST'])
def commit():
    data = request.get_json()  # Obtém os dados da requisição JSON
    rotas_server = data.get("rotas_server")  # Lista de rotas que foram aceitas pelos servidores
    cpf = data.get("cpf")  # CPF do cliente que está realizando a operação

    clientecopy = encontrar_cliente(cpf)  # Encontra o cliente com o CPF fornecido
    for i in rotas_server:
        novo_id = max(map(int, clientecopy.trechos.keys()), default=0) + 1  # Gera um novo ID para o trecho
        clientecopy.trechos[str(novo_id)] = i  # Adiciona o trecho à lista de trechos do cliente
    
    atualizar_cliente(clientecopy)  # Atualiza as informações do cliente no sistema
    salvar_json({}, CAMINHO_ROLLBACK)  # Limpa o arquivo de rollback, indicando que a transação foi confirmada


# Fase de rollback (para outros servidores) no protocolo de commit em duas fases
@app.route('/rollback', methods=['POST'])
def rollback():
    lock.acquire()  # Bloqueia o código para evitar concorrência durante o rollback
    try:
        rollback_arquivo = carregar_json(CAMINHO_ROLLBACK)  # Carrega o arquivo de rollback
        trechos_viagem = carregar_trechos_locais  # Carrega os trechos locais (de viagem)

        # Itera pelos trechos que precisam ser revertidos, conforme os dados no arquivo de rollback
        for origem, destinos in rollback_arquivo.items():
            for destino, detalhes in destinos.items():
                if detalhes['server_id'] == get_server():  # Verifica se o trecho é do servidor atual
                    trechos_viagem[origem][destino]["vagas"] = rollback_arquivo[origem][destino]["vagas"]  # Restaura a vaga do trecho
                    rollback_arquivo.pop(origem)  # Remove a origem do arquivo de rollback após reverter

        salvar_trechos(trechos_viagem)  # Salva os trechos locais atualizados
        salvar_json(rollback_arquivo, CAMINHO_ROLLBACK)  # Salva o arquivo de rollback atualizado
    finally:
        lock.release()  # Libera o bloqueio, permitindo que outras operações ocorram

    return jsonify({"msg": "Rollback realizado"}), 200  # Retorna a resposta de sucesso do rollback


# Função para inicializar os arquivos de trechos e clientes, caso não existam
def inicializar_arquivos():
    # Verifica se o arquivo de trechos não existe
    if not CAMINHO_TRECHOS.exists():
        # Salva um conjunto inicial de trechos de viagem no arquivo
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

    # Verifica se o arquivo de clientes não existe
    if not CAMINHO_CLIENTES.exists():
        # Cria e salva uma lista vazia de clientes
        salvar_clientes([])

# Inicializa os arquivos ao iniciar o servidor
inicializar_arquivos()

# Verifica se o script está sendo executado diretamente e inicia o servidor Flask
if __name__ == '__main__':
    # Inicializa os arquivos de trechos e clientes, se necessário
    inicializar_arquivos()
    
    # Inicia o servidor Flask na porta 6000, com modo de depuração e disponível para todas as interfaces (0.0.0.0)
    app.run(port=6000, debug=True, host='0.0.0.0', threaded=True)
