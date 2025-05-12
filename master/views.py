from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages

def custom_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'master/login.html', {'error': 'Invalid credentials'})
    return render(request, 'master/login.html')

@login_required
def dashboard_view(request):
    return render(request, 'master/dashboard.html')

def logout_view(request):
    logout(request)
    return redirect('login')
from django.shortcuts import render, redirect
from .forms import ExcelUploadForm
from .models import ExcelUpload, StudentRecord
import pandas as pd
import os
def student_data_view(request):
    upload_form = ExcelUploadForm()
    files = ExcelUpload.objects.order_by('-uploaded_at')
    table_data = []

    # ✅ Handle file upload
    if request.method == 'POST' and 'upload_submit' in request.POST:
        upload_form = ExcelUploadForm(request.POST, request.FILES)
        if upload_form.is_valid():
            upload_form.save()
            return redirect('student_data_view')

    # ✅ Combine and read all Excel files
    all_files = ExcelUpload.objects.all()
    combined_df = pd.DataFrame()

    for file_obj in all_files:
        try:
            file_path = file_obj.file.path
            file_ext = os.path.splitext(file_path)[1].lower()

            if file_ext == '.csv':
                df = pd.read_csv(file_path)
            elif file_ext == '.xlsx':
                df = pd.read_excel(file_path, engine='openpyxl')
            else:
                continue  # skip unknown types

            combined_df = pd.concat([combined_df, df], ignore_index=True)

        except Exception as e:
            print(f"Error reading file {file_path}: {e}")

    # ✅ Drop duplicates within Excel file data
    if not combined_df.empty:
        combined_df.drop_duplicates(subset=['Student ID', 'Student Name'], inplace=True)

        # ✅ Avoid inserting already saved DB records
        existing_records = StudentRecord.objects.values_list('student_id', 'student_name')
        existing_set = set((str(i).strip(), n.strip().lower()) for i, n in existing_records)

        for _, row in combined_df.iterrows():
            student_id = str(row.get('Student ID', '')).strip()
            student_name = str(row.get('Student Name', '')).strip().lower()

            if (student_id, student_name) not in existing_set:
                StudentRecord.objects.create(
                    student_id=student_id,
                    student_name=row.get('Student Name', ''),
                    guardian_name=row.get('Guardian Name', ''),
                    guardian_phone=row.get('Guardian Phone Number', ''),
                    guardian_relation=row.get('Guardian Relation with Student', ''),
                    department=row.get('Department', '')
                )
                existing_set.add((student_id, student_name))  # avoid re-saving in loop

    # ✅ Always show saved records from DB
    saved_records = StudentRecord.objects.all().values(
        'student_id', 'student_name', 'guardian_name',
        'guardian_phone', 'guardian_relation', 'department'
    )
    table_data = list(saved_records)

    return render(request, 'master/student_form.html', {
        'upload_form': upload_form,
        'files': files,
        'table_data': table_data
    })
# from .models import SentMessage, StudentRecord
# from django.contrib import messages
# from .models import SentMessage, StudentRecord

# def compose_message(request):
#     # Fetch unique departments
#     departments = StudentRecord.objects.values_list('department', flat=True).distinct()
#     departments = sorted(set(departments))

#     if request.method == 'POST':
#         # Get data from form
#         subject = request.POST.get('subject')
#         message = request.POST.get('message')
#         send_sms = 'sms' in request.POST
#         send_whatsapp = 'whatsapp' in request.POST
#         department = request.POST.get('department')

#         # Check if user selected "All" department
#         if department == "All":
#             # Save message for all departments
#             for dept in departments:
#                 SentMessage.objects.create(
#                     subject=subject,
#                     message=message,
#                     send_sms=send_sms,
#                     send_whatsapp=send_whatsapp,
#                     department=dept
#                 )
#         else:
#             # Save message for selected department
#             SentMessage.objects.create(
#                 subject=subject,
#                 message=message,
#                 send_sms=send_sms,
#                 send_whatsapp=send_whatsapp,
#                 department=department
#             )

#         # Add success message
#         messages.success(request, "Message sent successfully.")
        
#         # Redirect to the same page to show the success message
#         return redirect('compose_message')

#     return render(request, 'master/compose_message.html', {
#         'departments': departments
#     })


from .models import SentMessage, StudentRecord
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def message_history_view(request):
    channel_filter = request.GET.get('channel', '')
    status_filter = request.GET.get('status', '')
    department = request.GET.get('department')

    messages = SentMessage.objects.all().order_by('-sent_at')

    # Filter by channel
    if channel_filter == 'sms':
        messages = messages.filter(send_sms=True)
    elif channel_filter == 'whatsapp':
        messages = messages.filter(send_whatsapp=True)

    # Filter by status if provided
    if status_filter:
        messages = messages.filter(status=status_filter)
    if department:
        messages = messages.filter(department=department)

    # Assuming you have a static list of departments or from the DB
    departments = SentMessage.objects.values_list('department', flat=True).distinct()

    STATUS_DISPLAY = {
    'success': 'Delivered',
    'error': 'Failed',
    'pending': 'Pending',
}



    # Add guardian list (student name + guardian phone) for each message's department
    for msg in messages:
        students = StudentRecord.objects.filter(department=msg.department)
        msg.guardians = [{"student": s.student_name, "phone": s.guardian_phone} for s in students]
        status = (msg.status or "").lower()
        msg.status_display = STATUS_DISPLAY.get(status, msg.status.capitalize() if msg.status else "Unknown")

    return render(request, 'master/message_history.html', {
        'messages': messages,
        'channel_filter': channel_filter,
        'status_filter': status_filter,
        'department_filter': department,
        'departments': departments,
    })


from django.shortcuts import render
from .models import StudentRecord, SentMessage
from django.db.models import Count, Q
from datetime import timedelta
from django.utils import timezone

def dashboard_view(request):
    total_students = StudentRecord.objects.count()
    messages_sent = SentMessage.objects.count()
    active_departments = SentMessage.objects.values('department').distinct().count()

    # Calculate delivered messages
    delivered_messages = SentMessage.objects.filter(
        Q(send_sms=True) | Q(send_whatsapp=True)
    ).count()

    delivery_rate = round((delivered_messages / messages_sent) * 100, 2) if messages_sent > 0 else 0

    today = timezone.now()
    last_7_days = [(today - timedelta(days=i)).date() for i in range(6, -1, -1)]

    message_data = (
        SentMessage.objects
        .filter(sent_at__date__in=last_7_days)
        .values('sent_at__date')
        .annotate(count=Count('id'))
    )

    date_count_map = {entry['sent_at__date']: entry['count'] for entry in message_data}
    labels = [date.strftime("%Y-%m-%d") for date in last_7_days]
    counts = [date_count_map.get(date, 0) for date in last_7_days]

    # Annotate each recent message with is_delivered property
    recent_messages_qs = SentMessage.objects.order_by('-sent_at')[:5]
    recent_messages = []
    for msg in recent_messages_qs:
        msg.is_delivered = msg.send_sms or msg.send_whatsapp
        recent_messages.append(msg)

    context = {
        'total_students': total_students,
        'messages_sent': messages_sent,
        'active_departments': active_departments,
        'delivery_rate': delivery_rate,
        'labels': labels,
        'counts': counts,
        'recent_messages': recent_messages,
    }

    return render(request, 'master/dashboard.html', context)



from django.shortcuts import render, redirect
from django.contrib import messages
from .models import StudentRecord, SentMessage
from asgiref.sync import sync_to_async
import asyncio
from twilio.rest import Client
from django.conf import settings
from functools import partial

# Async Twilio sender with fixed parameter passing
async def send_twilio_message(to_number, body, send_sms, send_whatsapp):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    loop = asyncio.get_event_loop()

    try:
        if send_whatsapp:
            await loop.run_in_executor(
                None,
                partial(
                    client.messages.create,
                    body=body,
                    from_=f'whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}',
                    to=f'whatsapp:{to_number}'
                )
            )

        if send_sms:
            await loop.run_in_executor(
                None,
                partial(
                    client.messages.create,
                    body=body,
                    from_=settings.TWILIO_SMS_NUMBER,
                    to=to_number
                )
            )
        return True
    except Exception as e:
        print(f"❌ Error sending to {to_number}: {e}")
        return False

# Async ORM fetch based on department
@sync_to_async
def get_guardians_queryset(department):
    if department == "All":
        return list(StudentRecord.objects.all())
    return list(StudentRecord.objects.filter(department=department))

# Compose message view
def compose_message(request):
    departments = StudentRecord.objects.values_list('department', flat=True).distinct()
    departments = sorted(set(departments))
    selected_department = request.POST.get('department', '')

    if request.method == 'POST':
        subject = request.POST.get('subject')
        message_text = request.POST.get('message')
        send_sms = 'sms' in request.POST
        send_whatsapp = 'whatsapp' in request.POST
        department = request.POST.get('department')

        # Save message for record
        if department == "All":
            for dept in departments:
                SentMessage.objects.create(
                    subject=subject,
                    message=message_text,
                    send_sms=send_sms,
                    send_whatsapp=send_whatsapp,
                    department=dept
                )
        else:
            SentMessage.objects.create(
                subject=subject,
                message=message_text,
                send_sms=send_sms,
                send_whatsapp=send_whatsapp,
                department=department
            )  

        # Async send all messages
        async def send_all():
            guardians = await get_guardians_queryset(department)
            full_message = f"Subject: {subject}\n{message_text}"

            tasks = [
                send_twilio_message(f'+91{g.guardian_phone.strip()}', full_message, send_sms, send_whatsapp)
                for g in guardians
            ]
            results = await asyncio.gather(*tasks)

            # Logging results (optional)
            for i, success in enumerate(results):
                number = guardians[i].guardian_phone
                if not success:
                    print(f"❌ Failed to send to: +91{number}")
                else:
                    print(f"✅ Sent to: +91{number}")

            return results.count(False)

        # Run the async coroutine
        failed_count = asyncio.run(send_all())

        if failed_count == 0:
            messages.success(request, "✅ Message sent successfully to all guardians.")
        else:
            messages.warning(request, f"⚠️ Message sent with {failed_count} failures.")

        return redirect('compose_message')

    return render(request, 'master/compose_message.html', {
        'departments': departments,
        'selected_department': selected_department
    })
