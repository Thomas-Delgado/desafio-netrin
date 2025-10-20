from unittest.mock import patch, MagicMock
from worker.scraper import scrape_sintegra

# ===================== Success =====================
@patch("requests.post")
def test_scrape_sintegra_success(mock_post):

    # Mocka a resposta do requests.post
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = """
    <html>
        <span class='label_title'>Nome Empresarial</span>
        <span class='label_text'>Empresa Fictícia</span>
    </html>
    """
    mock_post.return_value = mock_response

    data = scrape_sintegra("12345678000195")
    
    assert data is not None
    assert isinstance(data, dict)

# ===================== Error =====================
@patch("requests.post")
def test_scrape_sintegra_error(mock_post):
    # Simula exceção na requisição
    mock_post.side_effect = Exception("Erro na requisição")
    
    data = scrape_sintegra("12345678000195")
    
    assert data is not None
    assert "erro" in data
