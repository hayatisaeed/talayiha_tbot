from django import forms
from .models import Exam, Answer


class AnswerFileUploadForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['related_file']
