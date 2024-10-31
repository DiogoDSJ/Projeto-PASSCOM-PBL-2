<h1>Sobre o projeto</h1>
<p>Este projeto foi desenvolvido como parte da disciplina MI — Concorrência e Conectividade do curso de Engenharia de Computação da Universidade Estadual de Feira de Santana (UEFS). Ele representa um sistema de compra de passagens aéreas, criado para explorar conceitos de concorrência e conectividade em rede de computadores.</p>
<div id = "introducao"> 
  <h2>Introdução</h2>
  <p>
    Este relatório apresenta o desenvolvimento de um sistema de compra de passagens, permitindo que clientes realizem consultas e reservas para rotas oferecidas por qualquer companhia em seu respectivo servidor. Para o compartilhamento de informações sobre os trechos, os servidores se comunicam entre si. Assim, foi implementado um sistema de comunicação baseado em TCP/IP, possibilitando que os clientes interajam com um dos servidores de maneira eficiente e direta. Neste projeto, os servidores foram desenvolvidos em Python, utilizando Flask para fornecer endpoints REST, enquanto o cliente usa a biblioteca requests para consumir esses serviços. Os dados são armazenados em arquivos JSON, assegurando a persistência das informações. [FALAR SOBRE CONCORRÊNCIA]
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
