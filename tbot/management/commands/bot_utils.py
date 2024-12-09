from tbot.models import Student, President, Teacher  # Import your model here
from asgiref.sync import sync_to_async


@sync_to_async
def user_exists(chat_id):
    return True if (
            Student.objects.filter(chat_id=chat_id).exists()
            or President.objects.filter(chat_id=chat_id)
            or Teacher.objects.filter(chat_id=chat_id).exists()) else False


@sync_to_async
def is_teacher(chat_id) -> bool:
    return True if Teacher.objects.filter(chat_id=chat_id).exists() else False


@sync_to_async
def is_student(chat_id) -> bool:
    return True if Student.objects.filter(chat_id=chat_id).exists() else False


@sync_to_async
def is_president(chat_id) -> bool:
    return True if President.objects.filter(chat_id=chat_id).exists() else False
