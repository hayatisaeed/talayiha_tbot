import datetime
import os
import django
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackContext, \
    ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from django.core.management.base import BaseCommand
from tbot.models import Student, Teacher, President, Exam, Answer, Group, ScoreSheet  # Import your model here
from .bot_utils import is_student, is_teacher, is_president, user_exists, create_exam_link
from functools import wraps
from asgiref.sync import sync_to_async
from tbot.information import BASE_URL
from telegram import InputFile
from django.core.files import File


# Initialize Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "your_project.settings")
django.setup()


# Replace with your bot's token
TOKEN = "8042887753:AAFF9FBEuEgcyeqVnsPC06_KMw2gAsF7Q64"
SERVER_URL = ""

# File paths
SEND_FILE_PATH = "examfiles"  # Update with the file path you want to send
SAVE_DIRECTORY = "examfiles/answerfiles/"  # Update with your desired save directory

# Ensure the save directory exists
os.makedirs(SAVE_DIRECTORY, exist_ok=True)


# Constants for conversation states
SHOW_EXAMS, HANDLE_BUTTON = range(2)


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
        keyboard = [
            [InlineKeyboardButton('My Groups', callback_data='showMyGroups_0')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"""
Welcome  {fullname}!
            """,
            reply_markup=reply_markup
        )
    elif await is_teacher(user_id):
        teacher = await sync_to_async(Teacher.objects.get)(chat_id=user_id)
        fullname = teacher.fullname
        keyboard = [
            # [InlineKeyboardButton('Open Web Panel', url=f"{BASE_URL}/admin")],  # TODO: uncomment this in production
            [InlineKeyboardButton('My Groups', callback_data='showMyGroups_0')],

        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"""
Welcome  {fullname}!

to add a new exam, go to 
{BASE_URL}/admin
and login using your username and password, then create a new exam.
your students answers will be sent to you and you can set their scores by just replying a number to that message.
or you can do it manually from you web panel.
                    """,
            reply_markup=reply_markup
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
{BASE_URL}/admin
            
Your username: {username}
Your password: {password}
            """
        )


async def register(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    await update.message.reply_text(f"""
Your ChatID is:
    
    ```{user_id}```
    
Please use /register command.
    """)


# Function to retrieve exams from the database
def noasync_get_exams(offset=0, limit=10, group_id: int | None = None):
    """
    Fetch exams, optionally filtering by a specific group.

    :param offset: Pagination offset
    :param limit: Pagination limit
    :param group_id: ID of the group to filter exams
    :return: QuerySet of exams
    """
    if group_id:
        # Filter exams related to the specified group
        exams = Exam.objects.filter(related_groups__id=group_id)
    else:
        # Return all exams if no group filter is applied
        exams = Exam.objects.all()

    # Apply offset and limit for pagination
    return exams[offset:offset + limit]


@sync_to_async
def get_exams(offset=0, limit=10, group_id: int | None = None):
    """
    Async wrapper for get_exams.

    :param offset: Pagination offset
    :param limit: Pagination limit
    :param group_id: ID of the group to filter exams
    :return: List of exams
    """
    return list(noasync_get_exams(offset, limit, group_id))


def noasync_get_answers(offset=0, limit=10, group_id: int | None = None):
    """
    Fetch exams, optionally filtering by a specific group.

    :param offset: Pagination offset
    :param limit: Pagination limit
    :param group_id: ID of the group to filter exams
    :return: QuerySet of exams
    """
    if group_id:
        # Filter exams related to the specified group
        answers = Answer.objects.filter(related_exam__related_groups__id=group_id)
    else:
        # Return all exams if no group filter is applied
        answers = Answer.objects.all()

    # Apply offset and limit for pagination
    return answers[offset:offset + limit]


@sync_to_async
def get_answers(offset=0, limit=10, group_id: int | None = None):
    """
    Async wrapper for get_exams.

    :param offset: Pagination offset
    :param limit: Pagination limit
    :param group_id: ID of the group to filter exams
    :return: List of exams
    """
    return list(noasync_get_answers(offset, limit, group_id))


def noasync_get_groups(offset=0, limit=10, teacher=None, student=None):
    """
    Fetch groups related to a specific teacher or student.

    :param offset: Pagination offset
    :param limit: Pagination limit
    :param teacher: Teacher object to filter groups
    :param student: Student object to filter groups
    :return: List of groups
    """
    if teacher:
        # Filter groups related to the teacher
        groups = Group.objects.filter(teachergroup__teacher=teacher)
    elif student:
        # Filter groups related to the student
        groups = Group.objects.filter(studentgroup__student=student)
    else:
        # Return all groups if no specific filter is applied
        groups = Group.objects.all()

    # Apply offset and limit for pagination
    return groups[offset:offset + limit]


@sync_to_async
def get_groups(offset=0, limit=10, teacher=None, student=None):
    """
    Async wrapper for get_groups.

    :param offset: Pagination offset
    :param limit: Pagination limit
    :param teacher: Teacher object to filter groups
    :param student: Student object to filter groups
    :return: List of groups
    """
    return list(noasync_get_groups(offset, limit, teacher, student))


# Function to create the inline keyboard
async def create_exam_buttons(offset=0, group_id=None):
    exams = await get_exams(offset=offset, limit=10, group_id=group_id)
    keyboard = []
    for exam in exams:
        keyboard.append(
            [InlineKeyboardButton(text=exam.name, callback_data=f"exam_{exam.id}")]
        )

    last_row = []
    # Pagination buttons
    if offset > 0:
        last_row.append([InlineKeyboardButton(text="⬅ Previous", callback_data=f"prevExam_{offset}")])
    tmp_exams = await get_exams(offset=offset + 10, limit=10, group_id=group_id)
    if len(tmp_exams) > 0:
        last_row.append([InlineKeyboardButton(text="Next ➡", callback_data=f"nextExam_{offset}")])

    if len(last_row) > 0:
        keyboard.append(last_row)

    return InlineKeyboardMarkup(keyboard)


async def create_answer_buttons(offset=0, group_id=None):
    answers = await get_answers(offset=offset, limit=10, group_id=group_id)
    keyboard = []
    for answer in answers:
        if answer.ended and answer.related_file:
            fullname = await sync_to_async(lambda: answer.related_student.fullname)()
            exam_name = await sync_to_async(lambda: answer.related_exam.name)()
            is_rated = await sync_to_async(lambda: answer.is_rated)()
            keyboard.append(
                [InlineKeyboardButton(text=f"{fullname} - {exam_name} - {'✅' if is_rated else '🟡'}", callback_data=f"answer_{answer.id}")]
            )

    last_row = []
    # Pagination buttons
    if offset > 0:
        last_row.append([InlineKeyboardButton(text="⬅ Previous", callback_data=f"prevAnswer_{offset}")])
    tmp_answers = await get_answers(offset=offset + 10, limit=10, group_id=group_id)
    if len(tmp_answers) > 0:
        last_row.append([InlineKeyboardButton(text="Next ➡", callback_data=f"nextAnswer_{offset}")])

    if len(last_row) > 0:
        keyboard.append(last_row)

    return InlineKeyboardMarkup(keyboard)


async def create_group_buttons(offset=0, student=None, teacher=None):
    groups = await get_groups(offset=offset, limit=10, student=student, teacher=teacher)
    keyboard = []
    for group in groups:
        keyboard.append(
            [InlineKeyboardButton(text=group.name, callback_data=f"group_{group.id}")]
        )

    last_row = []

    # Pagination buttons
    if offset > 0:
        last_row.append(InlineKeyboardButton(text="⬅ Previous", callback_data=f"prevGroup_{offset}"))
    if len(await get_groups(offset=offset + 10, limit=10, student=student, teacher=teacher)) > 0:
        last_row.append(InlineKeyboardButton(text="Next ➡", callback_data=f"nextGroup_{offset}"))
    if len(last_row) > 0:
        keyboard.append(last_row)

    return InlineKeyboardMarkup(keyboard)


# Handler for the /my_exams command
async def exams_command(update: Update, context: CallbackContext) -> int:
    student = await sync_to_async(Student.objects.get)(chat_id=update.effective_user.id)
    keyboard = await create_group_buttons(student=student)
    await update.message.reply_text("Select a group:", reply_markup=keyboard)
    return SHOW_EXAMS


def new_answer(student_id, exam_id, related_student_chat_id, time_started):
    try:
        related_exam = Exam.objects.get(id=exam_id)
        related_student = Student.objects.get(id=student_id)
        answer = Answer(related_student=related_student, related_student_chat_id=related_student_chat_id,
                        related_exam=related_exam, time_started=time_started)
        answer.save()
        return answer
    except Exception as e:
        return None


async def handle_callback_query(update: Update, context: CallbackContext):
    query = update.callback_query

    data = query.data

    if data.startswith("exam_"):
        exam_id = int(data.split("_")[1])
        exam = await sync_to_async(Exam.objects.get)(pk=exam_id)
        keyboard = [
            [InlineKeyboardButton(text=f"Start Exam", callback_data=f"showExam_{exam_id}")],
            [InlineKeyboardButton(text=f"Cancel", callback_data="showMyGroups_0")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"{exam.name}", reply_markup=reply_markup)
        await query.answer()
    elif data.startswith("group_"):
        await query.answer()
        group_id = int(data.split("_")[1])
        group = await sync_to_async(Group.objects.get)(pk=group_id)
        if await is_student(update.effective_user.id):
            reply_markup = await create_exam_buttons(group_id=group_id)
            await query.edit_message_text(
                f"Showing Exams for: {group.name}", reply_markup=reply_markup
            )
        else:
            reply_markup = await create_answer_buttons(group_id=group_id)
            await query.edit_message_text(
                f"Showing Answers of students of: {group.name}", reply_markup=reply_markup
            )
    elif data.startswith("showMyGroups_"):
        await query.answer()
        if await is_student(chat_id=update.effective_user.id):
            student = await sync_to_async(Student.objects.get)(chat_id=update.effective_user.id)
            reply_markup = await create_group_buttons(offset=int(query.data.split("_")[1]), student=student)
        else:
            teacher = await sync_to_async(Teacher.objects.get)(chat_id=update.effective_user.id)
            reply_markup = await create_group_buttons(offset=int(query.data.split("_")[1]), teacher=teacher)
        await query.edit_message_text("Your Groups:", reply_markup=reply_markup)
    elif data.startswith("answer_"):
        answer_id = int(data.split('_')[1])
        try:
            answer = await sync_to_async(Answer.objects.get)(id=answer_id)
        except Exception as e:
            answer = None

        if answer:
            file_path = answer.related_file.path
            with open(file_path, 'rb') as file:
                student_fullname = await sync_to_async(lambda: answer.related_student.fullname)()
                related_exam_name = await sync_to_async(lambda: answer.related_exam.name)()
                message = await context.bot.send_document(
                    chat_id=query.from_user.id,
                    document=InputFile(file, filename=answer.related_file.name),
                    caption=f"Student Name: {student_fullname}"
                    f"\nAnswer to Exam: {related_exam_name}"
                    f"\nDuration: {answer.duration}"
                    f"\n\nReply the score to this message"

                )
            message_id = message.id
            context.user_data[message_id] = answer_id
        else:
            await query.edit_message_text("Nothing was found!")
    elif data.startswith("showExam_"):
        student = await sync_to_async(Student.objects.get)(chat_id=update.effective_user.id)
        student_id = student.id
        exam_id = int(data.split("_")[1])
        exam = await sync_to_async(Exam.objects.get)(id=exam_id)
        if exam.related_file:
            file_path = exam.related_file.path
        else:
            await query.answer("No file for this exam!")
            return
        answer = await sync_to_async(new_answer)(
            student_id=student_id,
            related_student_chat_id=update.effective_user.id,
            exam_id=exam_id,
            time_started=datetime.datetime.now()
        )
        if answer:
            if exam.related_file:
                await query.answer("sending file, wait ...", )
                with open(file_path, 'rb') as file:
                    message = await context.bot.send_document(
                        chat_id=query.from_user.id,
                        document=InputFile(file, filename=exam.related_file.name),
                        caption=f"Exam Started Now! \n"
                        f"Send Your Answer in one file, reply that to this message.\n"
                        f"Duration will be calculated automatically.\n"
                    )
                message_id = message.id
                answer.related_message_id = message_id
                await sync_to_async(answer.save)()
            else:
                await query.answer("Error")
        else:
            await query.answer("error creating answer")
    elif data.startswith("nextExam_"):
        offset = int(data.split("_")[1]) + 10
        keyboard = await create_exam_buttons(offset=offset)
        await query.edit_message_text("Select an exam:", reply_markup=keyboard)
        await query.answer()
    elif data.startswith("prevExam_"):
        offset = int(data.split("_")[1]) - 10
        keyboard = await create_exam_buttons(offset=offset)
        await query.edit_message_text("Select an exam:", reply_markup=keyboard)
        await query.answer()


async def handle_answer_reply(update: Update, context: CallbackContext) -> None:
    if update.message.reply_to_message:  # Ensure the message is a reply
        replied_message = update.message.reply_to_message
        user_message = update.message
        message = update.message
        user_id = update.effective_user.id

        if await is_student(chat_id=user_id):
            # Check if the replied message belongs to the bot
            if replied_message.from_user.id == context.bot.id:
                # Ensure the user isn't replying to their own message
                if replied_message.from_user.id != user_message.from_user.id:
                    if message.document:  # Check if the message contains a document
                        try:
                            answer = await sync_to_async(Answer.objects.get)(
                                related_student_chat_id=update.effective_user.id,
                                related_message_id=replied_message.message_id,
                            )
                            if answer.ended:
                                answer = "Ended"
                            else:
                                answer.ended = True
                                await sync_to_async(answer.save)()
                        except Exception as e:
                            print(e)
                            answer = None
                        if answer == "Ended":
                            await context.bot.send_message(
                                chat_id=update.effective_chat.id,
                                text="Sorry, Exam is already ended."
                            )
                        elif not answer:
                            await context.bot.send_message(
                                chat_id=update.effective_chat.id,
                                text="IDK what to do with this!"
                            )
                        else:
                            # Step 1: Retrieve the file from Telegram
                            file = await context.bot.get_file(message.document.file_id)
                            file_name = message.document.file_name
                            os.makedirs("./tmpFiles", exist_ok=True)
                            file_path = f"./tmpFiles/{file_name}"

                            # Step 2: Download the file to a temporary location
                            await file.download_to_drive(file_path)

                            # Step 3: Save the file to the Django model
                            with open(file_path, 'rb') as f:
                                django_file = File(f)
                                uploaded_file = answer.related_file = django_file
                                await sync_to_async(answer.save)()

                            # Step 4: Respond to the user
                            await context.bot.send_message(
                                chat_id=message.chat.id,
                                text=f"File has been saved successfully! Wait till your score comes out.\n"
                                f"your exam duration: {answer.duration}\n"
                            )

                            # Step 5: Clean up the temporary file
                            os.remove(file_path)
                    else:
                        await context.bot.send_message(
                            chat_id=user_message.chat.id,
                            text="Reply a Document!"
                        )
                else:
                    await context.bot.send_message(
                        chat_id=user_message.chat.id,
                        text="."
                    )
            else:
                await context.bot.send_message(
                    chat_id=user_message.chat.id,
                    text="."
                )
        elif context.user_data.get(replied_message.id, None):  # user is teacher and replied message is correct
            try:
                score = float(update.message.text)
            except ValueError:
                score = None

            if score is None:
                await update.message.reply_text("Send a Valid Number! eg: 10.25")
            else:
                answer_id = context.user_data[replied_message.message_id]
                answer = await sync_to_async(Answer.objects.get)(id=answer_id)
                answer.is_rated = True
                await sync_to_async(answer.save)()
                await sync_to_async(ScoreSheet.objects.create)(related_answer=answer, score=score)
                related_student_chat_id = await sync_to_async(lambda: answer.related_student.chat_id)()
                exam_name = await sync_to_async(lambda: answer.related_exam.name)()
                await update.message.reply_text(f"Done! Score was set: {score}")
                await context.bot.send_message(
                    chat_id=related_student_chat_id,
                    text=f"You have a new score sheet!\n"
                    f"Exam name: {exam_name}\n"
                    f"Your exam duration: {answer.duration}\n"
                    f"\n\nYour exam score: {score}"
                )


reply_to_bot_handler = MessageHandler(filters.REPLY, handle_answer_reply)


async def register_handler(update: Update, context: CallbackContext):
    await update.message.reply_text("Send me your national id (latin numbers):\n/cancel")
    return 'GET_NATIONAL_ID'


async def register_get_phone_number(update: Update, context: CallbackContext):
    try:
        national_id = int(update.message.text)
        context.user_data['national_id'] = str(national_id)
        await update.message.reply_text("Now, send your phone number (eg: 09123456789):")
        return 'GET_PHONE_NUMBER'
    except ValueError:
        await update.message.reply_text("Send a Valid National ID! 10 digits, latin numbers:")
        return 'GET_NATIONAL_ID'


async def register_verify(update: Update, context: CallbackContext):
    try:
        phone_number = update.message.text
        student = await sync_to_async(Student.objects.get)(national_id=context.user_data['national_id'],
                                                           phone_number=phone_number)
        student.chat_id = update.effective_chat.id
        await sync_to_async(student.save)()
        await update.message.reply_text(f"Welcome {student.fullname}!\npress /start again.")
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text("User Not found! please contact admin.")
        return ConversationHandler.END


async def cancel(update: Update, context: CallbackContext):
    """Cancels the conversation."""
    await update.message.reply_text("Registration canceled. Press /start again.")
    return ConversationHandler.END


# Set up the ConversationHandler
registration_conversation = ConversationHandler(
    entry_points=[CommandHandler("register", register_handler)],
    states={
        'GET_NATIONAL_ID': [MessageHandler(filters.TEXT & ~filters.COMMAND, register_get_phone_number)],
        'GET_PHONE_NUMBER': [MessageHandler(filters.TEXT & ~filters.COMMAND, register_verify)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)


def main():
    """Main function to start the bot."""
    # Create an application instance
    application = Application.builder().token(TOKEN).build()

    # Add command and message handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("my_exams", exams_command))
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    application.add_handler(registration_conversation)

    application.add_handler(reply_to_bot_handler)

    # Run the bot
    application.run_polling()


class Command(BaseCommand):
    """Django management command to start the Telegram bot."""
    help = "Run the Telegram bot"

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting the Telegram bot...")
        main()
