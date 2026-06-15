from django import forms

from .models import Submission


class SubmissionForm(forms.ModelForm):
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
