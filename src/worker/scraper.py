import requests
from bs4 import BeautifulSoup
import logging
import os

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def scrape_sintegra(cnpj: str) -> dict:
    """
    Faz scraping do site da Sintegra Goiás.
    Retorna um dicionário com os data ou um campo 'erro' se houver falha.

    """
    try:
        logger.info(f"Iniciando scraping REAL para CNPJ: {cnpj}")
        
        url = os.environ.get('URL_SINTEGRA')
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://appasp.sefaz.go.gov.br',
            'Referer': 'https://appasp.sefaz.go.gov.br/sintegra/consulta/default.html',
        }
        form_data = {'num_cnpj': cnpj, 'botao': 'Consultar'}
        
        #Manda uma requisição POST para o site da Sintegra com o CNPJ e os headers apropriados
        response = requests.post(url, data=form_data, headers=headers, timeout=30)
        if response.status_code != 200:
            raise Exception(f"Erro {e}.")

        soup = BeautifulSoup(response.content, 'html.parser')
        data = extract_data_sintegra(soup, cnpj)

        logger.info(f"Scraping concluído para {cnpj}.")
        return data
        
    except requests.exceptions.Timeout:
        raise Exception("Timeout ao acessar o site da Sintegra.")
    except Exception as e:
        raise Exception(f"Erro no scraping: {str(e)}")


def extract_data_sintegra(soup: BeautifulSoup, cnpj: str) -> dict:
    """
    Extrai os data relevantes do HTML retornado pela Sintegra.
    """

    data = {
        "cnpj": cnpj,
        "inscricao_estadual": "",
        "razao_social": "",
        "nome_fantasia": "",
        "endereco": "",
        "atividade_principal": "",
        "situacao_cadastral": "",
        "regime_apuracao": "",
        "data_cadastramento": ""
    }

    try:
        # Realiza a extração dos campos necessários no HTML
        # Inscrição Estadual
        ie_el = soup.find('span', class_='label_title', string='Inscricao Estadual')
        if ie_el:
            ie_text = ie_el.find_next_sibling('span', class_='label_text')
            if ie_text:
                data['inscricao_estadual'] = ie_text.text.strip()
        
        # Nome Empresarial e Fantasia
        razao_el = soup.find('span', class_='label_title', string='Nome Empresarial')
        if razao_el:
            razao_text = razao_el.find_next_sibling('span', class_='label_text')
            if razao_text:
                data['razao_social'] = razao_text.text.strip()
        
        fantasia_el = soup.find('span', class_='label_title', string='Nome Fantasia')
        if fantasia_el:
            fantasia_text = fantasia_el.find_next_sibling('span', class_='label_text')
            if fantasia_text:
                data['nome_fantasia'] = fantasia_text.text.strip()
        
        # Endereço
        endereco_el = soup.find('div', class_='label_title', string='Endereco Estabelecimento')
        if endereco_el:
            endereco_text = endereco_el.find_next_sibling('span', class_='label_text')
            if endereco_text:
                data['endereco'] = endereco_text.text.strip()
        
        # Atividade Principal
        atividade_texts = soup.find_all('span', class_='label_text')
        for texto in atividade_texts:
            if ' - ' in texto.text and any(c.isdigit() for c in texto.text.split(' - ')[0]):
                data['atividade_principal'] = texto.text.strip()
        
        # Informações complementares
        situacao_el = soup.find('span', class_='label_title', string='Situacao Cadastral Vigente:')
        if situacao_el:
            situacao_text = situacao_el.find_next_sibling('span', class_='label_text')
            if situacao_text:
                data['situacao_cadastral'] = situacao_text.text.strip()
        
        regime_el = soup.find('span', class_='label_title', string='Regime de Apuracao:')
        if regime_el:
            regime_text = regime_el.find_next_sibling('span', class_='label_text')
            if regime_text:
                data['regime_apuracao'] = regime_text.text.strip()
        
        data_cad_el = soup.find('span', class_='label_title', string='Data de Cadastramento:')
        if data_cad_el:
            data_cad_text = data_cad_el.find_next_sibling('span', class_='label_text')
            if data_cad_text:
                data['data_cadastramento'] = data_cad_text.text.strip()
        
        # Verifica se CNPJ é inválido
        texto_pagina = soup.get_text()
        if 'nao encontrado' in texto_pagina.lower() or 'nao existe' in texto_pagina.lower():
            data['erro'] = 'CNPJ nao encontrado na base da Sintegra'
        
    except Exception as e:
        data['erro'] = f"Falha ao extrair data: {str(e)}"
    
    return data
