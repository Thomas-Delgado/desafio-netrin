from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uuid
from app.models import ScrapingRequest,ScrapingResponse,TaskStatus,StatusEnum,NotFoundError,InvalidRequestError,InternalServerError
from infrastructure.clients_manager import RedisClient, RabbitMQClient
import uvicorn

app = FastAPI(
    title="Scraping Sintegra API",
    description="API para scraping assíncrono de dados da Sintegra",
    version="1.0.0"
)

# ===================== Handlers de Exceptions =====================

@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

@app.exception_handler(InternalServerError)
async def internal_error_handler(request: Request, exc: InternalServerError):
    return JSONResponse(status_code=500, content={"detail": str(exc)})

@app.exception_handler(InvalidRequestError)
async def invalid_request_handler(request: Request, exc: InvalidRequestError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})

# ===================== Endpoints =====================

@app.post("/scrape", response_model=ScrapingResponse)
async def create_scraping_task(request: ScrapingRequest):
    """
    Cria uma nova tarefa de scraping para o CNPJ fornecido na fila do RabbitMQ.
    """

    cnpj = request.cnpj
    # Validação básica do CNPJ
    if not cnpj.isdigit() or len(cnpj) != 14:
        raise InvalidRequestError("CNPJ inválido. Deve conter 14 dígitos numéricos.")

    try:
        redis_client = RedisClient()
        rabbitmq_client = RabbitMQClient()

        #Gera um ID único para a tarefa, salva o status inicial no Redis e publica a tarefa no RabbitMQ
        task_id = str(uuid.uuid4())
        redis_client.set_task_status(task_id, StatusEnum.ENQUEUED.value)
        rabbitmq_client.publish_scraping_task(task_id, cnpj)

        return ScrapingResponse(
            task_id=task_id,
            status=StatusEnum.ENQUEUED,
            message="Tarefa de scraping enfileirada com sucesso."
        )

    except Exception as e:
        raise InternalServerError(f"Erro ao criar tarefa: {str(e)}")


@app.get("/results/{task_id}", response_model=TaskStatus)
async def get_scraping_results(task_id: str):
    """
    Retorna o status da tarefa de scraping e, caso esteja concluída, os dados processados.
    """
    try:
        #Manda buscar o status da tarefa no Redis
        redis_client = RedisClient()
        task_data = redis_client.get_task_status(task_id)

        if not task_data:
            raise NotFoundError(f"Tarefa com ID {task_id} não encontrada.")

        return TaskStatus(
            task_id=task_id,
            status=task_data.get("status"),
            data=task_data.get("data"),
            error=task_data.get("error")
        )

    except NotFoundError as e:
        raise e
    except Exception as e:
        raise InternalServerError(f"Erro ao buscar status da tarefa: {str(e)}")

# ===================== Main =====================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
