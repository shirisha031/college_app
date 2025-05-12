from django.urls import path
from . import views
# from .views import send_whatsapp_message_view


urlpatterns = [
    path('login/', views.custom_login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.custom_login_view, name='login'),  # Redirect root path to login
     path('student-data/', views.student_data_view, name='student_data_view'),
        # path('send-message/', views.send_whatsapp_message_view, name='send_message'),  # Correct function name
    # path('send-whatsapp-message/', send_whatsapp_message_view, name='send_whatsapp_message'),
    # path('incoming-whatsapp/', views.incoming_whatsapp, name='incoming_whatsapp'), 
      path('messages/', views.compose_message, name='compose_message'),
       path('message-history/', views.message_history_view, name='message_history_view'),
]
