# Desafio Netrin - Web Scraper com FastAPI e Docker

Este projeto é um **web scraper** para consultar dados de empresas no Sintegra, implementado em Python usando **FastAPI** para a API, com processamento assíncrono, **Redis** como broker e **RabbitMQ** como fila de tarefas. Todo o projeto é containerizado com **Docker** para facilitar execução e testes.

---

## Estrutura do Projeto

desafio_netrin/
├── docker-compose.yml
├── Dockerfile.api
├── Dockerfile.worker
├── requirements.txt
├── src/
│ ├── app/
│ │ ├── main.py # FastAPI application
│ │ └── models.py
│ ├── worker/
│ │ ├── worker.py # Worker
│ │ └── scraper.py # Funções de scraping
│ └── infrastructure/ # Client
└── tests/
├── test_api.py
└── test_scraper.py

## Requisitos

- Docker >= 20
- Docker Compose >= 2.3
- Python 3.11 (opcional se usar Docker)

---

## Setup e execução local

### 1. Clonar o repositório

```bash
git clone <url_do_repositorio>
cd desafio_netrin
### 2. Build e execução dos containers

```bash
sudo docker-compose up --build
```

Isso irá:

- Criar containers para API, Worker, Redis e RabbitMQ.
- Rodar a API na porta 8000.
- Inicializar o worker para processar as tarefas de scraping.
- Criar as dependências automaticamente.

### 3. Testando a API

A API possui dois endpoints principais:

#### POST /scrape

Enfileira uma tarefa de scraping. Exemplo usando `curl`:

```bash
curl -X POST http://localhost:8000/scrape \
-H "Content-Type: application/json" \
-d '{"cnpj": "12345678000195"}'
```

resposta esperada:
{
  "task_id": "uuid_da_tarefa",
  "status": "enqueued",
  "message": "Tarefa de scraping enfileirada com sucesso."
}

#### GET /status/{task_id}

Consulta o status de uma tarefa de scraping. Exemplo usando `curl`:

```bash
curl -X GET http://localhost:8000/status/{task_id}
```

Substitua `{task_id}` pelo ID da tarefa retornado pelo endpoint `/scrape`.

resposta esperada:
{
  "task_id": "uuid_da_tarefa",
  "status": "success",
  "result": { "cnpj": "12345678000195", "inscrição estadual": "Empresa XYZ", .... }
}

