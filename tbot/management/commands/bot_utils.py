from tbot.models import Student, President, Teacher  # Import your model here
from asgiref.sync import sync_to_async
from itsdangerous import URLSafeTimedSerializer
from django.conf import settings
from urllib.parse import urlencode


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


def generate_token(chat_id, exam_id):
    serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
    return serializer.dumps({'chat_id': chat_id, 'exam_id': exam_id})


def verify_token(token, max_age=18000):  # Token expires after 5 hour (an hour equals 3600 seconds)
    serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
    try:
        data = serializer.loads(token, max_age=max_age)
        return data  # Contains 'chat_id' and 'exam_id'
    except Exception as e:
        return None  # Invalid or expired token


def create_exam_link(base_url: str, chat_id, exam_id) -> str:
    """
    Create an exam link
    :param base_url: base url of Django project
    :param chat_id:
    :param exam_id:
    :return:
    """
    token = generate_token(chat_id, exam_id)
    params = {
        'chat_id': chat_id,
        'exam_id': exam_id,
        'token': token,
    }
    return f"{base_url}/newExam?{urlencode(params)}"


def create_show_exam_link(base_url: str, chat_id, student_id, exam_id, token) -> str:
    params = {
        'chat_id': chat_id,
        'student_id': student_id,
        'exam_id': exam_id,
        'token': token,
    }
    return f"{base_url}/showExam?{urlencode(params)}"
