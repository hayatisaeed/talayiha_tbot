from datetime import timedelta

from django.db import models
from django.contrib.auth.models import AbstractUser


class President(models.Model):
    fullname = models.CharField(max_length=255, blank=False, null=False)
    username = models.CharField(max_length=255, blank=False, null=False)
    password = models.CharField(max_length=255, blank=False, null=False)
    chat_id = models.CharField(max_length=255, unique=True, blank=False, null=False)


# class Profile(models.Model):
#     national_id = models.CharField(max_length=255, blank=True)
#     phone_number = models.CharField(max_length=255, unique=True)
#     first_name = models.CharField(max_length=255)
#     last_name = models.CharField(max_length=255)
#     fullname = models.CharField(max_length=255, blank=True)
#     chat_id = models.CharField(max_length=255, unique=True)
#
#     TEACHER = 'teacher'
#     STUDENT = 'student'
#     ROLE_CHOICES = [
#         (TEACHER, 'Teacher'),
#         (STUDENT, 'Student'),
#     ]
#
#     role = models.CharField(
#         max_length=10,
#         choices=ROLE_CHOICES,
#         default=STUDENT  # Set a default role if needed
#     )
#
#     city = models.CharField(max_length=255, blank=True)
#     school_name = models.CharField(max_length=255, blank=True)
#
#     def __str__(self):
#         return f"{self.first_name} {self.last_name}"


class Student(models.Model):
    national_id = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=255, unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    fullname = models.CharField(max_length=255, blank=True)
    chat_id = models.CharField(max_length=255, unique=True)
    city = models.CharField(max_length=255, blank=True)
    school_name = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Teacher(models.Model):
    national_id = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=255, unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    fullname = models.CharField(max_length=255, blank=True)
    chat_id = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Olympiad(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Subject(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Topic(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Group(models.Model):
    name = models.CharField(max_length=255)
    info = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Exam(models.Model):
    related_groups = models.ManyToManyField(Group, related_name='exam_groups')
    name = models.CharField(max_length=255)
    related_file = models.FileField(upload_to='examfiles/', blank=True, null=True)  # FileField for uploads

    def __str__(self):
        return self.name


class Answer(models.Model):
    related_exam = models.ForeignKey(Exam, on_delete=models.CASCADE, null=True)
    related_student = models.ForeignKey(Student, on_delete=models.CASCADE)
    related_student_chat_id = models.CharField(max_length=255)
    related_message_id = models.CharField(max_length=2250, blank=True)
    ended = models.BooleanField(default=False)
    time_started = models.DateTimeField(auto_now_add=True)
    time_ended = models.DateTimeField(auto_now=True)
    related_file = models.FileField(upload_to='examfiles/answerfiles', blank=True, null=True)

    def __str__(self):
        return f"Answer by {self.related_student}"

    @property
    def duration(self):
        """
        Returns the duration between time_started and time_ended.
        If time_ended is not set, it calculates duration until now.
        """
        if self.time_ended:
            return self.time_ended - self.time_started
        else:
            return timedelta(0)


class ScoreSheet(models.Model):
    score = models.FloatField()
    related_answer = models.OneToOneField(Answer, on_delete=models.CASCADE, related_name="score_sheet")

    def __str__(self):
        return f"ScoreSheet for Answer {self.related_answer}"


# Intermediary models for ManyToMany relationships
class StudentOlympiad(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="student_olympiad")
    olympiad = models.ForeignKey(Olympiad, on_delete=models.CASCADE)


class TeacherGroup(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="teacher_groups")
    group = models.ForeignKey(Group, on_delete=models.CASCADE)


class StudentGroup(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="student_groups")
    group = models.ForeignKey(Group, on_delete=models.CASCADE)


class GroupExam(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="group_exams")
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)


class ExamStudent(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="exam_students")
    user = models.ForeignKey(Student, on_delete=models.CASCADE)


class OlympiadSubject(models.Model):
    olympiad = models.ForeignKey(Olympiad, on_delete=models.CASCADE, related_name="olympiad_subjects")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
