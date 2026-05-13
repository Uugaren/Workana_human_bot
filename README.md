# Workana Human Bot 🤖💼

O **Workana Human Bot** é um sistema de monitorização inteligente e automatizado para freelancers que desejam capturar oportunidades no Workana em tempo real. O diferencial deste bot é o seu **comportamento humanizado**, projetado para simular a navegação de um utilizador real e evitar bloqueios.

---

## 🌟 Funcionalidades Principais

- **Scraping Automatizado:** Monitoriza constantemente novas publicações de projetos com base em palavras-chave específicas.
- **Notificações via Telegram:** Envia alertas instantâneos com título, orçamento, descrição e link direto para o projeto.
- **Comportamento Humanizado:**
  - **Turnos de Trabalho:** O bot opera por períodos (ex: 1 a 2 horas) e faz pausas obrigatórias para "descanso".
  - **Intervalos Randómicos:** O tempo entre as atualizações (F5) varia aleatoriamente para simular um humano a navegar.
  - **User-Agent Real:** Simula navegadores modernos (Chrome/Windows) para evitar deteção de bots.
- **Sistema de Cache:** Utiliza um ficheiro JSON local para garantir que o mesmo projeto nunca seja enviado duas vezes.

---

## 🛠️ Arquitetura do Sistema

O bot utiliza o Selenium para navegação e a API do Telegram para a camada de comunicação.



1. **Camada de Monitorização:** Utiliza o Selenium WebDriver para aceder ao Workana.
2. **Camada de Processamento:** Filtra projetos novos, extrai dados (skills, orçamento) e gera IDs únicos.
3. **Camada de Persistência:** Regista projetos já notificados num histórico local (`.json`).
4. **Camada de Alerta:** Envia a mensagem formatada para o chat/grupo do Telegram configurado.

---

## 🚀 Como Configurar (Ambiente de Staging)

### 1. Pré-requisitos
- Python 3.8 ou superior.
- Google Chrome instalado.
- Um Bot no Telegram (criado via [@BotFather](https://t.me/botfather)).

### 2. Instalação de Dependências
```bash
pip install selenium requests webdriver-manager
