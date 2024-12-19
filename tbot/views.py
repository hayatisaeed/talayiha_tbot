import datetime
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .management.commands.bot_utils import verify_token, create_show_exam_link
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.utils.timezone import now
from .models import Exam, Answer, Student
from .forms import AnswerFileUploadForm
from django.utils.decorators import method_decorator


from .information import BASE_URL
import openpyxl


@csrf_exempt
def upload_students(request):
    if request.method == "POST" and request.FILES.get("file"):
        file = request.FILES["file"]

        try:
            # Load the Excel workbook
            wb = openpyxl.load_workbook(file)
            sheet = wb.active

            # Iterate through rows, skipping the header
            for row in sheet.iter_rows(min_row=2, values_only=True):
                national_id, phone_number, first_name, last_name, fullname, chat_id, city, school_name = row

                # Create and save the student instance
                Student.objects.create(
                    national_id=national_id,
                    phone_number=phone_number,
                    first_name=first_name,
                    last_name=last_name,
                    fullname=fullname,
                    chat_id=chat_id,
                    city=city,
                    school_name=school_name
                )

            return JsonResponse({"message": "Students uploaded successfully."}, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    elif request.method == "GET":
        return render(request, 'excel_upload.html')
    return JsonResponse({"error": "Invalid request or no file uploaded."}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class AnswerView(View):
    def get(self, request):
        exam_id = request.GET.get('exam_id')
        chat_id = request.GET.get('chat_id')
        student_id = request.GET.get('student_id')
        token = request.GET.get('token')

        if not (chat_id and exam_id and token):
            return JsonResponse({'error': 'Missing parameters'}, status=400)

        data = verify_token(token)
        if not data or str(data['chat_id']) != chat_id or str(data['exam_id']) != exam_id:
            return JsonResponse({'error': 'Invalid or expired token'}, status=403)

        exam = get_object_or_404(Exam, id=exam_id)
        student = get_object_or_404(Student, id=student_id)

        # Retrieve or initialize the Answer object
        answer, created = Answer.objects.get_or_create(
            related_exam=exam,
            related_student=student,
            defaults={'duration': None, 'related_file': None},
        )

        return render(request, 'answer_detail.html', {'exam': exam, 'answer': answer})

    def post(self, request):
        exam_id = request.GET.get('exam_id')
        chat_id = request.GET.get('chat_id')
        student_id = request.GET.get('student_id')
        token = request.GET.get('token')
        if not (chat_id and exam_id and token):
            return JsonResponse({'error': 'Missing parameters'}, status=400)
        data = verify_token(token)
        if not data or str(data['chat_id']) != chat_id or str(data['exam_id']) != exam_id:
            return JsonResponse({'error': 'Invalid or expired token'}, status=403)

        exam = get_object_or_404(Exam, id=exam_id)
        student = get_object_or_404(Student, id=student_id)
        answer = Answer.objects.filter(related_exam=exam, related_student=student).first()
        if not answer:
            return HttpResponseForbidden("You must start the exam first.")

        if 'start' in request.POST:
            # Start the exam timer
            answer.duration = datetime.datetime.now()  # Store the start time in the `duration` temporarily
            answer.save()
            return redirect('answer_detail', exam_id=exam.id, student_id=student.id)

        elif 'submit' in request.POST:
            # Handle answer submission
            uploaded_file = request.FILES.get('related_file')
            if uploaded_file:
                if isinstance(answer.duration, datetime.timedelta):
                    time_taken = now() - answer.duration
                    answer.duration = time_taken
                else:
                    answer.duration = None
                answer.related_file = uploaded_file
                answer.save()
                return redirect('answer_success', exam_id=exam.id, student_id=student.id)

        return render(request, 'answer_detail.html', {'exam': exam, 'answer': answer})


def new_exam_view(request):
    chat_id = request.GET.get('chat_id')
    exam_id = request.GET.get('exam_id')
    token = request.GET.get('token')

    student_id = Student.objects.get(chat_id=chat_id).id

    if not (chat_id and exam_id and token):
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    data = verify_token(token)
    if not data or str(data['chat_id']) != chat_id or str(data['exam_id']) != exam_id:
        return JsonResponse({'error': 'Invalid or expired token'}, status=403)

    url_to_redirect = create_show_exam_link(base_url=BASE_URL,
                                            exam_id=exam_id, chat_id=chat_id, student_id=student_id, token=token)
    return redirect(url_to_redirect)
