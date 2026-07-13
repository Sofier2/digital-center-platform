from django import forms

from .models import Profile, Submission


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def clean(self, data, initial=None):
        single_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_clean(item, initial) for item in data]
        return [single_clean(data, initial)] if data else []


class SubmissionForm(forms.ModelForm):
    extra_files = MultipleFileField(
        label="Файли, скріни або відео",
        required=False,
        widget=MultipleFileInput(attrs={"multiple": True}),
    )
    extra_links = forms.CharField(
        label="Посилання на відео, скріни або матеріали",
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "Кожне посилання з нового рядка: YouTube, Google Drive, GitHub, Figma тощо.",
            }
        ),
    )

    class Meta:
        model = Submission
        fields = ["answer", "file"]
        widgets = {
            "answer": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Коротко опиши виконану роботу або залиш посилання на GitHub/Google Drive.",
                }
            ),
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["avatar", "learning_goal"]
        widgets = {
            "learning_goal": forms.TextInput(
                attrs={
                    "placeholder": "Наприклад: підтягнути speaking або здати перший сайт",
                    "maxlength": 180,
                }
            ),
        }


class ReviewSubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ["points", "teacher_comment"]
        widgets = {
            "points": forms.NumberInput(attrs={"min": 0, "placeholder": "Наприклад, 95"}),
            "teacher_comment": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Що вийшло добре, що поправити, наступний крок.",
                }
            ),
        }


class QuizTakeForm(forms.Form):
    def __init__(self, *args, questions=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.questions = list(questions or [])
        for question in self.questions:
            choices = [(choice.id, choice.text) for choice in question.choices.all()]
            self.fields[f"question_{question.id}"] = forms.ChoiceField(
                label=question.text,
                choices=choices,
                widget=forms.RadioSelect,
                required=True,
            )
