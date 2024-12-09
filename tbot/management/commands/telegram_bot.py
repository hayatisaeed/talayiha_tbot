import os
import django
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext
from django.core.management.base import BaseCommand
from tbot.models import Student, Teacher, President  # Import your model here
from .bot_utils import is_student, is_teacher, is_president, user_exists
from functools import wraps
from asgiref.sync import sync_to_async


# Initialize Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "your_project.settings")
django.setup()


# Replace with your bot's token
TOKEN = ""
SERVER_URL = ""

# File paths
SEND_FILE_PATH = "examfiles"  # Update with the file path you want to send
SAVE_DIRECTORY = "examfiles/answerfiles/"  # Update with your desired save directory

# Ensure the save directory exists
os.makedirs(SAVE_DIRECTORY, exist_ok=True)


def user_authorized(user_id, allowed_roles: set):
    if "all" in allowed_roles and user_exists(user_id):
        return True
    if "president" in allowed_roles and is_president(user_id):
        return True
    if "student" in allowed_roles and is_student(user_id):
        return True
    if "teacher" in allowed_roles and is_teacher(user_id):
        return True

    return False


def check_role(is_authorized, allowed_roles: set):
    """
    A decorator to check if a user is authorized based on their role.

    :param allowed_roles: Roles that are allowed to access this function (Set)
    :param is_authorized: A function that retrieves the user's role based on the update.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id

            if not is_authorized(user_id, allowed_roles):
                await update.message.reply_text("You are not authorized to use this command.")
                return  # Stop further execution if not authorized

            return await func(update, context, *args, **kwargs)

        return wrapper

    return decorator


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command."""
    user_id = update.effective_user.id
    if not await user_exists(user_id):
        await update.message.reply_text(
            "You are not authorized to use this bot, please /register first."
        )
    elif await is_student(user_id):
        student = await sync_to_async(Student.objects.get)(chat_id=user_id)
        fullname = student.fullname
        await update.message.reply_text(
            f"""
            Welcome  {fullname}!
            
            Available Commands:
            
            /my_info  Your Info
            /my_exams  Your New Exams
            /my_scores  Your Scores
            """
        )
    elif await is_teacher(user_id):
        teacher = await sync_to_async(Teacher.objects.get)(chat_id=user_id)
        fullname = teacher.fullname
        await update.message.reply_text(
            f"""
                    Welcome  {fullname}!

                    Available Commands:

                    /my_info  Your Info
                    /my_scores  Your Scores
                    """
        )

    elif await is_president(user_id):
        president = await sync_to_async(President.objects.get)(chat_id=user_id)
        fullname = president.fullname
        username = president.username
        password = president.password
        await update.message.reply_text(
            f"""
            Welcome {fullname},
            please use your web panel:
            {SERVER_URL}/admin
            
            Your username: {username}
            Your password: {password}
            """
        )


async def register(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    await update.message.reply_text(f"""
    Your ChatID is:
    
    ```{user_id}```
    
    Please ask admin to add you to the database.
    """)


def main():
    """Main function to start the bot."""
    # Create an application instance
    application = Application.builder().token(TOKEN).build()

    # Add command and message handlers
    application.add_handler(CommandHandler("start", start))

    # Run the bot
    application.run_polling()


class Command(BaseCommand):
    """Django management command to start the Telegram bot."""
    help = "Run the Telegram bot"

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting the Telegram bot...")
        main()
