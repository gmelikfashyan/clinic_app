
from django.contrib import admin
from users.forms import CustomUserCreationForm
from django.views.generic.edit import CreateView

from django.urls import include, path, reverse_lazy
from django.conf import settings


urlpatterns = [
    # Админ-панель
    path('admin/', admin.site.urls),
    
    path('auth/', include('django.contrib.auth.urls')),

    path('', include('clinic.urls')),
    
    # Аутентификация (встроенная в Django)
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Приложение поликлиники
    path('clinic/', include('clinic.urls')),

    path(
        'auth/registration/', 
        CreateView.as_view(
            template_name='registration/registration_form.html',
            form_class=CustomUserCreationForm,
            success_url=reverse_lazy('clinic:home'),
        ),
        name='registration',
    ),
    
]