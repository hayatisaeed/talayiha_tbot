import openpyxl
from django.http import HttpResponse


def export_to_excel(modeladmin, request, queryset):
    # Create a workbook and worksheet
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = 'Users'

    # Define headers for the Excel file
    headers = ['ID', 'Full Name', 'First Name', 'Last Name', 'National ID', 'Phone Number', 'Chat ID', 'City',
               'School Name']
    sheet.append(headers)

    # Add user data to rows
    for profile in queryset:
        sheet.append([
            profile.id,
            profile.fullname,
            profile.first_name,
            profile.last_name,
            profile.national_id,
            profile.phone_number,
            profile.chat_id,
            profile.city,
            profile.school_name,
        ])

    # Prepare the response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename=users.xlsx'

    # Save the workbook to the response
    workbook.save(response)
    return response
