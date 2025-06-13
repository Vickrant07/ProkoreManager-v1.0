from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    '''
    A custom user creation form that extends UserCreationForm to include additional fields
    '''
    username = forms.CharField(max_length=150, required=True, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.')
    email = forms.EmailField(required=True, help_text='Required. Enter a valid email address.')
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=150, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name') # Specify all fields here

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Reorder fields to your desired order
        self.fields = {
            'email': self.fields['email'],
            'first_name': self.fields['first_name'],
            'last_name': self.fields['last_name'],
            'username': self.fields['username'],
            'password1': self.fields['password1'], # This field comes from UserCreationForm
            'password2': self.fields['password2'], # This field also comes from UserCreationForm
        }
        # You can also re-label if needed, e.g.:
        self.fields['email'].label = "Your Email address Please"
        self.fields['first_name'].label = "Your First name"
        self.fields['last_name'].label = "Your Last name"
        self.fields['username'].label = "Your Username"

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user
    

class EmailLoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(widget=forms.PasswordInput)