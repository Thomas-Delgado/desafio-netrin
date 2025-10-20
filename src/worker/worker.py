import json
import logging
from infrastructure.clients_manager import RedisClient,RabbitMQClient
from worker.scraper import scrape_sintegra

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_task_status(task_id: str, status: str, data: dict = None, error: str = None):
    """Atualiza status da task no Redis"""

    redis_client = RedisClient()

    task_data = {
        "status": status,
        "data": data or {},
        "error": error
    }
    redis_client.set_task_status(task_id, status, task_data, error)
    logger.info(f"Task {task_id} -> {status}")

def process_message(body):
    """
    Processa uma mensagem da fila
    Recebe: {"task_id": "uuid", "cnpj": "00006486000175"}
    """
    try:
        message = json.loads(body)
        task_id = message.get('task_id')
        cnpj = message.get('cnpj')
        
        if not task_id or not cnpj:
            logger.error("Mensagem invalida: task_id ou cnpj ausentes.")
            raise Exception("Mensagem invalida: task_id ou cnpj ausentes.")
        
        logger.info(f"Processando task {task_id} para CNPJ: {cnpj}")
        
        # 1. Muda para processing
        update_task_status(task_id, "processing")
        
        # 2. Faz scraping na Sintegra
        scraped_data = scrape_sintegra(cnpj)
        
        # 3. Muda para completed
        update_task_status(task_id, "completed", scraped_data)
        
        logger.info(f"Task {task_id} concluida")
        
    except Exception as e:
        logger.error(f"Erro processando mensagem: {str(e)}")
        task_id = message.get('task_id')
        if task_id:
            update_task_status(task_id, "error", error=str(e))
        else:
            logger.error("Nao foi possivel atualizar o status da task.")

def start_worker():
    """Funcao principal - inicia o worker"""
    
    logger.info("Iniciando worker com scraping...")
    
    rabbitmq_client = RabbitMQClient()
    
    rabbitmq_client.setup_consumer(process_message)
    
    logger.info('Worker aguardando mensagens...')
    
    try:
        rabbitmq_client.start_consuming()
    except KeyboardInterrupt:
        logger.info("Worker finalizado")
    except Exception as e:
        logger.error(f"Erro: {str(e)}")

if __name__ == "__main__":
    start_worker()