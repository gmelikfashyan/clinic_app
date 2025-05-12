from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta, datetime, time

class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Администратор'),
        ('DOCTOR', 'Доктор'),
        ('PATIENT', 'Пациент'),
    )

    GENDER_CHOICES = (
        ('Man', 'Мужчина'),
        ('Woman', 'Женщины')
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, verbose_name='Роль')
    birth_date = models.DateField(null=True, blank=True, verbose_name='Дата рождения')
    phone = models.CharField(max_length=12, blank=True, null=True, verbose_name='Телефон')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, verbose_name='Пол')

    def is_admin(self):
        return self.role == 'ADMIN'
    
    def is_patient(self):
        return self.role == 'PATIENT'
    
    def is_doctor(self):
        return self.role == 'DOCTOR'
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new and self.role == 'PATIENT':
            Patient.objects.get_or_create(user=self)

    
class Specialization(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название специализации')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Специализация'
        verbose_name_plural = 'Специализации'

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialization = models.ForeignKey(Specialization, default='-', on_delete=models.SET_DEFAULT, null=False, blank=False, verbose_name='Специализация')
    education = models.TextField(verbose_name='Образование')
    experience = models.PositiveIntegerField(verbose_name='Опыт работы (лет)')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    photo = models.ImageField(upload_to='doctors/', blank=True, null=True, verbose_name='Фото')

    def __str__(self):
        return f'{self.user.get_full_name()} ({self.specialization})'
    
    class Meta:
        verbose_name = 'Врач'
        verbose_name_plural = 'Врачи'



class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    insurance_number = models.CharField(max_length=50, blank=True, verbose_name='Номер страхового полиса')
    
    def __str__(self):
        return self.user.get_full_name()
    
    class Meta:
        verbose_name = 'Пациент'
        verbose_name_plural = 'Пациенты'

class Schedule(models.Model):
    DAYS_OF_WEEK = (
        (0, 'Понедельник'),
        (1, 'Вторник'),
        (2, 'Среда'),
        (3, 'Четверг'),
        (4, 'Пятница'),
        (5, 'Суббота'),
        (6, 'Воскресенье'),
    )
    
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='schedules', verbose_name='Доктор')
    day_of_week = models.PositiveSmallIntegerField(choices=DAYS_OF_WEEK, verbose_name='День недели')
    start_time = models.TimeField(verbose_name='Время начала приема')
    end_time = models.TimeField(verbose_name='Время окончания приема')
    slot_duration = models.TimeField(verbose_name='Продолжительность приема')
    is_working = models.BooleanField(default=True, verbose_name='Рабочий день')
    
    def __str__(self):
        return f"{self.doctor} - {self.get_day_of_week_display()}: {self.start_time}-{self.end_time}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_working:  # Создаем слоты только для рабочих дней
            self.create_time_slots()
    
    def create_time_slots(self):
        """Создает временные слоты на 4 недели вперед"""
        today = timezone.now().date()
        end_date = today + timedelta(weeks=4)

        
        # Получаем ближайшие даты для этого дня недели
        current_date = today
        delta = 7
        if current_date.weekday() != self.day_of_week:
            difference = 7 - abs(self.day_of_week - current_date.weekday())
            current_date += timedelta(days=difference)
        while current_date <= end_date:
            self.create_slots_for_date(current_date)
            current_date += timedelta(days=7)
    
    def create_slots_for_date(self, date):
        slot_duration = datetime.combine(date, self.slot_duration) - datetime.combine(date, time(0))
        current_time = datetime.combine(date, self.start_time)
        end_time = datetime.combine(date, self.end_time)
        
        while current_time + slot_duration <= end_time:
            TimeSlot.objects.create(
                schedule=self,
                start_time=current_time,
                is_available=True
            )
            current_time += slot_duration
    
    class Meta:
        verbose_name = 'Расписание'
        verbose_name_plural = 'Расписания'
        unique_together = ('doctor', 'day_of_week')


class TimeSlot(models.Model):
    """Временные слоты для записи"""
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='time_slots', verbose_name='Расписание')
    start_time = models.DateTimeField(verbose_name='Начало слота')
    is_available = models.BooleanField(default=True, verbose_name='Доступен для записи')
    
    def __str__(self):
        return f"{self.schedule.doctor} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        verbose_name = 'Временной слот'
        verbose_name_plural = 'Временные слоты'
        ordering = ['start_time']


class Appointment(models.Model):
    STATUS_CHOICES = (
        ('BOOKED', 'Забронировано'),
        ('COMPLETED', 'Завершено'),
        ('CANCELLED', 'Отменено'),
        ('NOSHOW', 'Пациент не пришел'),
    )
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')  # Прямая связь
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    date = models.DateField()  # Конкретная дата приёма
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='BOOKED')

    class Meta:
        unique_together = [('patient', 'time_slot')]  # Пациент не может записаться дважды в один слот

    def save(self, *args, **kwargs):
        if self.time_slot_id and not self.doctor_id:
            self.doctor = self.time_slot.schedule.doctor
        if not self.date and self.time_slot_id:
            self.date = self.time_slot.start_time.date()
        super().save(*args, **kwargs)

    def update_status(self):
        now = timezone.now()
        if self.status == 'BOOKED':
            start_time = self.time_slot.start_time.time() if hasattr(self.time_slot.start_time, 'time') else self.time_slot.start_time
            
            appointment_datetime = datetime.combine(
                self.date,
                start_time
            )
            appointment_datetime = timezone.make_aware(appointment_datetime)
        
            if now > appointment_datetime + timedelta(days=1):
                self.status = 'NOSHOW'
                self.save()


class Report(models.Model):
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE, verbose_name="Пациент")
    doctor = models.OneToOneField(Doctor, on_delete=models.CASCADE, verbose_name="Доктор")
    appointment = models.OneToOneField(Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='report', verbose_name='Запись на прием')
    date = models.DateField(auto_now_add=True, verbose_name='Дата приёма')
    symptoms = models.TextField(verbose_name='Симптомы')
    diagnosis = models.TextField(verbose_name='Диагноз')
    treatment = models.TextField(verbose_name='Лечение')
    notes = models.TextField(blank=True, verbose_name='Примечания')
    
    def __str__(self):
        return f"{self.patient} - {self.date}"
    
    def save(self, *args, **kwargs):
        if self.appointment and not self.date:
            self.date = self.appointment.date
            self.patient = self.appointment.patient
            self.doctor = self.appointment.doctor
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = 'Медицинское заключение'
        verbose_name_plural = 'Медицинские заключения'