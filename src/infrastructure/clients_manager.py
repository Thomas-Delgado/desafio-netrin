from app.models import NotFoundError
import redis
import pika
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class RedisClient:
    """
    Gerencia operações relacionadas ao Redis.
    """

    def __init__(self, redis_host: str = 'redis') -> None:
        self.redis_host = redis_host
        self.redis_client: Optional[redis.Redis] = None

    def setup_redis(self) -> None:
        """Estabelece conexão com Redis"""
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=6379,
                db=0,
                decode_responses=True,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            self.redis_client.ping()
            logger.info("Conexão Redis estabelecida.")
        except Exception as e:
            logger.error(f"Erro ao conectar com Redis: {str(e)}")
            raise ConnectionError(f"Redis connection failed: {str(e)}") from e

    def set_task_status(
        self,task_id: str,
        status: str,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        cnpj: Optional[str] = None
    ) -> None:
        
        """Salva status da tarefa no Redis"""

        try:
            if not self.redis_client:
                self.setup_redis()
            task_data = {
                "status": status,
                "data": data or {},
                "error": error,
                "cnpj": cnpj
            }
            self.redis_client.setex(
                f"task:{task_id}",
                3600,  # 1 hora
                json.dumps(task_data)
            )
            logger.debug(f"Status salvo: {task_id} -> {status}")
        except Exception as e:
            logger.error(f"Erro ao salvar status no Redis: {str(e)}")
            raise RuntimeError(f"Erro ao salvar status no Redis: {str(e)}") from e

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Busca status da tarefa no Redis"""
        try:
            if not self.redis_client:
                self.setup_redis()

            data = self.redis_client.get(f"task:{task_id}")

            if data:
                return json.loads(data)
            
            raise NotFoundError(f"Tarefa com ID {task_id} não encontrada.")
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Erro ao buscar status no Redis: {str(e)}")
            raise RuntimeError(f"Erro ao buscar status no Redis: {str(e)}") from e


class RabbitMQClient:
    """
    Gerencia operações relacionadas ao RabbitMQ.
    """

    def __init__(self, rabbitmq_host: str = 'rabbitmq') -> None:
        self.rabbitmq_host = rabbitmq_host
        self.rabbitmq_connection: Optional[pika.BlockingConnection] = None
        self.rabbitmq_channel: Optional[pika.channel.Channel] = None

    def setup_rabbitmq(self) -> None:
        """Estabelece conexão e canal com RabbitMQ"""
        try:
            self.rabbitmq_connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=self.rabbitmq_host,
                    credentials=pika.PlainCredentials('guest', 'guest'),
                    heartbeat=600
                )
            )

            self.rabbitmq_channel = self.rabbitmq_connection.channel()
            self.rabbitmq_channel.queue_declare(
                queue='scraping_queue',
                durable=True
            )

            logger.info("Conexão RabbitMQ estabelecida.")
        except Exception as e:
            logger.error(f"Erro ao conectar com RabbitMQ: {str(e)}")
            raise ConnectionError(f"RabbitMQ connection failed: {str(e)}") from e

    def publish_scraping_task(self, task_id: str, cnpj: str) -> None:
        """Publica tarefa de scraping na fila"""
        try:
            if not self.rabbitmq_channel:
                self.setup_rabbitmq()

            message = {"task_id": task_id, "cnpj": cnpj}

            self.rabbitmq_channel.basic_publish(
                exchange='',
                routing_key='scraping_queue',
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2)
            )

            logger.info(f"Tarefa publicada: {task_id} para CNPJ: {cnpj}")

        except Exception as e:
            logger.error(f"Erro ao publicar tarefa no RabbitMQ: {str(e)}")

            raise RuntimeError(f"Erro ao publicar tarefa no RabbitMQ: {str(e)}") from e

    def setup_consumer(self, callback_function) -> None:
        """Configura consumer para a fila de scraping"""
        try:
            if not self.rabbitmq_channel:
                self.setup_rabbitmq()

            self.rabbitmq_channel.basic_consume(
                queue='scraping_queue',
                on_message_callback=callback_function,
                auto_ack=True
            )

            logger.info("Consumer configurado para scraping_queue.")
        except Exception as e:
            logger.error(f"Erro ao configurar consumer: {str(e)}")
            raise RuntimeError(f"Erro ao configurar consumer: {str(e)}") from e

    def start_consuming(self) -> None:
        """Inicia consumo da fila"""
        try:
            if not self.rabbitmq_channel:
                self.setup_rabbitmq()

            logger.info("Iniciando consumo da fila...")
            self.rabbitmq_channel.start_consuming()

        except Exception as e:
            logger.error(f"Erro ao consumir fila: {str(e)}")
            raise RuntimeError(f"Erro ao consumir fila: {str(e)}") from e
