Desafio Netrin — Scraper Sintegra (FastAPI + RabbitMQ + Redis + Worker Playwright)

Scraper assíncrono para consultar dados de empresas no Sintegra/GO.
A API enfileira tarefas no RabbitMQ, o worker (Playwright/Chromium, headless) processa e o Redis armazena status/resultado.

Stack

API: FastAPI (Python 3.11)

Fila: RabbitMQ (com painel :15672)

Cache/Status: Redis

Worker: Playwright (Chromium headless)

Container: Docker + Docker Compose

Requisitos

Git

Docker 20+

Docker Compose v2+

Como rodar (5 passos)
1) Clonar o repositório
git clone https://github.com/Thomas-Delgado/desafio-netrin.git
cd desafio-netrin

2) Subir com Docker
docker compose up -d --build

3) Verificar serviços
docker compose ps


Você deve ver api, worker, redis, rabbitmq como Up.

4) Acessos úteis

RabbitMQ UI: http://localhost:15672
 (user: guest, pass: guest)

Fluxo (resumo)
POST /scrape  →  publica job na fila  →  worker consome  →  faz scraping  →  salva status/resultado no Redis
GET  /results/{task_id}  →  retorna status e dados (se prontos)

Endpoints (com exemplos curl)
1) Criar tarefa de scraping
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{"cnpj":"00006486000175"}'


Resposta (exemplo)

{
  "task_id": "8fcb0c4b-1b60-4d38-86bb-938b11e64a33",
  "status": "enqueued",
  "message": "Tarefa de scraping enfileirada com sucesso."
}

2) Consultar status/resultado
curl -X GET http://localhost:8000/results/8fcb0c4b-1b60-4d38-86bb-938b11e64a33


Possíveis respostas

Em processamento

{ "task_id":"...", "status":"processing", "data":{}, "error":null }


Concluída

{
  "task_id":"...",
  "status":"completed",
  "data":{
    "cnpj":"00006486000175",
    "razao_social":"EMPRESA XYZ LTDA",
    "inscricao_estadual":"123456789",
    "situacao_cadastral":"HABILITADO",
    "uf":"GO"
  },
  "error":null
}


Erro

{ "task_id":"...", "status":"error", "data":{}, "error":"Mensagem de erro" }

Logs rápidos (útil pro avaliador)

Todos os serviços

docker compose logs -f


Só o worker (ver consumo da fila e scraping)

docker compose logs -f worker


RabbitMQ (ver se está aceitando conexões)

docker compose logs -f rabbitmq


No painel do RabbitMQ (Queues → scraping_queue) verifique Consumers = 1 (worker conectado) e a queda do campo Ready quando o worker consome.

Estrutura do projeto
src/
├─ app/
│  ├─ __init__.py
│  ├─ main.py                # FastAPI: /scrape e /results/{task_id}
│  └─ models.py              # Pydantic models e exceptions
├─ infrastructure/
│  └─ clients_manager.py     # RedisClient e RabbitMQClient (publish/consume)
└─ worker/
   ├─ __init__.py
   ├─ worker.py              # loop do consumidor (RabbitMQ → processa → Redis)
   └─ scraper.py             # Playwright: consulta.asp → consultar.asp → parse

Como o Worker funciona (resumo técnico)

Conecta no RabbitMQ e consome a fila scraping_queue.

Para cada mensagem {task_id, cnpj}:

marca processing no Redis;

abre o Playwright/Chromium (headless), acessa Consulta/consulta.asp, preenche o CNPJ, clica em Consultar, espera consultar.asp;

extrai os campos com BeautifulSoup;

marca completed (ou error) no Redis com os dados.

Adicione seu usuário ao grupo docker:

sudo usermod -aG docker $USER && newgrp docker

Worker não conecta ao RabbitMQ (ConnectionRefused/Consumers=0)

Veja se o RabbitMQ está “Up”:

docker compose ps
docker compose logs -f rabbitmq


Reinicie o worker (às vezes o RabbitMQ leva alguns segundos a mais):

docker compose restart worker

Erro ao puxar imagem Playwright (tag não encontrada)

Use mcr.microsoft.com/playwright/python:v1.47.2-jammy ou mcr.microsoft.com/playwright/python:jammy.

“no such element” no scraping

O site pode estar lento/diferente. O worker usa esperas explícitas (Playwright wait_for_*).
Reenvie a tarefa; se persistir, verifique seletor/URL (Consulta/consulta.asp → consultar.asp).

Desenvolvimento (hot-reload simples)

Os serviços montam ./src:/src como volume — alterou o código, o container enxerga na hora.
Se mudar dependências (requirements.txt) ou Dockerfiles, rebuild:

docker compose up -d --build
