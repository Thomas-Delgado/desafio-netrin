from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch
from app.models import StatusEnum

client = TestClient(app)

## ===================== Testes do endpoint /scrape =====================
@patch("app.infrastructure.clients_manager.RedisClient.set_task_status")
@patch("app.infrastructure.clients_manager.RabbitMQClient.publish_scraping_task")
def test_create_scraping_task_success(mock_rabbit, mock_redis):
    """Cenário de sucesso - cria tarefa de scraping"""
    payload = {"cnpj": "12345678000195"}  # CNPJ válido fictício
    response = client.post("/scrape", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == StatusEnum.ENQUEUED.value

def test_create_scraping_task_invalid_cnpj():
    """Cenário de erro - CNPJ inválido"""
    payload = {"cnpj": "12345"}  # CNPJ inválido
    response = client.post("/scrape", json=payload)

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "CNPJ inválido" in data["detail"]

# ===================== Testes do endpoint /results =====================
@patch("app.infrastructure.clients_manager.RedisClient.get_task_status")
def test_get_scraping_results_success(mock_get_status):
    """Cenário de sucesso - retorna status da tarefa"""
    task_id = "1234-uuid-test"
    response = client.get(f"/results/{task_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id
    assert data["status"] == StatusEnum.COMPLETED.value

@patch("app.infrastructure.clients_manager.RedisClient.get_task_status")
def test_get_scraping_results_not_found(mock_get_status):
    """Cenário de erro - tarefa não encontrada"""
    task_id = "invalid-task-id"
    response = client.get(f"/results/{task_id}")
    
    assert response.status_code == 404

