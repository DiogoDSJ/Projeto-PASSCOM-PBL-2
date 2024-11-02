import requests
import os
import sys
import json

# Configurações do servidor
SERVER_HOST = 'localhost'  # Altere para o IP do servidor se necessário
SERVER_PORT = 3000         # Porta configurada no servidor Flask
BASE_URL = f'http://{SERVER_HOST}:{SERVER_PORT}'
SERVER_1_URL = "http://localhost:3000"
SERVER_2_URL = "http://localhost:4000"
SERVER_3_URL = "http://localhost:5000"

def limpar_tela():
    """Limpa a tela do terminal para uma visualização mais limpa."""
    os.system('cls' if os.name == 'nt' else 'clear')

def exibir_menu_principal():
    """Exibe o menu principal de forma formatada."""
    limpar_tela()
    print("="*30)
    print("       MENU PRINCIPAL")
    print("="*30)
    print("1. Ver Trechos Disponíveis")
    print("2. Ver Passagens Compradas")
    print("3. Comprar Passagem")
    print("4. Sair")
    print("="*30)

def print_cidades():
    """Imprime as cidades disponíveis para escolha."""
    cidades = set()  # Usamos um set para garantir que as cidades não se repitam

    # Lista de URLs dos servidores
    servidores = [SERVER_1_URL, SERVER_2_URL, SERVER_3_URL]

    for servidor in servidores:
        try:
            response = requests.get(f"{servidor}/obter_cidades")
            if response.status_code == 200:
                # Adiciona cada cidade à lista de cidades únicas
                cidades.update(response.json())
        except requests.RequestException as e:
            print(f"Erro ao conectar com o servidor {servidor}: {e}")

    # Converte para lista e ordena as cidades antes de imprimir
    cidades = sorted(cidades)
    
    # Imprime cada cidade
    for indice, cidade in enumerate(cidades, start=1):
        print(f"{indice}. {cidade}")
        
    return cidades

def selecionar_cidade(indice, cidades):
    """Seleciona a cidade com base na opção escolhida."""
    if 1 <= indice <= len(cidades):
        return cidades[indice - 1]  # Ajusta o índice para o padrão 0-baseado
    else:
        raise IndexError("Índice fora do intervalo da lista.")

def ver_trechos(server_url):
    """Visualiza os trechos disponíveis."""
    try:
        response = requests.get(f"{server_url}/trechos")
        if response.status_code == 200:
            trechos = response.json()
            for origem, destinos in trechos.items():
                print(f"Origem: {origem}")
                for destino, info in destinos.items():
                    print(f"  Destino: {destino}")
                    print(f"    Vagas: {info['vagas']}")
                    print(f"    Preço: R${info['preco']}")
                print("-"*30)
        else:
            print(f"Erro ao buscar trechos: {response.json().get('msg', '')}")
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão: {e}")

def ver_passagens_compradas():
    """Visualiza as passagens compradas pelo cliente."""
    limpar_tela()
    print("="*30)
    print("   PASSAGENS COMPRADAS")
    print("="*30)

    cpf = input("Insira seu CPF (11 dígitos): ").strip()
    if not cpf.isdigit() or len(cpf) != 11:
        print("CPF inválido. Deve conter exatamente 11 dígitos.")
        input("Pressione Enter para voltar ao menu principal...")
        return

    try:
        response = requests.get(f"{BASE_URL}/passagens", params={"cpf": cpf})
        if response.status_code == 200:
            passagens = response.json()
            if not passagens:
                print("Você não possui passagens compradas.")
            else:
                for id_passagem, caminho in passagens.items():
                    trajeto = " -> ".join(caminho)
                    print(f"Passagem {id_passagem}: {trajeto}")
        else:
            print(f"Erro ao buscar passagens: {response.json().get('msg', '')}")
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão: {e}")

    input("Pressione Enter para voltar ao menu principal...")

def comprar_passagem():
    """Realiza a compra de uma passagem."""
    limpar_tela()
    print("="*30)
    print("       COMPRAR PASSAGEM")
    print("="*30)

    cpf = input("Insira seu CPF (11 dígitos): ").strip()
    if not cpf.isdigit() or len(cpf) != 11:
        print("CPF inválido. Deve conter exatamente 11 dígitos.")
        input("Pressione Enter para voltar ao menu principal...")
        return

    print("Escolha a origem:")
    cidades = print_cidades()
    try:
        opcao_origem = int(input("Escolha a opção de origem (1-10): ").strip())
        cidade_origem = selecionar_cidade(opcao_origem, cidades)
        if not cidade_origem:
            raise ValueError("Opção de origem inválida.")
    except ValueError:
        print("Opção de origem inválida.")
        input("Pressione Enter para voltar ao menu principal...")
        return

    limpar_tela()
    print("="*30)
    print("       COMPRAR PASSAGEM")
    print("="*30)
    print("Escolha o destino:")
    print_cidades()
    try:
        opcao_destino = int(input("Escolha a opção de destino (1-10): ").strip())
        cidade_destino = selecionar_cidade(opcao_destino, cidades)
        if not cidade_destino:
            raise ValueError("Opção de destino inválida.")
    except ValueError:
        print("Opção de destino inválida.")
        input("Pressione Enter para voltar ao menu principal...")
        return

    # Busca de rotas disponíveis
    params = {
        "origem": cidade_origem,
        "destino": cidade_destino
    }

    try:
        response = requests.get(f"{BASE_URL}/buscar", params=params)
        if response.status_code == 200:
            rotas = response.json()
            if not rotas:
                print("Não há rotas disponíveis para essa viagem.")
                input("Pressione Enter para voltar ao menu principal...")
                return

            print("\nRotas disponíveis:")
            for id_rota, detalhes in rotas.items():
                trajeto = " -> ".join(detalhes['caminho'])
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

            rota_escolhida = rotas[escolha_rota]['caminho']

            # Envio da requisição de compra
            payload = {
                "caminho": rota_escolhida,
                "cpf": cpf  # Adiciona o CPF na payload
            }

            compra_response = requests.post(f"{BASE_URL}/comprar", json=payload)
            if compra_response.status_code == 200:
                print("Compra realizada com sucesso!")
            else:
                print(f"Erro na compra: {compra_response.json().get('msg', '')}")

        else:
            print(f"Erro ao buscar rotas: {response.json().get('msg', '')}")

    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão: {e}")

    input("Pressione Enter para voltar ao menu principal...")

def menu_principal():
    """Função principal que exibe o menu e processa a escolha do usuário."""
    while True:
        exibir_menu_principal()
        escolha = input("Escolha uma opção (1/2/3/4): ").strip()
        if escolha == '1':
            print("="*30)
            print("     TRECHOS DISPONÍVEIS")
            print("="*30)
            ver_trechos(SERVER_1_URL)
            ver_trechos(SERVER_2_URL)
            ver_trechos(SERVER_3_URL)
            input("Pressione Enter para voltar ao menu principal...")
        elif escolha == '2':
            ver_passagens_compradas()
        elif escolha == '3':
            comprar_passagem()
        elif escolha == '4':
            print("="*30)
            print("   Saindo do programa...")
            print("="*30)
            sys.exit()
        else:
            limpar_tela()
            print("="*30)
            print("Opção inválida, tente novamente.")
            print("="*30)
            input("Pressione Enter para continuar...")
def main():
    """Inicialização do cliente."""
    menu_principal()

if __name__ == "__main__":
    main()
