from django.contrib import admin

from tbot.models import *
from django.utils.translation import gettext_lazy as _
from .excel import export_to_excel


class OlympiadFilter(admin.SimpleListFilter):
    title = _('Olympiad')
    parameter_name = 'olympiad'

    def lookups(self, request, model_admin):
        # Get unique Olympiad instances linked to any Student
        olympiads = StudentOlympiad.objects.values_list('olympiad', 'olympiad__name').distinct()
        return [(olympiad_id, olympiad_name) for olympiad_id, olympiad_name in olympiads]

    def queryset(self, request, queryset):
        if self.value():
            # Filter Students that are linked to the selected olympiad
            return queryset.filter(Studentolympiad__olympiad_id=self.value())
        return queryset


class StudentOlympiadInline(admin.TabularInline):
    model = StudentOlympiad
    extra = 1  # Number of empty forms to display
    autocomplete_fields = ['student']  # If you have a large number of students, use autocomplete


class OlympiadAdmin(admin.ModelAdmin):
    inlines = [StudentOlympiadInline]
    search_fields = ['name']  # Add fields suitable for searching Olympiads


class OlympiadInline(admin.TabularInline):
    model = StudentOlympiad
    extra = 1
    autocomplete_fields = ['student', 'olympiad']


class TeacherInline(admin.TabularInline):
    model = TeacherGroup
    extra = 1
    autocomplete_fields = ['teacher', 'group']


class TeacherAdmin(admin.ModelAdmin):
    inlines = [TeacherInline]
    search_fields = ['fullname', 'phone_number', 'national_id', 'chat_id']
    list_display = ['fullname', 'phone_number', 'national_id', 'chat_id']


class StudentInline(admin.TabularInline):
    model = StudentGroup
    extra = 1
    autocomplete_fields = ['student', 'group']


class StudentAdmin(admin.ModelAdmin):
    inlines = [OlympiadInline, StudentInline]
    search_fields = ['fullname', 'phone_number', 'national_id', 'chat_id', 'city']
    list_display = ['fullname', 'phone_number', 'national_id', 'chat_id', 'city']
    export_to_excel.short_description = "Export selected users to Excel"
    actions = [export_to_excel]
    list_filter = [OlympiadFilter, 'city', 'school_name']


class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'info']
    inlines = [TeacherInline, StudentInline]
    search_fields = ['name', 'info']


admin.site.register(Student, StudentAdmin)
admin.site.register(Teacher, TeacherAdmin)
admin.site.register(Olympiad, OlympiadAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Exam)
admin.site.register(Answer)
admin.site.register(ScoreSheet)

# Register your models here.
