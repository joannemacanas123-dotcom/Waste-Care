from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth.forms import UserCreationForm
from .models import Appointment, User, Feedback, JournalEntry


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["waste_type", "address", "latitude", "longitude", "preferred_date", "preferred_time", "priority", "estimated_weight", "notes", "special_instructions"]
        widgets = {
            'waste_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
                'placeholder': ' '
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': ' ',
                'required': True
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': ' ',
                'step': '0.000001',
                'min': '-90',
                'max': '90'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': ' ',
                'step': '0.000001',
                'min': '-180',
                'max': '180'
            }),
            'preferred_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'min': timezone.now().date().isoformat(),
                'placeholder': ' '
            }),
            'preferred_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
                'placeholder': ' '
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': ' '
            }),
            'estimated_weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': ' ',
                'min': '0',
                'step': '0.1'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': ' '
            }),
            'special_instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': ' '
            })
        }
        labels = {
            'waste_type': 'Waste Type',
            'address': 'Pickup Address',
            'latitude': 'Latitude (Optional)',
            'longitude': 'Longitude (Optional)',
            'preferred_date': 'Preferred Date',
            'preferred_time': 'Preferred Time',
            'priority': 'Priority Level',
            'estimated_weight': 'Estimated Weight (kg)',
            'notes': 'Additional Notes',
            'special_instructions': 'Special Instructions'
        }
        help_texts = {
            'latitude': 'Latitude for Almeria, Biliran (range: 11.58 to 11.71)',
            'longitude': 'Longitude for Almeria, Biliran (range: 124.32 to 124.47)'
        }
    
    def clean_preferred_date(self):
        date = self.cleaned_data.get('preferred_date')
        if date and date < timezone.now().date():
            raise ValidationError("Pickup date cannot be in the past.")
        if date and date > timezone.now().date() + timedelta(days=30):
            raise ValidationError("Pickup date cannot be more than 30 days in advance.")
        return date
    
    def clean_address(self):
        address = self.cleaned_data.get('address')
        if address and len(address.strip()) < 10:
            raise ValidationError("Please provide a complete address with at least 10 characters.")
        return address.strip() if address else address


class AppointmentStatusForm(forms.ModelForm):
    handled_by = forms.ModelChoiceField(
        queryset=User.objects.filter(role__in=['staff', 'admin']),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Select staff member"
    )

    class Meta:
        model = Appointment
        fields = ["status", "handled_by", "notes"]
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Staff notes (optional)'
            })
        }


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Share your feedback about our service...',
                'required': True
            })
        }
        labels = {
            'message': 'Your Feedback'
        }
    
    def clean_message(self):
        message = self.cleaned_data.get('message')
        if message and len(message.strip()) < 10:
            raise ValidationError("Please provide more detailed feedback (at least 10 characters).")
        return message.strip() if message else message


class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter journal title',
                'required': True
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Write your journal entry...',
                'required': True
            })
        }
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if title and len(title.strip()) < 3:
            raise ValidationError("Title must be at least 3 characters long.")
        return title.strip() if title else title
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if content and len(content.strip()) < 20:
            raise ValidationError("Journal content must be at least 20 characters long.")
        return content.strip() if content else content


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email Address'
            })
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("This email address is already in use.")
        return email


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'required': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'required': True
        })
    )


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'required': True
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Password',
            'required': True
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'role')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email Address',
                'required': True
            }),
            'role': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            })
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords do not match.")
        return password2

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError("This email address is already registered.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


