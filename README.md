# 🎮 Steam Update Bot (Telegram)

Um bot para Telegram que monitora atualizações dos seus jogos da Steam e te notifica quando novas versões são lançadas.

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Privacy](https://img.shields.io/badge/termos%20e%20privacidade-MIT-green.svg)](https://rveiga08.github.io/steam-bot-privacidade/privacidade.html)


## ✨ Funcionalidades

- 🔔 Notifica quando seus jogos instalados recebem atualizações
- 📊 Mantém estatísticas de atualizações
- 🌐 Suporte a múltiplos idiomas (Inglês, Português, Espanhol)
- ⚙️ Configuração personalizável (intervalo de verificação, modo silencioso)
- 📱 Interface intuitiva via Telegram

## 🛠 Tecnologias

- **Backend**: Python 3.8+
- **Bibliotecas Principais**:
  - `python-telegram-bot` (v20.x) - Interface com o Telegram
  - `requests` - Comunicação com a API da Steam
  - `apscheduler` - Agendamento de verificações periódicas
- **Banco de Dados**: SQLite (armazenamento local)

## 📦 Instalação

1. Clone o repositório:
```bash
git clone https://github.com/rveiga08/steam-update-bot.git
cd steam-update-bot
```

2. Crie e ative um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate   # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
```bash
cp .env.example .env
```

5. Edite o arquivo `.env` com suas credenciais:
```
TELEGRAM_TOKEN=seu_token_aqui
STEAM_API_KEY=sua_chave_steam_api
```

## 🚀 Como Usar

1. Inicie o bot:
```bash
python bot.py
```

2. No Telegram:
- Procure pelo seu bot
- Use o comando `/start` para começar
- `/vincular <steamid>` para conectar sua conta Steam
- `/jogos` para selecionar quais jogos estão instalados

## 📝 Descrição do Repositório

Este projeto foi desenvolvido para ajudar jogadores a ficarem informados sobre atualizações dos seus jogos Steam sem precisar verificar manualmente. O bot oferece:

- Monitoramento automático de atualizações
- Notificações via Telegram quando patches são lançados
- Acesso rápido aos changelogs (via SteamDB)
- Controle sobre quais jogos devem ser monitorados
- Estatísticas de atualizações

## 🤝 Contribuição

Contribuições são bem-vindas! Siga estes passos:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Distribuído sob a licença MIT. Veja [LICENSE](LICENSE) para mais informações.

## ✉️ Contato

Rodrigo Veiga - [@seu_linkedin](https://linkedin.com/rodrigo-veiga) - rveiga08@hotmail.com

Link do Projeto: [https://github.com/rveiga08/steam-update-bot](https://github.com/rveiga08/steam-update-bot)

---

## 📌 Descrição para o Repositório GitHub

🎮 Steam Update Bot - Notificador de Atualizações para Jogos Steam via Telegram

Um bot que monitora seus jogos instalados na Steam e envia notificações quando novas atualizações são lançadas, incluindo:

- 📅 Data/hora da atualização
- 📝 Link para changelog completo
- ⏱️ Histórico de atualizações

### Principais recursos:
✅ Suporte a múltiplos idiomas  
✅ Configuração personalizável  
✅ Interface amigável no Telegram  
✅ Baixo consumo de recursos

**Tecnologias**: Python, Telegram Bot API, Steam Web API, SQLite

---

## 📁 Estrutura Recomendada de Arquivos

```
steam-update-bot/
├── .env.example
├── LICENSE
├── README.md
├── requirements.txt
├── bot.py
├── steam_api.py
├── db.py
├── updater.py
├── config.py
├── logger.py
├── privacidade.html
└── localization/
    ├── en.json
    ├── pt.json
    └── es.json
```

## 🔐 Exemplo de `.env.example`
```
TELEGRAM_TOKEN=seu_token_aqui
STEAM_API_KEY=sua_chave_steam_api
```
