from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from telegram import Bot
from config import Config
from logger import logger
import time

class UpdateChecker:
    def __init__(self, db, steam_api, bot_token):
        self.db = db
        self.steam_api = steam_api
        self.bot = Bot(token=bot_token)
        self.scheduler = BackgroundScheduler()
        self.jobs = {}
    
    def start(self):
        self.scheduler.start()
        logger.info("Update checker scheduler started")
    
    def stop(self):
        self.scheduler.shutdown()
        logger.info("Update checker scheduler stopped")
    
    def schedule_user_check(self, telegram_id):
        """Schedule or reschedule a user's update check"""
        user = self.db.get_user(telegram_id)
        if not user or not user[1]:  # No Steam ID
            return False
        
        # Remove existing job if any
        self.unschedule_user_check(telegram_id)
        
        # Get user's check interval (default is 6 hours)
        check_interval = user[3] or Config.DEFAULT_CHECK_INTERVAL
        
        # Schedule new job
        job = self.scheduler.add_job(
            self.check_user_updates,
            'interval',
            hours=check_interval,
            args=[telegram_id],
            next_run_time=datetime.now() + timedelta(minutes=1)
        )
        
        self.jobs[telegram_id] = job
        logger.info(f"Scheduled update checks every {check_interval} hours for user {telegram_id}")
        return True
    
    def unschedule_user_check(self, telegram_id):
        """Remove a user's scheduled update checks"""
        if telegram_id in self.jobs:
            self.jobs[telegram_id].remove()
            del self.jobs[telegram_id]
            logger.info(f"Unscheduled update checks for user {telegram_id}")
            return True
        return False
    
    def check_user_updates(self, telegram_id):
        """Check for updates in user's installed games"""
        logger.info(f"Checking updates for user {telegram_id}")
        
        user = self.db.get_user(telegram_id)
        if not user or not user['steam_id']:
            return False
        
        installed_games = self.db.get_installed_games(telegram_id)
        if not installed_games:
            return False
        
        updates_found = 0
        
        for game in installed_games:
            game_id = game['game_id']
            game_name = game['name']
            last_buildid = game['last_buildid']
            
            current_build = self.steam_api.get_current_build_id(game_id)
            if not current_build:
                logger.warning(f"Couldn't get current build for {game_name} (ID: {game_id})")
                continue
            
            logger.debug(f"Game: {game_name} | Last: {last_buildid} | Current: {current_build}")
            
            if last_buildid != current_build:
                changelog = self.steam_api.get_steamdb_changelog(game_id)
                changelog_url = changelog.get('url') if changelog else f"https://steamdb.info/app/{game_id}/patchnotes/"
                
                # Registra a atualização
                self.db.record_update(telegram_id, game_id, game_name, current_build, changelog_url)
                self.db.update_game_buildid(telegram_id, game_id, current_build)
                
                # Notifica o usuário se não estiver em modo silencioso
                if not user['silent_mode']:
                    message = (
                        f"📢 Atualização disponível para {game_name}!\n"
                        f"🕒 Hora da verificação: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                        f"📝 Changelog: {changelog_url}"
                    )
                    try:
                        self.bot.send_message(telegram_id, message)
                    except Exception as e:
                        logger.error(f"Failed to send update notification to {telegram_id}: {e}")
                
                updates_found += 1
        
        logger.info(f"Found {updates_found} updates for user {telegram_id}")
        return updates_found > 0
    
    def check_all_users(self):
        """Check for updates for all users (manual trigger)"""
        logger.info("Starting update check for all users")
        
        with closing(self.db.conn.cursor()) as c:
            c.execute('SELECT telegram_id FROM users WHERE steam_id IS NOT NULL')
            users = c.fetchall()
        
        for (telegram_id,) in users:
            try:
                self.check_user_updates(telegram_id)
            except Exception as e:
                logger.error(f"Error checking updates for user {telegram_id}: {e}")
        
        logger.info("Completed update check for all users")
        
    def unschedule_user_check(self, telegram_id):
        """Remove as verificações agendadas para um usuário"""
        if telegram_id in self.jobs:
            self.jobs[telegram_id].remove()
            del self.jobs[telegram_id]
            logger.info(f"Unscheduled update checks for user {telegram_id}")
            return True
        return False    