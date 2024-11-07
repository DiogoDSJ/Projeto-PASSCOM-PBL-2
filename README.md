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
Foi desenvolvida uma API REST no servidor para que os clientes interajam com o sistema de passagens por meio de uma série de operações. Segue abaixo o detalhamento dos métodos implementados: 
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

<div id = "roteamento">

  <h2>Roteamento</h2>
  
  <p>No sistema, para os servidores individuais, a busca em profundidade (DFS) é usada para explorar todas as rotas possíveis entre uma origem e um destino ao calcular passagens. Esse método funciona percorrendo recursivamente o grafo dos trechos, onde cada cidade representa um nó e cada trecho entre cidades representa uma aresta com uma quantidade limitada de vagas e um custo associado. A DFS inicia na cidade de origem e percorre os trechos disponíveis, acumulando o custo total do caminho e parando ao atingir a cidade de destino. A busca também verifica a disponibilidade de vagas em cada trecho para garantir que a rota seja válida para compra. </p>

<p>Quando um cliente decide comprar uma passagem de um trecho específico, o sistema é projetado para agregar todas as possibilidades de rotas disponíveis, considerando a origem e o destino informados. Inicialmente, a consulta pode ser realizada na companhia A, que verifica a disponibilidade do trecho desejado. Caso o trecho não esteja disponível somente na companhia A, o sistema amplia a busca, consultando as companhias B e C por meio de requisições HTTP a seus respectivos endpoints de listagem de trechos.</p>

<p>Essa integração entre as companhias é essencial para enriquecer o catálogo de trechos de viagem disponíveis para compra. Ao coletar informações de diferentes fontes, o servidor coordenador da compra monta as rotas novamente com a dfs no novo grafo, com os novos trechos adicionados e retorna para o cliente as possibilidades. </p>

</div>

<div id = "concorrencia">
  <h2>Concorrência distribuida</h2>
  <p>O sistema de compra de passagens foi projetado utilizando o protocolo de confirmação em duas fases (Two-Phase Commit - 2PC) para gerenciar a concorrência em um ambiente distribuído. O 2PC é um protocolo que assegura a consistência de dados em transações que envolvem múltiplas fontes de dados. Ele garante que uma operação distribuída seja realizada de forma atômica: ou todos os participantes confirmam a execução da operação, ou ela é cancelada para todos, preservando a integridade dos dados. Este protocolo é essencial em sistemas distribuídos, pois ajuda a evitar inconsistências e conflitos que podem surgir devido a falhas de comunicação ou concorrência.</p>

  <p>O sistema consiste em um aplicativo cliente e três servidores (A, B e C), que compartilham informações sobre os trechos de viagem disponíveis. O servidor A atua como coordenador das transações, enquanto os servidores B e C são responsáveis por partes específicas dos dados (considerando que, se o cliente acessar o servidor B, ou C, ele se torna o servidor coordenador da operação). Quando um cliente solicita a compra de uma passagem, ele se conecta ao servidor A, que primeiro verifica a disponibilidade de trechos localmente. Se o trecho solicitado não estiver disponível, o servidor A consulta os servidores B e C. Essa abordagem permite uma gestão eficaz das requisições de compra e assegura a consistência entre os servidores.</p>

  <p>Para coordenar a execução das transações de compra, o protocolo 2PC é complementado pelo uso de locks, que controlam o acesso aos arquivos de dados de cada servidor. Assim que uma transação é iniciada, cada servidor aplica um lock ao seu arquivo de trechos, impedindo que outras transações o modifiquem ou consultem simultaneamente. Essa trava permanece ativa durante as fases de Preparação e Commit do 2PC. Somente após a conclusão da transação, seja pelo commit ou pelo abort, o lock é liberado, permitindo que outros processos acessem o arquivo. Essa estratégia é crucial para evitar conflitos e inconsistências que poderiam surgir durante a reserva e a atualização dos dados.
</p>

<p>Caso o servidor A não consiga atender à solicitação diretamente, ele inicia uma transação distribuída, consultando os servidores B e C. A compra é efetivada apenas se todos os servidores confirmarem que não estão com acesso restrito aos arquivos e as vagas estão disponíveis. O uso de locks em conjunto com o protocolo 2PC proporciona segurança contra inconsistências e assegura que as operações sejam realizadas de forma atômica, mesmo em cenários com múltiplas consultas simultâneas.
</p>

<h4>Detalhamento do Caso de Uso:</h4>

<p><strong>1 - Fase de Preparação:</strong> Quando o coordenador inicia a transação, ele solicita que cada servidor trave o acesso ao arquivo de dados que contém os trechos de viagem. Esse lock impede que outros processos ou transações paralelas acessem ou modifiquem o arquivo até que a transação atual seja concluída. Cada servidor verifica sua capacidade de atender à solicitação e responde ao coordenador com "prepare" (se houver disponibilidade e o trecho puder ser reservado) ou "not-prepare" (se não houver disponibilidade). A manutenção do lock nesta fase é crucial para evitar que alterações no número de assentos ocorram simultaneamente, prevenindo conflitos entre transações.
</p>

<p><strong>2 - Fase de Commit (ou Abort):</strong> Se todos os servidores responderem "prepare", a transação avança para a fase de Commit, onde cada servidor atualiza seu arquivo para efetivar a reserva dos trechos. O lock permanece ativo durante esta fase para evitar qualquer interferência externa, garantindo que a atualização dos dados seja realizada sem interrupções. Se algum servidor retornar "not-prepare" na fase de preparação, a transação entra na fase de Abort, onde a compra é cancelada. Após a conclusão da transação, seja por Commit ou Abort, o lock é liberado, permitindo o acesso de outros processos ou transações ao arquivo.
</p>

<div id = "confiabilidade">


  

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

  
