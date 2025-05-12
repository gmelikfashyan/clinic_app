from django.urls import path
from clinic.views import (
    SpecializationListView,
    DoctorListView,
    DateSelectionView,
    TimeSlotSelectionView,
    CreateAppointmentView,
    HomeView,
    PatientAppointmentListView,
    DoctorDashboardView,
    AppointmentDetailView,
    MedicalReportCreateView,
    CompleteAppointmentView,
    MedicalReportDetailView,
)

app_name = 'clinic'

urlpatterns = [
    # Пошаговая запись
    path('', HomeView.as_view(), name='home'),
    path('patient/book/', SpecializationListView.as_view(), name='book_appointment_start'),
    path('patient/book/specialization/<int:specialization_id>/', DoctorListView.as_view(), name='choose_doctor'),
    path('patient/book/doctor/<int:doctor_id>/', DateSelectionView.as_view(), name='choose_date'),
    path('patient/book/doctor/<int:doctor_id>/<str:date>/', TimeSlotSelectionView.as_view(), name='choose_timeslot'),
    path('patient/book/create/', CreateAppointmentView.as_view(), name='create_appointment'),
    path('patient/appointments/', PatientAppointmentListView.as_view(), name='patient_appointments'),
    path('doctor/dashboard/', DoctorDashboardView.as_view(), name='doctor_dashboard'),
    path('appointments/<int:pk>/', AppointmentDetailView.as_view(), name='appointment_detail'),
    path('appointments/<int:pk>/report/', MedicalReportCreateView.as_view(), name='create_report'),
    path('report/<int:report_pk>/', MedicalReportDetailView.as_view(), name='detail_report'),
    path('appointments/<int:pk>/complete/', CompleteAppointmentView.as_view(), name='complete_appointment'),
]