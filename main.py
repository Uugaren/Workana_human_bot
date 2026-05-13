import time
import threading
import requests
import logging
import random
import json
import os
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Configuração de Logging para monitoramento do bot
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WorkanaHumanBot:
    def __init__(self, telegram_token, telegram_chat_id, cache_file="historico_projetos.json", headless=True):
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
        self.cache_file = cache_file
        self.driver = None
        self.wait = None
        self.headless = headless
        self.monitoring_active = False
        self.monitoring_thread = None
        self.sent_projects = self._load_cache()

    def _load_cache(self):
        """Carrega os IDs dos projetos já enviados do arquivo JSON para evitar duplicidade"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    logger.info(f" Histórico carregado: {len(data)} projetos já registrados no cache.")
                    return set(data)
            except Exception as e:
                logger.error(f"Erro ao ler cache: {e}")
        return set()

    def _save_cache(self):
        """Salva os IDs atuais no arquivo JSON de persistência"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(list(self.sent_projects), f)
        except Exception as e:
            logger.error(f"Erro ao salvar cache: {e}")

    def _setup_driver(self):
        """Inicia o navegador com User-Agent real para simular acesso humano"""
        logger.info(" Abrindo navegador para novo turno...")
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        chrome_options.add_argument("--log-level=3")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)

    def send_telegram_notification(self, project):
        """Envia os dados do projeto via API do Telegram"""
        if not self.telegram_token or not self.telegram_chat_id: 
            logger.warning("Token ou Chat ID não configurados.")
            return False

        message = f"""
<b>NOVO PROJETO DETECTADO!</b>

<b>Título:</b> {project['title']}
<b>Orçamento:</b> {project['budget']}
<b>Skills:</b> {', '.join(project['skills'])}

<b>Resumo:</b>
{project['description'][:250]}...

🔗 <a href="{project['url']}"><b>CLIQUE AQUI PARA ABRIR</b></a>
        """
        
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        data = {"chat_id": self.telegram_chat_id, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}
        
        try:
            requests.post(url, data=data)
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar Telegram: {e}")
            return False

    def search_projects(self, keywords):
        """Realiza a busca no Workana baseada em palavras-chave"""
        try:
            search_url = f"https://www.workana.com/jobs?language=pt&publication=1d&query={keywords.replace(' ', '%20')}"
            self.driver.get(search_url)
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            projects = []
            project_elements = self.driver.find_elements(By.CSS_SELECTOR, '.project-item')
            
            for element in project_elements:
                try:
                    title_elem = element.find_element(By.CSS_SELECTOR, 'h2.project-title a')
                    title = title_elem.text.strip()
                    url = title_elem.get_attribute('href')
                    
                    try: desc = element.find_element(By.CSS_SELECTOR, '.project-details').text.strip()
                    except: desc = "Detalhes não disponíveis"
                    
                    try: budget = element.find_element(By.CSS_SELECTOR, '.budget .values').text.strip()
                    except: budget = "N/A"
                    
                    skills = [s.text for s in element.find_elements(By.CSS_SELECTOR, 'label-skill')]
                    
                    projects.append({'title': title, 'url': url, 'description': desc, 'budget': budget, 'skills': skills})
                except: continue
            return projects
        except Exception as e:
            logger.error(f"Erro durante o scraping: {e}")
            return []

    def get_project_id(self, url):
        """Extrai o ID único do projeto da URL"""
        if not url: return "unknown"
        try:
            if "/project/" in url: return url.split("/project/")[1].split("-")[0]
        except: pass
        return str(hash(url))

    def run_shift(self, keywords, duration_minutes, min_f5, max_f5):
        """Executa um turno de monitoramento com intervalos de atualização aleatórios"""
        self._setup_driver()
        self.monitoring_active = True
        
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        logger.info(f"Turno iniciado. Trabalhando até: {end_time.strftime('%H:%M')}")
        
        try:
            first_run = True
            while self.monitoring_active and datetime.now() < end_time:
                if not first_run:
                    wait_time = random.uniform(min_f5, max_f5)
                    logger.info(f"Pausa entre atualizações: {wait_time:.1f} min")
                    time.sleep(wait_time * 60)
                
                first_run = False
                projects = self.search_projects(keywords)
                new_found = 0
                
                for project in projects:
                    p_id = self.get_project_id(project['url'])
                    if p_id not in self.sent_projects:
                        if self.send_telegram_notification(project):
                            self.sent_projects.add(p_id)
                            self._save_cache()
                            new_found += 1
                            time.sleep(random.uniform(2, 5)) # Delay entre mensagens
                
                if new_found > 0:
                    logger.info(f" {new_found} novos projetos enviados para o Telegram.")
                else:
                    logger.info("Nenhuma novidade encontrada nesta rodada.")

        except Exception as e:
            logger.error(f"Erro fatal no turno: {e}")
        finally:
            self.stop_driver()

    def stop_driver(self):
        """Encerra o processo do Selenium"""
        self.monitoring_active = False
        if self.driver:
            logger.info(" Encerrando navegador (Fim do turno/pausa)...")
            try:
                self.driver.quit()
            except: pass
            self.driver = None

# --- ORQUESTRADOR DE ROTINA ---

if __name__ == "__main__":
    # CONFIGURAÇÕES DE STAGING / MOCKUP
    # Use variáveis de ambiente (export TELEGRAM_TOKEN=...) para maior segurança
    TOKEN = os.getenv("TELEGRAM_TOKEN", "0000000000:MOCKUP_TOKEN_PLACEHOLDER_STAGING")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "123456789")
    KEYWORDS = "chatbot automation python"
    MODO_INVISIVEL = True
    ARQUIVO_HISTORICO = "cache_staging_projetos.json"

    # Parâmetros de Comportamento (em minutos)
    TURNO_MIN, TURNO_MAX = 45, 90     # Duração do tempo online
    PAUSA_MIN, PAUSA_MAX = 10, 20     # Tempo fora do ar (descanso)
    REFRESH_MIN, REFRESH_MAX = 4, 8   # Intervalo entre buscas (F5)

    bot = WorkanaHumanBot(TOKEN, CHAT_ID, cache_file=ARQUIVO_HISTORICO, headless=MODO_INVISIVEL)

    logger.info("Iniciando Bot em modo Staging - Monitoramento Humanizado.")
    
    try:
        while True:
            # Define tempo de trabalho aleatório
            tempo_trabalho = random.randint(TURNO_MIN, TURNO_MAX)
            bot.run_shift(KEYWORDS, duration_minutes=tempo_trabalho, min_f5=REFRESH_MIN, max_f5=REFRESH_MAX)
            
            # Define tempo de descanso aleatório
            tempo_descanso = random.randint(PAUSA_MIN, PAUSA_MAX)
            previsao_retorno = datetime.now() + timedelta(minutes=tempo_descanso)
            
            logger.info(f"Bot em pausa para descanso por {tempo_descanso} minutos.")
            logger.info(f"Próximo turno inicia às: {previsao_retorno.strftime('%H:%M')}")
            
            time.sleep(tempo_descanso * 60)
            logger.info("Reiniciando atividades...")

    except KeyboardInterrupt:
        logger.info("Processo interrompido manualmente pelo usuário.")
