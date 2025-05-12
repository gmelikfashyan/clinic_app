# clinic/views/patient.py
from django.views.generic import ListView, TemplateView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from clinic.models import Specialization
from clinic.models import Doctor
from django.utils import timezone
from clinic.models import Schedule, Report
from django.shortcuts import get_object_or_404
from clinic.models import TimeSlot, Appointment
from django.views import View
from django.http import JsonResponse
from django.db.models import Q
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model

class SpecializationListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Specialization
    template_name = 'clinic/patient/choose_specialization.html'
    context_object_name = 'specializations'

    def test_func(self):
        return self.request.user.is_patient
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        blocked_specializations = set(
            Appointment.objects.filter(
                patient=self.request.user.patient_profile,
                status = 'BOOKED',
            ).values_list('doctor__specialization_id', flat=True)
        )
        context['blocked_specializations'] = blocked_specializations
        return context
    
    
    

class HomeView(TemplateView):
    template_name = 'clinic/home.html'
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'Melik1234')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['clinic_name'] = "Поликлиника 'Здоровье'"
        context['year_founded'] = 1995
        return context
    
class DoctorListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Doctor
    template_name = 'clinic/patient/choose_doctor.html'
    context_object_name = 'doctors'

    def test_func(self):
        return self.request.user.is_patient

    def get_queryset(self):
        specialization_id = self.kwargs['specialization_id']
        return Doctor.objects.filter(
            specialization_id=specialization_id
        ).select_related('user')


class DateSelectionView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'clinic/patient/choose_date.html'

    def test_func(self):
        return self.request.user.is_patient

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctor_id = self.kwargs['doctor_id']
        doctor = get_object_or_404(Doctor, pk=doctor_id)
        
        # Получаем доступные даты (например, на 2 недели вперёд)
        today = timezone.now().date()
        date_range = [today + timezone.timedelta(days=i) for i in range(14)]
        
        context['doctor'] = doctor
        context['date_range'] = date_range
        return context

class TimeSlotSelectionView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'clinic/patient/choose_timeslot.html'

    def test_func(self):
        return self.request.user.is_patient

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctor_id = self.kwargs['doctor_id']
        selected_date = self.kwargs['date']
        
        time_slots = TimeSlot.objects.filter(
            schedule__doctor_id=doctor_id,
            start_time__date=selected_date,
            is_available=True
        ).order_by('start_time')
        
        context['time_slots'] = time_slots
        context['selected_date'] = selected_date
        return context

class CreateAppointmentView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_patient

    def post(self, request, *args, **kwargs):
        time_slot_id = request.POST.get('time_slot_id')
        time_slot = get_object_or_404(TimeSlot, pk=time_slot_id, is_available=True)
        
        # Создаём запись
        appointment = Appointment.objects.create(
            patient=request.user.patient_profile,
            doctor=time_slot.schedule.doctor,
            time_slot=time_slot,
            date=time_slot.start_time.date()
        )
        
        # Помечаем слот как занятый
        time_slot.is_available = False
        time_slot.save()
        
        return JsonResponse({'status': 'success', 'appointment_id': appointment.id})
    
class PatientAppointmentListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Appointment
    template_name = 'clinic/patient/patient_appointments.html'
    context_object_name = 'appointments'

    def test_func(self):
        return self.request.user.is_patient

    def get_queryset(self):
        now = timezone.now()
        current_date = now.date()
        current_time = now.time()

        return Appointment.objects.filter(
            Q(patient=self.request.user.patient_profile),
            Q(time_slot__start_time__date__gt=current_date) |
            Q(
                time_slot__start_time__date=current_date,
                time_slot__start_time__time__gte=current_time
            )
        ).select_related(
            'time_slot',
            'doctor',
            'doctor__user'
        ).order_by('time_slot__start_time')
    

class DoctorDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'clinic/doctor/doctor_dashboard.html'
    
    def test_func(self):
        return self.request.user.is_doctor()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        doctor = self.request.user.doctor_profile
        
        appointments = Appointment.objects.filter(doctor=doctor)
        for appointment in appointments:
            appointment.update_status()
        
        context['doctor'] = doctor
        context['today_appointments'] = Appointment.objects.filter(
            doctor=doctor,
            date=today,
            status='BOOKED'
        ).order_by('date')
        
        return context
    
class AppointmentDetailView(LoginRequiredMixin, DetailView):
    model = Appointment
    template_name = 'clinic/appointment_detail.html'
    context_object_name = 'appointment'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_doctor'] = self.request.user.is_doctor()
        context['is_patient'] = self.request.user.is_patient()
        return context

class MedicalReportCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Report
    fields = ['symptoms', 'treatment', 'diagnosis', 'notes']
    template_name = 'clinic/medical_report_form.html'
    
    def test_func(self):
        return self.request.user.is_doctor()
    
    def get_appointment(self):
        return Appointment.objects.get(pk=self.kwargs['pk'])
    
    def form_valid(self, form):
        form.instance.appointment = self.get_appointment()
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('clinic:appointment_detail', kwargs={'pk': self.get_appointment().pk})

class CompleteAppointmentView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Appointment
    fields = []
    template_name = 'clinic/appointment_detail.html'
    
    def test_func(self):
        return self.request.user.is_doctor()
    
    def form_valid(self, form):
        form.instance.status = 'COMPLETED'
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('clinic:appointment_detail', kwargs={'pk': self.object.pk})
    
class MedicalReportDetailView(LoginRequiredMixin, DetailView):
    model = Report
    template_name = 'clinic/report_detail.html'
    context_object_name = 'report'
    pk_url_kwarg = 'report_pk'
    
    def get_object(self, queryset=None):
        return get_object_or_404(Report, pk=self.kwargs.get(self.pk_url_kwarg))

    
