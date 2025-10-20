import logging
import os
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FORM_URL = os.getenv(
    "URL_SINTEGRA"
)

def scrape_sintegra(cnpj: str) -> dict:
    """
    Scraping do Sintegra GO com Playwright (Chromium headless).
    Fluxo:
      1) Abre consulta.asp
      2) Preenche CNPJ e clica "Consultar"
      3) Aguarda consultar.asp
      4) Extrai dados com BeautifulSoup
    """
    logger.info(f"Iniciando scraping Playwright para CNPJ: {cnpj}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--window-size=1920,1080",
            ])
            context = browser.new_context()
            page = context.new_page()

            # 1) Abre o formulário
            page.goto(FORM_URL, wait_until="domcontentloaded", timeout=30000)

            # 2) Espera o input e preenche
            page.wait_for_selector('input[name="num_cnpj"]', timeout=15000)
            page.fill('input[name="num_cnpj"]', cnpj)

            # 3) Clica em "Consultar"
            # (nome 'botao' é comum nesse formulário)
            page.click('input[name="botao"]')

            # 4) Aguarda a página de resultado (consultar.asp) ou um seletor estável
            try:
                page.wait_for_url(lambda url: "consultar.asp" in url, timeout=20000)
            except PWTimeout:
                # fallback: espera algum label típico
                page.wait_for_selector("span:has-text('Nome Empresarial')", timeout=10000)

            html = page.content()
            page.close()
            context.close()
            browser.close()

        soup = BeautifulSoup(html, "html.parser")
        data = extract_data_sintegra(soup, cnpj)
        logger.info(f"Scraping Playwright concluído para {cnpj}")
        return data

    except Exception as e:
        logger.error(f"Erro no scraping (Playwright): {e}")
        raise Exception(f"Erro no scraping (Playwright): {e}")


def extract_data_sintegra(soup: BeautifulSoup, cnpj: str) -> dict:
    """Extrai dados principais da página consultar.asp (GO)."""
    data = {
        "cnpj": cnpj,
        "inscricao_estadual": "",
        "razao_social": "",
        "nome_fantasia": "",
        "endereco": "",
        "atividade_principal": "",
        "situacao_cadastral": "",
        "regime_apuracao": "",
        "data_cadastramento": "",
        "erro": ""
    }

    try:
        def get_value(label):
            el = soup.find("span", string=lambda s: s and label in s)
            if el:
                nxt = el.find_next("span")
                if nxt:
                    return nxt.get_text(strip=True)
            return ""

        data["inscricao_estadual"] = get_value("Inscricao Estadual")
        data["razao_social"] = get_value("Nome Empresarial")
        data["nome_fantasia"] = get_value("Nome Fantasia")
        data["situacao_cadastral"] = get_value("Situacao Cadastral Vigente")
        data["regime_apuracao"] = get_value("Regime de Apuracao")
        data["data_cadastramento"] = get_value("Data de Cadastramento")

        # Endereço (pode variar o container)
        end_el = soup.find(lambda tag: tag.name in ("div", "span") and tag.get_text(strip=True).startswith("Endereco"))
        if end_el:
            nxt = end_el.find_next("span")
            if nxt:
                data["endereco"] = nxt.get_text(strip=True)

        # Atividade principal (heurística simples)
        for s in soup.find_all("span"):
            txt = s.get_text(strip=True)
            if " - " in txt and any(ch.isdigit() for ch in txt.split(" - ")[0]):
                data["atividade_principal"] = txt
                break

        # Erro comum
        texto = soup.get_text(" ", strip=True).lower()
        if "não encontrado" in texto or "nao encontrado" in texto:
            data["erro"] = "CNPJ não encontrado na base da Sintegra"

    except Exception as e:
        data["erro"] = f"Falha ao extrair dados: {e}"

    return data
