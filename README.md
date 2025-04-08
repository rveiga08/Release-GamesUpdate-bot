<<<<<<< HEAD
# Release-GamesUpdate-bot
=======
# Steam Update Notifier Bot 🎮📲

Este projeto é um bot que notifica os usuários via Telegram sempre que um jogo instalado da biblioteca Steam é atualizado.

## Funcionalidades

- Integração com a Steam Web API para listar e monitorar jogos.
- Consulta periódica para verificar atualizações de `buildid`.
- Envio de mensagens via Telegram quando um jogo instalado é atualizado.
- Suporte a múltiplos usuários, com cada um registrando sua SteamID.
- Armazenamento local em banco SQLite.

## Requisitos

- Python 3.8+
- Uma chave da Steam Web API ([obtenha aqui](https://steamcommunity.com/dev/apikey))
- Um token de bot do Telegram ([crie com o BotFather](https://t.me/BotFather))

## Instalação

1. Clone o repositório:

```bash
git clone https://github.com/seuusuario/steam-update-bot.git
cd steam-update-bot
```

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Configure as chaves no arquivo `config.py`:

```python
TELEGRAM_BOT_TOKEN = 'SEU_TOKEN_DO_BOT'
STEAM_API_KEY = 'SUA_CHAVE_DA_STEAM_API'
DB_PATH = 'steam_users.db'
```

4. Execute o verificador de atualizações manualmente:

```bash
python updater.py
```

Ou integre com `cron`, `systemd`, ou qualquer agendador.

## Estrutura do Projeto

- `bot.py` — envio de mensagens pelo Telegram.
- `db.py` — controle de usuários e jogos salvos.
- `steam_api.py` — integração com a Steam Web API.
- `updater.py` — verificação de atualizações.
- `config.py` — configurações do bot (chaves e banco).
- `logger.py` — sistema de logging estruturado.

## Exemplo de Notificação

> 🎮 O jogo *Counter-Strike 2* foi atualizado!  
> Build anterior: `123456` → Nova: `123789`

## License

MIT © 2025 SeuNome
>>>>>>> 29f32aa (Primeiro commit)
