import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from db import Database
from steam_api import SteamAPI
from updater import UpdateChecker
from config import Config
from logger import logger
from contextlib import closing

def load_localization():
    """Carrega os arquivos de localização da pasta 'localization'"""
    localization = {}
    localization_dir = os.path.join(os.path.dirname(__file__), 'localization')
    
    if not os.path.exists(localization_dir):
        logger.error(f"Localization directory not found: {localization_dir}")
        return {'en': {}}
    
    for filename in os.listdir(localization_dir):
        if filename.endswith('.json'):
            lang = filename.split('.')[0]
            try:
                filepath = os.path.join(localization_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    localization[lang] = json.load(f)
            except Exception as e:
                logger.error(f"Error loading {filename}: {e}")
    return localization

LOCALIZATION = load_localization()

class SteamUpdateBot:
    def __init__(self, token):
        # Configuração da Application (substitui o Updater)
        self.application = Application.builder().token(token).build()
        self.db = Database()
        self.steam_api = SteamAPI()
        self.update_checker = UpdateChecker(self.db, self.steam_api, token)
        
        # Handlers de comandos
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("vincular", self.link_account))
        self.application.add_handler(CommandHandler("games", self.list_games))
        self.application.add_handler(CommandHandler("status", self.status))
        self.application.add_handler(CommandHandler("stats", self.stats))
        self.application.add_handler(CommandHandler("settings", self.settings))
        self.application.add_handler(CommandHandler("language", self.language))
        self.application.add_handler(CommandHandler("delete", self.delete_account))
        
        # Handler de mensagens
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Handler de callbacks
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Handler de erros
        self.application.add_error_handler(self.error_handler)

    def get_text(self, update, key):
        """Get localized text for the user"""
        user = self.db.get_user(update.effective_user.id)
        lang = user[2] if user and user[2] else 'en'
        return LOCALIZATION.get(lang, {}).get(key, LOCALIZATION['en'].get(key, key))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        self.db.add_user(user_id)
        
        welcome_msg = self.get_text(update, 'welcome_message')
        help_msg = self.get_text(update, 'help_message')
        
        await update.message.reply_text(f"{welcome_msg}\n\n{help_msg}")

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_msg = self.get_text(update, 'help_message')
        await update.message.reply_text(help_msg)

    async def link_account(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        args = context.args
        
        if not args:
            await update.message.reply_text(self.get_text(update, 'provide_steam_id'))
            return
        
        steam_input = args[0]
        steam_id = self.steam_api.get_steam_id_from_url(steam_input)
        
        if not steam_id:
            await update.message.reply_text(self.get_text(update, 'invalid_steam_id'))
            return
        
        games = self.steam_api.get_owned_games(steam_id)
        if not games:
            await update.message.reply_text(self.get_text(update, 'private_profile_error'))
            return
        
        self.db.update_steam_id(user_id, steam_id)
        
        for game in games:
            self.db.add_or_update_game(
                user_id,
                game['appid'],
                game.get('name', f"AppID {game['appid']}"),
                installed=False,
                last_played=game.get('playtime_forever', 0)
            )
        
        self.update_checker.schedule_user_check(user_id)
        await update.message.reply_text(self.get_text(update, 'account_linked_success'))

    async def list_games(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user = self.db.get_user(user_id)
        
        if not user or not user[1]:  # Verifica se o usuário tem Steam ID vinculado
            await update.message.reply_text(self.get_text(update, 'link_account_first'))
            return
        
        # Busca os jogos da biblioteca Steam
        games = self.steam_api.get_owned_games(user[1])
        if not games:
            await update.message.reply_text(self.get_text(update, 'no_games_found'))
            return
        
        # Verifica se a resposta da API está no formato esperado
        if isinstance(games, dict) and 'games' in games.get('response', {}):
            games = games['response']['games']
        
        # Ordena os jogos por tempo jogado (decrescente)
        games.sort(key=lambda x: x.get('playtime_forever', 0), reverse=True)
        
        # Prepara o teclado com os jogos
        keyboard = []
        for game in games:
            game_id = game['appid']
            game_name = game.get('name', f"AppID {game_id}")
            playtime_hours = game.get('playtime_forever', 0) // 60
            
            # Verifica se o jogo já está marcado como instalado
            is_installed = self.db.is_game_installed(user_id, game_id)
            status_emoji = "✅" if is_installed else "❌"
            
            text = f"{status_emoji} {game_name}"
            if playtime_hours > 0:
                text += f" ({playtime_hours}h)"
                
            keyboard.append([InlineKeyboardButton(text, callback_data=f"toggle_{game_id}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            self.get_text(update, 'select_games_to_toggle'),
            reply_markup=reply_markup
        )

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        installed_games = self.db.get_installed_games(user_id)
        
        if not installed_games:
            await update.message.reply_text(self.get_text(update, 'no_installed_games'))
            return
        
        message = self.get_text(update, 'installed_games_header') + "\n\n"
        for game_id, game_name, last_buildid, last_played in installed_games:
            played_hours = last_played // 60
            message += f"🎮 {game_name}"
            message += f" ({played_hours}h)" if played_hours > 0 else ""
            message += f"\n🆔 Build ID: {last_buildid}\n\n"
        
        await update.message.reply_text(message)

    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        stats = self.db.get_user_stats(user_id)
        
        if not stats:
            await update.message.reply_text(self.get_text(update, 'no_stats_available'))
            return
        
        message = self.get_text(update, 'stats_header') + "\n\n"
        message += f"📊 Total updates tracked: {stats['total_updates']}\n"
        message += f"🕒 Last update detected: {stats['last_update'] or 'Never'}\n"
        message += f"🎮 Games installed: {stats['installed_count']}\n\n"
        
        if stats['recent_updates']:
            message += self.get_text(update, 'recent_updates_header') + "\n"
            for game_name, update_time in stats['recent_updates']:
                message += f"• {game_name} ({update_time})\n"
        
        await update.message.reply_text(message)

    async def settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user = self.db.get_user(user_id)
        
        if not user:
            await update.message.reply_text(self.get_text(update, 'unexpected_error'))
            return
        
        keyboard = [
            [
                InlineKeyboardButton(
                    self.get_text(update, 'change_check_interval'),
                    callback_data="setting_interval"
                )
            ],
            [
                InlineKeyboardButton(
                    self.get_text(update, 'toggle_silent_mode'),
                    callback_data="setting_silent"
                )
            ],
            [
                InlineKeyboardButton(
                    self.get_text(update, 'change_language'),
                    callback_data="setting_language"
                )
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        settings_msg = self.get_text(update, 'current_settings') + "\n\n"
        settings_msg += f"🕒 Check interval: {user[3]} hours\n"
        settings_msg += f"🔇 Silent mode: {'On' if user[4] else 'Off'}\n"
        settings_msg += f"🌐 Language: {user[2]}\n"
        
        await update.message.reply_text(settings_msg, reply_markup=reply_markup)
        
    async def delete_account(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
    
        keyboard = [
            [InlineKeyboardButton(self.get_text(update, 'yes_delete'), callback_data="confirm_delete")],
            [InlineKeyboardButton(self.get_text(update, 'cancel'), callback_data="cancel_delete")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            self.get_text(update, 'delete_confirmation'),
            reply_markup=reply_markup
        )    

    async def language(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        args = context.args
        
        if not args:
            await update.message.reply_text(self.get_text(update, 'provide_language'))
            return
        
        lang = args[0].lower()
        if lang not in LOCALIZATION:
            await update.message.reply_text(self.get_text(update, 'invalid_language'))
            return
        
        self.db.update_user_setting(user_id, 'language', lang)
        await update.message.reply_text(self.get_text(update, 'language_changed'))

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        try:
            if data.startswith("toggle_"):
                game_id = int(data.split("_")[1])
                
                # Obter nome do jogo antes de fazer qualquer alteração
                game_name = None
                with closing(self.db.conn.cursor()) as c:
                    c.execute('''SELECT name FROM games 
                                WHERE telegram_id = ? AND game_id = ?''', 
                                (user_id, game_id))
                    result = c.fetchone()
                    if result:
                        game_name = result[0]
                
                if game_name:
                    # Alternar status de instalação
                    with closing(self.db.conn.cursor()) as c:
                        c.execute('''UPDATE games SET installed = NOT installed 
                                    WHERE telegram_id = ? AND game_id = ?''', 
                                    (user_id, game_id))
                        self.db.conn.commit()
                    
                    # Verificar novo status
                    with closing(self.db.conn.cursor()) as c:
                        c.execute('''SELECT installed FROM games 
                                    WHERE telegram_id = ? AND game_id = ?''', 
                                    (user_id, game_id))
                        new_status = c.fetchone()[0]
                    
                    status_msg = self.get_text(update, 'game_installed') if new_status else self.get_text(update, 'game_uninstalled')
                    await query.edit_message_text(f"{game_name} - {status_msg}")
                    
                    # Reschedule checks if needed
                    installed_count = 0
                    with closing(self.db.conn.cursor()) as c:
                        c.execute('''SELECT COUNT(*) FROM games 
                                    WHERE telegram_id = ? AND installed = TRUE''', 
                                    (user_id,))
                        installed_count = c.fetchone()[0]
                    
                    if installed_count == (1 if new_status else 0):
                        self.update_checker.schedule_user_check(user_id)
                else:
                    await query.edit_message_text(self.get_text(update, 'game_not_found'))
            
            elif data == "confirm_delete":
                try:
                    with closing(self.db.conn.cursor()) as c:
                        # Remove todos os dados do usuário
                        c.execute('DELETE FROM users WHERE telegram_id = ?', (user_id,))
                        c.execute('DELETE FROM games WHERE telegram_id = ?', (user_id,))
                        c.execute('DELETE FROM updates WHERE telegram_id = ?', (user_id,))
                        c.execute('DELETE FROM stats WHERE telegram_id = ?', (user_id,))
                        self.db.conn.commit()
                    
                    # Cancela verificações agendadas
                    self.update_checker.unschedule_user_check(user_id)
                    
                    await query.edit_message_text(
                        "🗑️ Todos os seus dados foram excluídos com sucesso.\n\n"
                        "Se quiser usar o bot novamente, digite /start"
                    )
                except Exception as e:
                    logger.error(f"Error deleting account {user_id}: {e}")
                    await query.edit_message_text("❌ Ocorreu um erro ao excluir seus dados. Por favor, tente novamente.")

            elif data == "cancel_delete":
                await query.edit_message_text("✅ Operação cancelada. Seus dados não foram alterados.")
            
            # Adicione estas condições para lidar com os botões de configuração
            elif data == "setting_interval":
                keyboard = [
                    [InlineKeyboardButton("1 hora", callback_data="interval_1")],
                    [InlineKeyboardButton("3 horas", callback_data="interval_3")],
                    [InlineKeyboardButton("6 horas", callback_data="interval_6")],
                    [InlineKeyboardButton("12 horas", callback_data="interval_12")],
                    [InlineKeyboardButton("24 horas", callback_data="interval_24")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    self.get_text(update, 'select_interval'),
                    reply_markup=reply_markup
                )
            
            elif data.startswith("interval_"):
                interval = int(data.split("_")[1])
                self.db.update_user_setting(user_id, 'check_interval', interval)
                self.update_checker.schedule_user_check(user_id)
                await query.edit_message_text(
                    self.get_text(update, 'interval_set').format(interval=interval)
                )
            
            elif data == "setting_silent":
                user = self.db.get_user(user_id)
                new_status = not user[4]
                self.db.update_user_setting(user_id, 'silent_mode', new_status)
                
                status_msg = self.get_text(update, 'silent_mode_on') if new_status else self.get_text(update, 'silent_mode_off')
                await query.edit_message_text(status_msg)
            
            elif data == "setting_language":
                keyboard = [
                    [InlineKeyboardButton("English", callback_data="lang_en")],
                    [InlineKeyboardButton("Português", callback_data="lang_pt")],
                    [InlineKeyboardButton("Español", callback_data="lang_es")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    self.get_text(update, 'select_language'),
                    reply_markup=reply_markup
                )
            
            elif data.startswith("lang_"):
                lang = data.split("_")[1]
                self.db.update_user_setting(user_id, 'language', lang)
                await query.edit_message_text(self.get_text(update, 'language_changed'))
        
        except Exception as e:
            logger.error(f"Error in button_callback: {e}")
            await query.edit_message_text(self.get_text(update, 'unexpected_error'))

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(self.get_text(update, 'unrecognized_command'))

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.error(f"Error while handling update {update}: {context.error}")
        
        if update and update.effective_user:
            try:
                await update.effective_user.send_message(
                    self.get_text(update, 'unexpected_error_occurred')
                )
            except:
                pass

    def run(self):
        self.update_checker.start()
        self.application.run_polling()
        self.update_checker.stop()
        self.db.close()

if __name__ == '__main__':
    bot = SteamUpdateBot(Config.TELEGRAM_TOKEN)
    bot.run()