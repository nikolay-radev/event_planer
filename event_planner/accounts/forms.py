from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.hashers import make_password
from event_planner.accounts.models import Profile

CustomUser = get_user_model()  # This retrieves the CustomUser model


class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'}),
        label="Password"
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm your password'}),
        label="Confirm Password"
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password']

    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords do not match")
        return password_confirm

    def save(self, commit=True):
        user = super().save(commit=False)
        user.password = make_password(self.cleaned_data['password'])  # Hash the password
        if commit:
            user.save()
        return user


class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        label="Username"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        label="Password"
    )


User = get_user_model()


class ProfileForm(forms.ModelForm):
    email = forms.EmailField(required=True, label="Email")  # Add email field for update

    class Meta:
        model = Profile
        fields = ['profile_picture', 'email', 'first_name', 'last_name', 'address', 'phone_number',]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Accept the user instance
        super().__init__(*args, **kwargs)
        if user:
            self.user = user
            self.fields['email'].initial = user.email  # Prepopulate the email with the current email of the user
            self.fields['profile_picture'].widget.attrs.update({
                'class': 'form-control'
            })

            profile_picture = forms.ImageField(
                required=False,
                widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
                label='Change Profile Picture'
            )

    def clean_email(self):
        """Ensure the email is unique."""
        email = self.cleaned_data['email']
        existing_user = User.objects.filter(email=email).exclude(pk=self.user.pk).first()
        if existing_user:
            raise forms.ValidationError("This email is already in use by another account.")
        return email

    def save(self, commit=True):
        """Save the profile and update the user's email."""
        profile = super().save(commit=False)
        if commit:
            profile.save()
            # Update the user's email
            self.user.email = self.cleaned_data['email']
            self.user.save()
        return profile
