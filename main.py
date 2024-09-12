import telepot
import os
import time
from datetime import datetime
from subprocess import Popen, PIPE
from telepot.loop import MessageLoop

# Fetch Telegram bot token, chat ID, and MySQL credentials from environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')

# Initialize bot
bot = telepot.Bot(BOT_TOKEN)

def send_log_to_telegram(message):
    """
    Function to send log messages to the Telegram chat.
    """
    try:
        bot.sendMessage(CHAT_ID, message)
    except Exception as e:
        print(f"Failed to send log to Telegram: {e}")

def backup_database():
    """
    Function to create a backup of the database in-memory and return the SQL data.
    """
    try:
        # Command to create the SQL dump
        dump_command = f"mysqldump -u {DB_USER} -p{DB_PASS} {DB_NAME}"
        process = Popen(dump_command, shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()

        # Check if the backup was successful by examining the process return code
        if process.returncode == 0:
            send_log_to_telegram(f"Backup process successful for database: {DB_NAME}")
            return stdout
        else:
            send_log_to_telegram(f"Backup failed: {stderr.decode('utf-8')}")
            return None
    except Exception as e:
        send_log_to_telegram(f"Backup process failed: {e}")
        return None

def send_backup_to_telegram(sql_data):
    """
    Function to send the backup SQL data to the Telegram chat as a file.
    """
    try:
        # Save the SQL data temporarily in-memory as a file object
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{DB_NAME}_{timestamp}.sql"

        # Send the SQL data as a file to the Telegram chat
        bot.sendDocument(CHAT_ID, ('backup.sql', sql_data))

        send_log_to_telegram(f"Backup file sent to Telegram: {filename}")
    except Exception as e:
        send_log_to_telegram(f"Error sending backup file to Telegram: {e}")

def handle(msg):
    """
    Function to handle incoming messages and commands.
    """
    content_type, chat_type, chat_id = telepot.glance(msg)
    
    if content_type == 'text':
        message = msg['text']
        
        if message == '/start':
            bot.sendMessage(chat_id, "I'm alive and will send the backup at 11:59 PM daily!")
            send_log_to_telegram("Received /start command - bot is alive.")
        else:
            bot.sendMessage(chat_id, "Unknown command. Use /start to check if I'm alive.")

def run_bot():
    """
    Main function to run the bot and perform the backup at 11:59 PM daily.
    """
    send_log_to_telegram("Bot started. Waiting for 11:59 PM to perform backups.")

    # Start listening for /start commands
    MessageLoop(bot, handle).run_as_thread()

    while True:
        try:
            # Get current time
            now = datetime.now()

            # Check if time is 11:59 PM
            if now.hour == 00 and now.minute == 15:
                send_log_to_telegram(f"Backup process started at {now.strftime('%H:%M')}")

                # Backup database in-memory and send it to Telegram
                sql_data = backup_database()
                if sql_data:
                    send_backup_to_telegram(sql_data)
                else:
                    send_log_to_telegram("Backup process failed.")

                # Wait for 60 seconds to avoid multiple backups in the same minute
                time.sleep(60)
            else:
                # Wait for 30 seconds before checking the time again
                time.sleep(30)

        except Exception as e:
            send_log_to_telegram(f"Error in run_bot loop: {e}")

if __name__ == "__main__":
    # Run the bot
    run_bot()
