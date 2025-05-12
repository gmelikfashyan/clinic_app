from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django import forms

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):

    birth_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True,
        label='Дата рождения'
    )
    phone = forms.CharField(
        max_length=12,
        required=True,
        label='Телефон'
    )
    
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 
                 'birth_date', 'gender', 'phone')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'PATIENT'
        
        if commit:
            user.save()
        
        return user