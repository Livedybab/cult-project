from django import forms
from .models import Profile, Photo, Interest, Value, CharacterTrait

class OnboardingStep1Form(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['age', 'gender', 'city']
        widgets = {
            'age': forms.NumberInput(attrs={'placeholder': 'Ваш возраст'}),
            'gender': forms.Select(choices=Profile._meta.get_field('gender').choices),
            'city': forms.TextInput(attrs={'placeholder': 'Город проживания'}),
        }

class OnboardingStep2Form(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['looking_for', 'bio']
        widgets = {
            'looking_for': forms.Select(choices=Profile._meta.get_field('looking_for').choices),
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Расскажите о себе...'}),
        }

class OnboardingStep3Form(forms.ModelForm):
    interests = forms.ModelMultipleChoiceField(queryset=Interest.objects.all(), widget=forms.CheckboxSelectMultiple, required=False)
    values = forms.ModelMultipleChoiceField(queryset=Value.objects.all(), widget=forms.CheckboxSelectMultiple, required=False)

    class Meta:
        model = Profile
        fields = ['interests', 'values']

class OnboardingStep4Form(forms.ModelForm):
    character_traits = forms.ModelMultipleChoiceField(queryset=CharacterTrait.objects.all(), widget=forms.CheckboxSelectMultiple, required=False)

    class Meta:
        model = Profile
        fields = ['character_traits']

class ProfileForm(forms.ModelForm):
    interests = forms.ModelMultipleChoiceField(queryset=Interest.objects.all(), widget=forms.SelectMultiple(attrs={'class': 'form-control'}), required=False)
    values = forms.ModelMultipleChoiceField(queryset=Value.objects.all(), widget=forms.SelectMultiple(attrs={'class': 'form-control'}), required=False)
    character_traits = forms.ModelMultipleChoiceField(queryset=CharacterTrait.objects.all(), widget=forms.SelectMultiple(attrs={'class': 'form-control'}), required=False)

    class Meta:
        model = Profile
        fields = ['avatar', 'age', 'gender', 'city', 'bio', 'looking_for', 'interests', 'values', 'character_traits']

class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ['image', 'caption']