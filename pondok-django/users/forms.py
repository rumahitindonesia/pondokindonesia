from django import forms
from django.contrib.auth import get_user_model
from unfold.forms import UserCreationForm as UnfoldUserCreationForm, UserChangeForm as UnfoldUserChangeForm

User = get_user_model()

class UserCreationForm(UnfoldUserCreationForm):
    class Meta(UnfoldUserCreationForm.Meta):
        model = User
        fields = UnfoldUserCreationForm.Meta.fields + ('first_name', 'last_name', 'email', 'phone_number', 'role', 'tenant')

class UserChangeForm(UnfoldUserChangeForm):
    class Meta(UnfoldUserChangeForm.Meta):
        model = User
        fields = '__all__'
