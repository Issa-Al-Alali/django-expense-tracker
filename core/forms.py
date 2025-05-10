from django import forms
import os

class RegistrationForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        if self.cleaned_data.get('password') != self.cleaned_data.get('confirm_password'):
            raise forms.ValidationError("Passwords don't match")
        return self.cleaned_data

class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

class ProfilePictureForm(forms.Form):
    profile_picture = forms.ImageField(
        label='Profile Picture',
        widget=forms.FileInput(attrs={'accept': 'image/*'}),
    )
    
    def clean_profile_picture(self):
        profile_picture = self.cleaned_data.get('profile_picture')
        if profile_picture:
            # Check file extension
            ext = os.path.splitext(profile_picture.name)[1].lower()
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            
            if ext not in valid_extensions:
                raise forms.ValidationError("Only JPEG, PNG, and GIF files are allowed.")
                
            # Limit file size (e.g., 5MB)
            if profile_picture.size > 5 * 1024 * 1024:  # 5MB in bytes
                raise forms.ValidationError("File size must be no more than 5MB.")
                
        return profile_picture