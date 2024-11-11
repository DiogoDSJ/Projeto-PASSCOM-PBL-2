<h1>Sobre o projeto</h1>
<p>Este projeto foi desenvolvido como parte da disciplina MI — Concorrência e Conectividade do curso de Engenharia de Computação da Universidade Estadual de Feira de Santana (UEFS). Ele representa um sistema de compra de passagens aéreas, criado para explorar conceitos de concorrência e conectividade em rede de computadores.</p>
<div id = "introducao"> 
  <h2>Introdução</h2>
  <p>
    Este relatório apresenta o desenvolvimento de um sistema de compra de passagens, permitindo que clientes realizem consultas e reservas para rotas oferecidas por qualquer companhia em seu respectivo servidor. Para o compartilhamento de informações sobre os trechos, os servidores se comunicam entre si. Assim, foi implementado um sistema de comunicação baseado em TCP/IP, possibilitando que os clientes interajam com um dos servidores de maneira eficiente e direta. Neste projeto, os servidores foram desenvolvidos em Python, utilizando Flask para fornecer endpoints REST, enquanto o cliente usa a biblioteca requests para consumir esses serviços. Os dados são armazenados em arquivos JSON, assegurando a persistência das informações. O sistema conta também com mecanismos de controle de transações com o protocolo Two-Phase Commit (2PC) e locks para gerenciar a concorrência, garantindo a integridade dos dados durante operações simultâneas. Os resultados gerados demonstram que o sistema consegue gerenciar as reservas de passagens de forma eficiente e descentralizada, possibilitando que os clientes selecionem trechos de diversas companhias e realizem a compra de maneira simples e eficaz. 
  </p>
</div>

<h2>Equipe</h2>
<uL>
  <li><a href="https://github.com/DiogoDSJ">Diogo dos Santos de Jesus</a></li>
  <li><a href="https://github.com/eugabrielbr">Gabriel Silva dos Santos</a></li>
</ul>

<h2>Tutor</h2>
<uL>
  <li>Prof. Me. Antonio Augusto Teixeira Ribeiro Coutinho (UEFS)</li>
</ul>

<div id = "arquitetura">
<h2>Arquitetura da solução</h2>

  <p>A arquitetura foi desenvolvida com base no modelo de comunicação HTTP, utilizando a linguagem de programação Python, baseando-se no conjunto de restrições de arquitetura API REST. Para implementar essa comunicação, foi utilizada na aplicação do cliente a biblioteca requests, que é responsável por abstrair a complexidade da conexão de rede e permite que o cliente envie solicitações HTTP como GET e POST para o servidor. O servidor foi desenvolvido com base no microframework Flask, onde foram codificados endpoints responsáveis por receber as solicitações HTTP, realizar as operações necessárias e retornar as respostas para o cliente.</p>

  <p>Foi implementado uma aplicação cliente e três servidores, um para cada companhia. O que difere entre os servidores, de significativo, é apenas a URL de acesso a eles e o caminho dos arquivos dos seus determinados trechos. Segue o papel dos componentes desenvolvidos:</p>

  <p><strong>Cliente</strong>: Interage com o usuário, permitindo que ele execute ações como cadastro, compra de passagens e visualização de trechos. O código do cliente é responsável por coletar entradas do usuário, efetuar as solicitações HTTP e apresentar informações de forma organizada.</p>
  <p><strong>Servidor</strong>: Recebe e processa as requisições do cliente, gerenciando a lógica de negócios, armazenamento de dados e comunicação com o seu banco de dados. O servidor valida os dados recebidos e retorna as respostas apropriadas para as solicitações do cliente.</p>
  <p><strong>Arquivos de dados</strong>: Armazena os trechos da sua respectiva companhia em arquivos JSON. </p>
  <p><strong>API</strong>: implementada no servidor, é a interface que permite autenticações dos clientes, implementa os endpoints HTTP, efetua operações básicas de CRUD no arquivo JSON, regras de negócio, etc. </p>

</div> 

<div id = "protocolo">
  <h2>Protocolo de comunicação</h2>
<p>A API REST (Representational State Transfer) é um estilo arquitetural que define um conjunto de restrições e princípios para a criação de serviços web, permitindo a comunicação entre clientes e servidores de forma padronizada. Uma API REST utiliza os métodos HTTP (GET, POST, PUT, DELETE) para realizar operações em recursos identificados por URLs, onde cada recurso representa uma entidade do sistema, como usuários ou produtos. A comunicação é geralmente feita em formato JSON, o que facilita a integração com diferentes plataformas e linguagens de programação. REST promove a statelessness, ou seja, cada requisição do cliente deve conter todas as informações necessárias para que o servidor possa processá-la, permitindo escalabilidade e eficiência no gerenciamento de recursos.</p>

<p>
Foi desenvolvida uma API REST no servidor para que os clientes interajam com o sistema de passagens por meio de uma série de operações. Segue abaixo o detalhamento dos endpoints implementados: 
</p>
  
  <h3>Cadastro de Clientes (<code>cadastro()</code>)</h3>
    <ul>
        <li><strong>Endpoint:</strong> /cadastro</li>
        <li><strong>Método:</strong> POST</li>
        <li><strong>Parâmetros:</strong> HTTP - CPF do cliente</li>
        <li><strong>Retornos:</strong> JSON - status de cadastro. (400 - erro, 409 - cliente já existe, 201 - cadastro efetuado)</li>
        <li><strong>Descrição:</strong> Permite cadastrar um novo cliente fornecendo um CPF. Verifica se o CPF já existe antes de adicionar.</li>
    </ul>

  <h3>Listar Trechos Disponíveis (<code>listar_trechos()</code>)</h3>
    <ul>
        <li><strong>Endpoint:</strong> /trechos</li>
        <li><strong>Método:</strong> GET</li>
        <li><strong>Parâmetros:</strong> N/A</li>
        <li><strong>Retornos:</strong> JSON - trechos disponíveis na companhia</li>
        <li><strong>Descrição:</strong> Retorna todos os trechos de viagem disponíveis em formato JSON.</li>
    </ul>

  <h3>Comprar Passagem (<code>comprar_passagem()</code>)</h3>
    <ul>
        <li><strong>Endpoint:</strong> /comprar</li>
        <li><strong>Método:</strong> POST</li>
        <li><strong>Parâmetros:</strong> HTTP - Cidades de origem e destino e CPF do cliente</li>
        <li><strong>Retornos:</strong> JSON - status de compra ou erro de informações (400 - cpf inválido, caminho inválido e passagem não comprada, 404 - cliente não encontrado, 200 - passagem comprada)</li>
        <li><strong>Descrição:</strong> Permite que um cliente compre uma passagem, fornecendo o CPF e o caminho (lista de cidades).</li>
    </ul>

  <h3>Ver Passagens Compradas (<code>ver_passagens()</code>)</h3>
    <ul>
        <li><strong>Endpoint:</strong> /passagens</li>
        <li><strong>Método:</strong> GET</li>
        <li><strong>Parâmetros:</strong> HTTP - CPF do cliente</li>
        <li><strong>Retornos:</strong> JSON - status de consulta, trechos comprados e erros (400 - erro CPF inválido, 404 - cliente não encontrado, 200 - trechos comprados do cliente)</li>
        <li><strong>Descrição:</strong> Retorna as passagens compradas por um cliente específico, identificado pelo CPF.</li>
    </ul>

  <h3>Buscar Possibilidades de Rotas (<code>buscar_rotas()</code>)</h3>
    <ul>
        <li><strong>Endpoint:</strong> /buscar</li>
        <li><strong>Método:</strong> GET</li>
        <li><strong>Parâmetros:</strong> HTTP - Cidades de origem e destino</li>
        <li><strong>Retornos:</strong> JSON - status de busca e rotas solicitadas (400 - erro de parâmetro, 200 - possibilidade de rotas)</li>
        <li><strong>Descrição:</strong> Permite buscar rotas entre uma origem e um destino, retornando as rotas possíveis e seus custos.</li>
    </ul>
  
</div>

<h3>Buscar Possibilidades de Rotas (<code>buscar_rotas()</code>)</h3>
    <ul>
        <li><strong>Endpoint:</strong> /buscar</li>
        <li><strong>Método:</strong> GET</li>
        <li><strong>Parâmetros:</strong> HTTP - Cidades de origem e destino</li>
        <li><strong>Retornos:</strong> JSON - status de busca e rotas solicitadas (400 - erro de parâmetro, 200 - possibilidade de rotas)</li>
        <li><strong>Descrição:</strong> Permite buscar rotas entre uma origem e um destino, retornando as rotas possíveis e seus custos.</li>
    </ul>


<h3>Encontrar Cliente (<code>encontrar_cliente()</code>)</h3>
<ul>
    <li><strong>Endpoint:</strong> /encontrar_cliente</li>
    <li><strong>Método:</strong> POST</li>
    <li><strong>Parâmetros:</strong> HTTP - CPF do cliente</li>
    <li><strong>Retornos:</strong> JSON - dados do cliente se encontrado (200) ou mensagem de erro (400 se não encontrado)</li>
    <li><strong>Descrição:</strong> Permite buscar um cliente pelo CPF. Retorna os dados do cliente caso ele seja encontrado.</li>
</ul>

<h3>Atualizar Cliente (<code>atualizar_cliente()</code>)</h3>
<ul>
    <li><strong>Endpoint:</strong> /atualizar_cliente</li>
    <li><strong>Método:</strong> POST</li>
    <li><strong>Parâmetros:</strong> JSON - dados do cliente (incluindo CPF)</li>
    <li><strong>Retornos:</strong> JSON - mensagem de sucesso (200 para cliente atualizado/adicionado)</li>
    <li><strong>Descrição:</strong> Permite atualizar os dados de um cliente pelo CPF. Caso o cliente não exista, ele é adicionado ao sistema.</li>
</ul>

<h3>Remover Vaga (<code>remover_uma_vaga()</code>)</h3> <ul> <li><strong>Endpoint:</strong> /remover_vaga</li> <li><strong>Método:</strong> POST</li> <li><strong>Parâmetros:</strong> JSON - Cidades de origem e destino</li> <li><strong>Retornos:</strong> JSON - status da remoção (400 - erro, 200 - vaga removida com sucesso)</li> <li><strong>Descrição:</strong> Remove uma vaga disponível em um trecho específico entre duas cidades, ajustando a capacidade disponível do trecho.</li> </ul>

<h3>Carregar Trechos Locais (<code>carregar_trechos_locais()</code>)</h3> <ul> <li><strong>Endpoint:</strong> /carregar_trecho_local</li> <li><strong>Método:</strong> GET</li> <li><strong>Parâmetros:</strong> N/A</li> <li><strong>Retornos:</strong> JSON - lista de trechos locais disponíveis no servidor (200 - sucesso)</li> <li><strong>Descrição:</strong> Retorna os trechos de viagem locais disponíveis no servidor atual, incluindo as cidades de origem e destino e as vagas disponíveis.</li> </ul>

<h3>Inicializar Arquivo (<code>inicializar_arquivo()</code>)</h3> <ul> <li><strong>Endpoint:</strong> /inicializar_arquivo</li> <li><strong>Método:</strong> POST</li> <li><strong>Parâmetros:</strong> JSON - Dados iniciais para configurar o arquivo de trechos</li> <li><strong>Retornos:</strong> JSON - status da inicialização (200 - sucesso, 500 - erro interno)</li> <li><strong>Descrição:</strong> Inicializa o arquivo de trechos de viagem com os dados fornecidos, substituindo qualquer conteúdo existente.</li> </ul>

<h3>Verificar Disponibilidade (<code>verificar_disponibilidade()</code>)</h3> <ul> <li><strong>Endpoint:</strong> /verificar_disponibilidade</li> <li><strong>Método:</strong> GET</li> <li><strong>Parâmetros:</strong> HTTP - Cidades de origem e destino</li> <li><strong>Retornos:</strong> JSON - status da disponibilidade (200 - disponível, 404 - não disponível)</li> <li><strong>Descrição:</strong> Verifica se há vagas disponíveis para um trecho específico entre uma cidade de origem e destino.</li> </ul>

<h3>Preparar para Compra (<code>prepare()</code>)</h3> <ul> <li><strong>Endpoint:</strong> /prepare</li> <li><strong>Método:</strong> POST</li> <li><strong>Parâmetros:</strong> JSON - Cidades de origem e destino</li> <li><strong>Retornos:</strong> JSON - status de preparação (200 - sucesso, 409 - conflito)</li> <li><strong>Descrição:</strong> Verifica e bloqueia a concorrência para uma operação de compra em um trecho, garantindo que a operação esteja pronta para o próximo estágio sem conflitos.</li> </ul>

<h3>Confirmar Compra (<code>commit()</code>)</h3> <ul> <li><strong>Endpoint:</strong> /commit</li> <li><strong>Método:</strong> POST</li> <li><strong>Parâmetros:</strong> JSON - Cidades de origem e destino</li> <li><strong>Retornos:</strong> JSON - status da confirmação (200 - sucesso, 404 - erro)</li> <li><strong>Descrição:</strong> Confirma a compra de uma vaga em um trecho previamente bloqueado na fase de preparação.</li> </ul>

<h3>Abortar Compra (<code>abort()</code>)</h3> <ul> <li><strong>Endpoint:</strong> /abort</li> <li><strong>Método:</strong> POST</li> <li><strong>Parâmetros:</strong> JSON - Cidades de origem e destino</li> <li><strong>Retornos:</strong> JSON - status do aborto (200 - sucesso, 404 - erro)</li> <li><strong>Descrição:</strong> Aborta a operação de compra de vaga em um trecho, liberando qualquer bloqueio feito durante a fase de preparação.</li> </ul>


  
</div>

<div id = "roteamento">

  <h2>Roteamento</h2>
  
  <p>No sistema, para os servidores individuais, a busca em profundidade (DFS) é usada para explorar todas as rotas possíveis entre uma origem e um destino ao calcular passagens. Esse método funciona percorrendo recursivamente o grafo dos trechos, onde cada cidade representa um nó e cada trecho entre cidades representa uma aresta com uma quantidade limitada de vagas e um custo associado. A DFS inicia na cidade de origem e percorre os trechos disponíveis, acumulando o custo total do caminho e parando ao atingir a cidade de destino. A busca também verifica a disponibilidade de vagas em cada trecho para garantir que a rota seja válida para compra. </p>

<p>Quando um cliente decide comprar uma passagem de um trecho específico, o sistema é projetado para agregar todas as possibilidades de rotas disponíveis, considerando a origem e o destino informados. Inicialmente, a consulta pode ser realizada na companhia A, que verifica a disponibilidade do trecho desejado. Caso o trecho não esteja disponível somente na companhia A, o sistema amplia a busca, consultando as companhias B e C por meio de requisições HTTP a seus respectivos endpoints de listagem de trechos.</p>

<p>Essa integração entre as companhias é essencial para enriquecer o catálogo de trechos de viagem disponíveis para compra. Ao coletar informações de diferentes fontes, o servidor coordenador da compra monta as rotas novamente com a dfs no novo grafo, com os novos trechos adicionados e retorna para o cliente as possibilidades. Segue uma figura que exemplifica o funcionamento geral do sistema: </p>

<div align="center"> 
  <img src = "https://github.com/user-attachments/assets/58eb098d-e12b-44f3-9252-97ca20a77d0e" width="550px" />
</div>
<p align="center"><strong>Figura 1. Esquema de comunicação geral</strong></p>

</div>

<div id = "concorrencia">
  <h2>Concorrência distribuida</h2>
  <p>O sistema de compra de passagens foi projetado utilizando algumas funcionalidades do protocolo de confirmação em duas fases (Two-Phase Commit - 2PC) para gerenciar a concorrência em um ambiente distribuído. O 2PC é um protocolo que assegura a consistência de dados em transações que envolvem múltiplas fontes de dados. Ele garante que uma operação distribuída seja realizada de forma atômica: ou todos os participantes confirmam a execução da operação, ou ela é cancelada para todos, preservando a integridade dos dados. Este protocolo é essencial em sistemas distribuídos, pois ajuda a evitar inconsistências e conflitos que podem surgir devido a falhas de comunicação ou concorrência.</p>

  <p>O sistema consiste em um aplicativo cliente e três servidores (A, B e C), que compartilham informações sobre os trechos de viagem disponíveis. O servidor A atua como coordenador das transações, enquanto os servidores B e C são responsáveis por partes específicas dos dados (considerando que, se o cliente acessar o servidor B, ou C, ele se torna o servidor coordenador da operação). Quando um cliente solicita a compra de uma passagem, ele se conecta ao servidor A, que solicita todas as rotas possíveis entre o servidor B e C e apresenta todas as possibilidades possíveis..</p>

  <p>Para coordenar a execução das transações de compra, todo o processo é o complementado pelo uso de locks, que controlam o acesso aos arquivos de dados de cada servidor. Assim que uma transação é iniciada, cada servidor aplica um lock ao seu arquivo de trechos, impedindo que outras transações o modifiquem ou consultem simultaneamente. Somente após a conclusão da transação, o lock é liberado, permitindo que outros processos acessem o arquivo. Essa estratégia é crucial para evitar conflitos e inconsistências que poderiam surgir durante a reserva e a atualização dos dados.
</p>


<h4>Detalhamento do Caso de Uso:</h4>

<p><strong>1 - Fase de Preparação:</strong> Quando o coordenador inicia a transação, ele solicita que cada servidor trave o acesso ao arquivo de dados que contém os trechos de viagem. Esse lock impede que outros processos ou transações paralelas acessem ou modifiquem o arquivo até que a transação atual seja concluída. Cada servidor verifica sua capacidade de atender à solicitação e responde ao coordenador com "prepare" (se houver disponibilidade e o trecho puder ser reservado) ou "not-prepare" (se não houver disponibilidade). A manutenção do lock nesta fase é crucial para evitar que alterações no número de assentos ocorram simultaneamente, prevenindo conflitos entre transações.
</p>

<p><strong>2 - Fase de Commit (ou Abort):</strong> Se todos os servidores responderem "prepare", a transação avança para a fase de Commit, onde cada servidor atualiza seu arquivo para efetivar a reserva dos trechos. O lock permanece ativo durante esta fase para evitar qualquer interferência externa, garantindo que a atualização dos dados seja realizada sem interrupções. Se algum servidor retornar "not-prepare" na fase de preparação, a transação entra na fase de Abort, onde a compra é cancelada e o rollback é realizado. Após a conclusão da transação, seja por Commit ou Abort, o lock é liberado, permitindo o acesso de outros processos ou transações ao arquivo.
</p>

<div id = "confiabilidade">

<h2>Confiabilidade da solução</h2>

<p>Foi implementado no sistema um esquema que permite ao usuário continuar comprando mesmo que um ou mais servidores estejam indisponíveis. Assim, caso uma das companhias falhe, os trechos disponíveis em outras companhias continuam sendo oferecidos ao usuário. O sistema apresenta todas as rotas possíveis de acordo com as vagas disponíveis, garantindo que o usuário não visualize uma rota que dependa de um servidor fora do ar, pois, na prática, essa vaga é imediatamente considerada perdida.</p>

<p>Esse esquema funciona, em resumo, da seguinte maneira: ao acessar o sistema, o usuário tem sua conexão verificada com o servidor da companhia A, com tentativas de conexão realizadas três vezes antes de emitir um veredito. Caso o servidor não responda, o usuário é automaticamente redirecionado para outro servidor e pode optar por desconectar se não tiver interesse nessa companhia. Permanecendo conectado, ele pode realizar a compra normalmente, acessando os recursos dos servidores disponíveis no momento. A cada requisição, o sistema tenta reconectar ao servidor que estava offline; caso ele volte ao ar, as rotas que o incluem passam a ser apresentadas imediatamente, ampliando as possibilidades para o usuário.</p>

<p>Caso ocorra alguma falha critíca, um rollbak é realizado. O rollback no protocolo de commit em duas fases (2PC) é uma ação realizada quando ocorre uma falha em alguma das etapas do processo de commit distribuído. No 2PC, os participantes passam por duas fases: prepare (preparação) e commit (confirmação). Na fase de preparação, cada servidor verifica se consegue realizar a transação e responde ao coordenador com um "ok" ou "não". Se algum servidor responde negativamente ou ocorre uma falha durante o processo, o coordenador decide pelo rollback da transação.</p>

<p>O rollback, então, desfaz qualquer alteração provisória feita por cada servidor participante, retornando o sistema ao estado anterior ao início da transação, garantindo a consistência dos dados e evitando operações incompletas ou inconsistentes.</p>

  

</div>

<div id = "docker">

  <h2>Emprego do docker</h2>

  <p>A utilização do Docker no sistema é fundamental para garantir um ambiente de desenvolvimento e produção consistente e isolado. Com o Docker, é possível empacotar a aplicação e suas dependências em contêineres, o que simplifica o processo de implantação e garante que o sistema funcione de maneira idêntica em diferentes ambientes. Além disso, o Docker facilita a escalabilidade, permitindo que múltiplos contêineres sejam executados em paralelo para atender a um aumento na demanda, sem comprometer a performance. Essa abordagem também melhora a gestão de recursos, reduzindo conflitos entre serviços e proporcionando uma recuperação mais rápida em caso de falhas. Segue abaixo como executar o sistema:</p>

1. **Construir as imagens Docker:**
Navegue até a pasta onde o arquivo docker-compose.yml está e execute o seguinte comando
    ```bash
    docker compose build
    ```

3. **Construir contêiner do servidor e executa-lo:**
    ```bash
    docker compose up servidor(numero do servidor)
    ```

**Adicionar clientes:**

3. **Criar contêiner de um único cliente**
    ```bash
    docker compose up cliente
    ```

4. **Criar contêiners de vários clientes**
    ```bash
    docker compose up --scale cliente=(número de clientes que deseja)
    ```

</div> 

<div id = "conclusao">

  <h2>Conclusão</h2>  

  <p>
  Em conclusão, o sistema de compra de passagens desenvolvido neste projeto demonstra uma abordagem eficiente e robusta para gerenciar reservas de trechos de diferentes companhias aéreas, utilizando um aplicativo cliente e três servidores independentes que podem se interconectar. A implementação do protocolo Two-Phase Commit (2PC), juntamente com mecanismos de bloqueio (locks), assegura a integridade e a consistência dos dados durante operações simultâneas, prevenindo conflitos e garantindo que todas as transações sejam atômicas. A comunicação via HTTP permite uma interação fluida e escalável entre os clientes e servidores, facilitando a realização de consultas e reservas. O uso do Flask para o desenvolvimento dos endpoints REST proporciona uma interface intuitiva e de fácil acesso. Além disso, a adoção do Docker oferece um ambiente controlado e escalável, facilitando a implantação e gestão do sistema em diferentes contextos operacionais. No geral, as soluções implementadas garantem uma experiência segura e confiável para os usuários, permitindo-lhes realizar compras de passagens de maneira ágil e eficiente.</p>
</div>

<div id = "referencias">
 <h2>Referências</h2>

  <p>FOWLER, Martin. Patterns of Distributed Systems: Two-Phase Commit. Martinfowler.com, 23 novembro 2023. Disponível em: https://martinfowler.com/articles/patterns-of-distributed-systems/two-phase-commit.html. Acesso em: 6 nov. 2024.</p>
</div>

  
