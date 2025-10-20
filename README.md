🚀 Desafio Netrin — Scraper Sintegra
Sistema assíncrono para consulta de dados de empresas no Sintegra/GO

Um scraper robusto que utiliza FastAPI + RabbitMQ + Redis + Worker Playwright para processar consultas de forma assíncrona e eficiente.

🏗️ Arquitetura
text
📦 Sistema Assíncrono
├── 🚀 API (FastAPI)
├── 📨 Fila (RabbitMQ)
├── 💾 Cache (Redis)
└── 🛠️ Worker (Playwright)

🛠️ Stack Tecnológica

API	FastAPI (Python 3.11)
Fila	RabbitMQ (com painel :15672)
Cache/Status	Redis
Worker	Playwright (Chromium headless)
Container	Docker + Docker Compose
⚡ Como Rodar (5 passos rápidos)
1. 📥 Clonar o repositório
bash
git clone https://github.com/Thomas-Delgado/desafio-netrin.git
cd desafio-netrin
2. 🐳 Subir com Docker
bash
docker compose up -d --build
3. ✅ Verificar serviços
bash
docker compose ps
Você deve ver: api, worker, redis, rabbitmq como Up ✅

4. 🌐 Acessos úteis
RabbitMQ UI: http://localhost:15672

👤 User: guest

🔑 Pass: guest

5. 🧪 Testar a aplicação
bash
# Exemplo de consulta
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{"cnpj":"00006486000175"}'
🔄 Fluxo do Sistema





POST /scrape → publica job na fila

Worker consome da fila → faz scraping

Redis armazena status/resultado

GET /results/{task_id} → retorna status e dados

📡 Endpoints
🎯 Criar tarefa de scraping
bash
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{"cnpj":"00006486000175"}'
📤 Resposta (exemplo):

json
{
  "task_id": "8fcb0c4b-1b60-4d38-86bb-938b11e64a33",
  "status": "enqueued",
  "message": "Tarefa de scraping enfileirada com sucesso."
}
🔍 Consultar status/resultado
bash
curl -X GET http://localhost:8000/results/8fcb0b4b-1b60-4d38-86bb-938b11e64a33
📥 Possíveis respostas:

🔄 Em processamento:

json
{
  "task_id": "...",
  "status": "processing",
  "data": {},
  "error": null
}
✅ Concluída:

json
{
  "task_id": "...",
  "status": "completed",
  "data": {
    "cnpj": "00006486000175",
    "razao_social": "EMPRESA XYZ LTDA",
    "inscricao_estadual": "123456789",
    "situacao_cadastral": "HABILITADO",
    "uf": "GO"
  },
  "error": null
}
❌ Erro:

json
{
  "task_id": "...",
  "status": "error",
  "data": {},
  "error": "Mensagem de erro"
}
📊 Monitoramento
👀 Ver todos os serviços com logs
bash
docker compose logs -f
🛠️ Só o worker (ver consumo da fila e scraping)
bash
docker compose logs -f worker
🐇 RabbitMQ (ver conexões)
bash
docker compose logs -f rabbitmq
📈 Painel RabbitMQ
Acesse: http://localhost:15672

Vá em Queues → scraping_queue

Verifique Consumers = 1 (worker conectado)

Observe a queda do campo Ready quando o worker consome

🔄 Processo Técnico
📥 Consumo: Conecta no RabbitMQ e consome a fila scraping_queue

🔄 Processamento: Para cada mensagem {task_id, cnpj}:

Marca processing no Redis

Abre Playwright/Chromium (headless)

Acessa Consulta/consulta.asp

Preenche o CNPJ, clica em "Consultar", espera consultar.asp

Extrai os campos com BeautifulSoup

💾 Armazenamento: Marca completed (ou error) no Redis com os dados

⚠️ Considerações Importantes
🌐 Site pode estar lento/diferente

⏳ Worker usa esperas explícitas (Playwright wait_for_*)

🔄 Reenvie a tarefa se necessário

🔍 Verifique seletores/URLs se persistirem erros

🚀 Desenvolvimento (Hot-Reload)
🔥 Desenvolvimento com Hot-Reload
Os serviços montam ./src:/src como volume — alterações no código são refletidas instantaneamente!

📦 Rebuild para dependências
Se mudar requirements.txt ou Dockerfiles:

bash
docker compose up -d --build
