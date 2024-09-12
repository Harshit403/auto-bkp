import os
import time
import logging
import telepot
from datetime import datetime
from telepot.loop import MessageLoop
from dotenv import load_dotenv
from io import BytesIO
import subprocess

# Load environment variables from .env file
load_dotenv()

# Get environment variables
TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
MYSQL_USER = os.getenv('DB_USER')
MYSQL_PASSWORD = os.getenv('DB_PASS')
MYSQL_DATABASE = os.getenv('DB_NAME')

# Initialize bot
bot = telepot.Bot(TOKEN)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def send_message(text):
    """Send a text message to the bot."""
    bot.sendMessage(CHAT_ID, text)

def send_backup_file(file_bytes, filename):
    """Send a backup file to the bot."""
    file = BytesIO(file_bytes)
    file.name = filename
    try:
        bot.sendDocument(CHAT_ID, file)
        logging.info(f"Backup file {filename} sent to Telegram successfully.")
    except Exception as e:
        logging.error(f"Error sending backup file to Telegram: {e}")
        send_message(f"Error sending backup file to Telegram: {e}")

def backup_database():
    """Create a backup of the MySQL database and send it to Telegram."""
    now = datetime.now()
    filename = f"{now.strftime('%Y%m%d_%H%M%S')}.sql"
    
    # Backup command
    backup_command = [
        'mysqldump',
        '-u', MYSQL_USER,
        f'-p{MYSQL_PASSWORD}',
        MYSQL_DATABASE
    ]
    
    try:
        # Run the backup command and capture the output
        result = subprocess.run(backup_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if result.returncode == 0:
            logging.info(f"Backup process successful for database: {MYSQL_DATABASE}")
            # Send the output to Telegram as a file
            send_backup_file(result.stdout, filename)
        else:
            logging.error(f"Backup process failed: {result.stderr.decode('utf-8')}")
            send_message(f"Backup process failed: {result.stderr.decode('utf-8')}")
    except Exception as e:
        logging.error(f"Error during backup process: {e}")
        send_message(f"Error during backup process: {e}")

def handle(msg):
    """Handle incoming Telegram messages."""
    content_type, chat_type, chat_id = telepot.glance(msg)
    
    if content_type == 'text':
        command = msg['text'].strip().lower()
        if command == '/start':
            send_message("Bot is alive!")
        elif command == '/backup':
            send_message("Initiating manual backup...")
            backup_database()  # Trigger manual backup on /backup command
        else:
            send_message("Unknown command!")

def run_backup_scheduler():
    """Schedule the backup to run every day at 12:15 AM."""
    while True:
        now = datetime.now()
        if now.hour == 0 and now.minute == 44:
            backup_database()
            time.sleep(60)  # Sleep for a minute to avoid running multiple times
        time.sleep(1)  # Check every second

if __name__ == "__main__":
    # Start the bot and handle messages
    MessageLoop(bot, handle).run_as_thread()
    logging.info("Bot is running. Waiting for commands...")

    # Run the backup scheduler in the background
    run_backup_scheduler()
