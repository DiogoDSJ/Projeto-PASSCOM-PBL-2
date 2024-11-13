import requests
import os
import sys
import json

# Configurações do servidor


# conectar entre conteiners localmente
SERVER_HOST = '192.168.1.156'  # localhost ou servidor1
SERVER_PORT = 3000         # Porta configurada no servidor Flask
SERVER_1_URL = "http://192.168.1.156:3000" #para conectar conteiners de pcs diferentes, basta trocar "servidor1" e demais pelo ip da maquina do servidor
SERVER_2_URL = "http://192.168.1.156:4000"
SERVER_3_URL = "http://192.168.1.156:6000"

BASE_URL = f'http://{SERVER_HOST}:{SERVER_PORT}'



def limpar_tela():
    """Limpa a tela do terminal para uma visualização mais limpa."""
    os.system('cls' if os.name == 'nt' else 'clear')  # Limpa a tela com base no SO

def exibir_menu_principal():
    """Exibe o menu principal de forma formatada."""
    limpar_tela()  # Limpa a tela antes de mostrar o menu
    print("="*30)  # Exibe a borda superior
    print("       MENU PRINCIPAL")  # Título do menu
    print("="*30)  # Exibe a borda inferior
    print("1. Ver Trechos Disponíveis")  # Opção 1
    print("2. Ver Passagens Compradas")  # Opção 2
    print("3. Comprar Passagem")  # Opção 3
    print("4. Sair")  # Opção 4
    print("="*30)  # Exibe a borda final

def obter_cidades():
    """Imprime as cidades disponíveis para escolha."""
    cidades = set()  # Conjunto para garantir que não haja duplicatas

    servidores = [SERVER_1_URL, SERVER_2_URL, SERVER_3_URL]  # Lista de servidores
    for servidor in servidores:
        try:
            response = requests.get(f"{servidor}/obter_cidades")  # Requisição para obter cidades
            if response.status_code == 200:
                cidades.update(response.json())  # Atualiza o conjunto de cidades
                break  # Sai do loop após sucesso em um servidor
        except requests.RequestException as e:
            print(f"Erro ao conectar com o servidor {servidor}")  # Erro de conexão

    cidades = sorted(cidades)  # Ordena as cidades

    return cidades  # Retorna a lista de cidades ordenadas


def print_cidades(cidades):
    """Exibe as cidades disponíveis com índice para seleção."""
    for indice, cidade in enumerate(cidades, start=1):  # Itera sobre as cidades com índice iniciado em 1
        print(f"{indice}. {cidade}")  # Imprime a cidade com seu índice

def selecionar_cidade(indice, cidades):
    """Seleciona a cidade com base na opção escolhida."""
    if 1 <= indice <= len(cidades):  # Verifica se o índice está dentro do intervalo
        return cidades[indice - 1]  # Retorna a cidade correspondente (ajustando para índice 0)
    else:
        raise IndexError("Índice fora do intervalo da lista.")  # Levanta erro se índice for inválido

def ver_trechos(server_url):
    """Visualiza os trechos disponíveis em um servidor."""
    try:
        response = requests.get(f"{server_url}/trechos")  # Requisição para obter os trechos
        trechos = response.json()  # Converte a resposta em JSON
        if response.status_code == 200:  # Se a resposta for bem-sucedida
            for origem, destinos in trechos.items():  # Itera pelas origens dos trechos
                print(f"Origem: {origem}")  # Imprime origem
                for destino, info in destinos.items():  # Itera pelos destinos de cada origem
                    print(f"  Destino: {destino}")  # Imprime destino
                    print(f"    Vagas: {info['vagas']}")  # Imprime o número de vagas
                    print(f"    Preço: R${info['preco']}")  # Imprime o preço
                print("-"*30)  # Separador entre trechos
        else:
            print(f"Erro ao buscar trechos: {response.json().get('msg', '')}")  # Exibe mensagem de erro
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão: [SERVER1] {e}")  # Exibe erro de conexão


def ver_passagens_compradas():
    """Exibe as passagens compradas pelo cliente, fazendo requisições para os servidores."""
    limpar_tela()  # Limpa a tela
    print("="*30)  # Exibe cabeçalho
    print("   PASSAGENS COMPRADAS")  # Título da seção
    print("="*30)

    cpf = input("Insira seu CPF (11 dígitos): ").strip()  # Solicita CPF
    # Verifica se o CPF é válido
    if not cpf.isdigit() or len(cpf) != 11:
        print("CPF inválido. Deve conter exatamente 11 dígitos.")
        input("Pressione Enter para voltar ao menu principal...")
        return
    servidores_urls = [SERVER_1_URL, SERVER_2_URL, SERVER_3_URL]  # URLs dos servidores
    for i in range(3):
        try:
            # Faz uma requisição GET para verificar as passagens compradas
            response = requests.get(f"{servidores_urls[i]}/passagens", params={"cpf": cpf})
            if response.status_code == 200:
                passagens = response.json()  # Retorna o JSON com as passagens
                if not passagens:
                    print("Você não possui passagens compradas.")
                else:
                    print(f"Passagens servidor {i+1}:")
                    for id_passagem, caminho in passagens.items():
                        trajeto = " -> ".join(caminho)  # Exibe o trajeto das passagens
                        print(f"Trecho {id_passagem}: {trajeto}")
            else:
                print(f"Erro ao buscar passagens: {response.json().get('msg', '')}")
        except requests.exceptions.RequestException as e:
            print(f"Erro de conexão: {e}")

    input("Pressione Enter para voltar ao menu principal...")  # Aguarda input para voltar ao menu

def comprar_passagem():
    """Realiza a compra de uma passagem, incluindo verificação de rotas e servidores."""
    limpar_tela()  # Limpa a tela
    print("="*30)  # Exibe cabeçalho
    print("       COMPRAR PASSAGEM")  # Título da seção
    print("="*30)

    cpf = input("Insira seu CPF (11 dígitos): ").strip()  # Solicita CPF
    # Verifica se o CPF é válido
    if not cpf.isdigit() or len(cpf) != 11:
        print("CPF inválido. Deve conter exatamente 11 dígitos.")
        input("Pressione Enter para voltar ao menu principal...")
        return
    tentativas = 0  # Inicializa contador de tentativas
    servidores_urls = [SERVER_1_URL, SERVER_2_URL, SERVER_3_URL]  # URLs dos servidores

    try:
        while tentativas < len(servidores_urls):  # Tenta acessar os servidores para realizar cadastro
            try:
                situacao_cadastro = requests.post(f"{servidores_urls[tentativas]}/cadastro", json={"cpf": cpf})
                if situacao_cadastro.status_code == 200 or situacao_cadastro.status_code == 409:
                    ver = True  # Marca como válido se cadastro for bem-sucedido
                    print(f"{situacao_cadastro.json().get('msg', '')}")
                    break  # Sai do loop se cadastro for bem-sucedido
                else:
                    print(f"Erro no cadastro.")
                    print(f"{situacao_cadastro.json().get('msg', '')}")
                    print(f"Tentativa {tentativas} de {len(servidores_urls)}")
            except requests.exceptions.RequestException as e:
                print(f"Erro ao acessar o servidor {servidores_urls[tentativas]}")
            tentativas += 1    
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão: {e}")
    if(tentativas == 3):  # Caso todas as tentativas falhem
        print("Compra cancelada.")
        input("Pressione Enter para voltar ao menu principal...")
        return
    print("Escolha a origem:")
    cidades = obter_cidades()  # Obtém as cidades para o usuário escolher
    print_cidades(cidades)  # Exibe as cidades disponíveis
    try:
        opcao_origem = int(input("Escolha a opção de origem: ").strip())
        cidade_origem = selecionar_cidade(opcao_origem, cidades)  # Seleciona a cidade de origem
    except (ValueError, IndexError):
        print("Opção de origem inválida.")
        input("Pressione Enter para voltar ao menu principal...")
        return

    limpar_tela()
    print("="*30)
    print("       COMPRAR PASSAGEM")
    print("="*30)
    print("Escolha o destino:")
    print_cidades(cidades)  # Exibe as cidades novamente para escolher o destino
    try:
        opcao_destino = int(input("Escolha a opção de destino: ").strip())
        cidade_destino = selecionar_cidade(opcao_destino, cidades)  # Seleciona a cidade de destino
    except (ValueError, IndexError):
        print("Opção de destino inválida.")
        input("Pressione Enter para voltar ao menu principal...")
        return

    # Busca de rotas disponíveis
    params = {
        "origem": cidade_origem,
        "destino": cidade_destino
    }
    tentativas = 0
    servidores_urls = [SERVER_1_URL, SERVER_2_URL, SERVER_3_URL]
    rotas = None
    try:
        while tentativas < len(servidores_urls):  # Tenta acessar os servidores para buscar rotas
            try:
                response = requests.get(f"{servidores_urls[tentativas]}/buscar", params=params, timeout=10)
                if response.status_code == 200:
                    rotas = response.json()  # Retorna as rotas disponíveis
                    if len(rotas) > 0:
                        print(f"Rotas encontradas no servidor {servidores_urls[tentativas]}")
                        break  # Sai do loop se rotas forem encontradas
                else:
                    print(f"Erro ao buscar rotas no servidor {servidores_urls[tentativas]}: {response.json().get('msg', '')}")
            except requests.exceptions.RequestException as e:
                print(f"Erro ao acessar o servidor {servidores_urls[tentativas]}: {e}")
            except requests.exceptions.ConnectionError as e:
                print(f"Erro ao acessar o servidor {servidores_urls[tentativas]}: {e}")
            tentativas += 1
            print(f"Tentativa {tentativas} de {len(servidores_urls)}")

        if rotas is None:  # Caso não haja rotas disponíveis
            print("Não há rotas disponíveis para essa viagem.")
            input("Pressione Enter para voltar ao menu principal...")
            return
        
        print("\nRotas disponíveis:")
        for id_rota, detalhes in rotas.items():
            trajeto = " -> ".join(detalhes['caminho'])  # Exibe as rotas disponíveis
            preco_total = detalhes['preco_total']
            print(f"{id_rota}. {trajeto} | Preço Total: R${preco_total}")
        print(rotas)
        # Escolha da rota
        escolha_rota = input("\nEscolha a rota desejada (número) ou digite 'cancelar' para abortar: ").strip()
        if escolha_rota.lower() == 'cancelar':
            print("Compra cancelada.")
            input("Pressione Enter para voltar ao menu principal...")
            return

        if not escolha_rota.isdigit() or escolha_rota not in rotas:
            print("Opção inválida.")
            input("Pressione Enter para voltar ao menu principal...")
            return

        rota_escolhida = rotas[escolha_rota]['caminho']  # Seleciona a rota escolhida
        servidores = rotas[escolha_rota]["servidores_incluidos"]  # Obtém os servidores que participam da rota
        # Inicia o processo de compra com o protocolo 2PC
        payload = {
            "caminho": rota_escolhida,
            "cpf": cpf,  # Adiciona o CPF na payload
            "servidores" : servidores
        }
        tentativas = 0
        try:
            while tentativas < len(servidores_urls):  # Tenta realizar a compra nos servidores
                try:
                    compra_response = requests.post(f"{servidores_urls[tentativas]}/comprar", json=payload)
                    if compra_response.status_code == 200:
                        print("Compra realizada com sucesso!")
                        break  # Sai do loop se compra for realizada
                    else:
                        print(f"Erro ao realizar compra pelo servidor {tentativas+1}, {compra_response.json().get('msg', '')}.")
                        print(f"Tentativa {tentativas} de {len(servidores_urls)}")
                except requests.exceptions.RequestException as e:
                    print(f"Erro ao acessar o servidor {servidores_urls[tentativas]}")
                tentativas += 1    
        except requests.exceptions.RequestException as e:
            print(f"Erro de conexão: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão: {e}")
    input("Pressione Enter para voltar ao menu principal...")  # Aguarda

def main():
    """Função principal do cliente, onde o menu é exibido e as opções são tratadas."""
    while True:
        exibir_menu_principal()  # Exibe o menu principal
        opcao = input("Escolha uma opção: ").strip()  # Solicita a opção ao usuário
        if opcao == "1":  # Se a opção for 1, exibe os trechos de cada servidor
            print("SERVER 1\n")
            ver_trechos(SERVER_1_URL)
            print("SERVER 2\n")
            ver_trechos(SERVER_2_URL)
            print("SERVER 3\n")
            ver_trechos(SERVER_3_URL)
            input("Pressione Enter para voltar ao menu principal...")  # Aguarda input para voltar
        elif opcao == "2":  # Se a opção for 2, exibe as passagens compradas
            ver_passagens_compradas()
        elif opcao == "3":  # Se a opção for 3, permite a compra de passagem
            comprar_passagem()
        elif opcao == "4":  # Se a opção for 4, sai do sistema
            print("Saindo do sistema...")
            sys.exit(0)
        else:  # Caso a opção seja inválida
            print("Opção inválida. Tente novamente.")

if __name__ == "__main__":
    main()  # Inicia a função principal

