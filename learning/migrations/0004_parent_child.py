from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("learning", "0003_material_submission_attachments"),
    ]

    operations = [
        migrations.CreateModel(
            name="ParentChild",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("note", models.CharField(blank=True, max_length=160, verbose_name="примітка")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="створено")),
                ("child", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="parent_links", to=settings.AUTH_USER_MODEL, verbose_name="дитина")),
                ("parent", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="child_links", to=settings.AUTH_USER_MODEL, verbose_name="батьки")),
            ],
            options={
                "verbose_name": "зв'язок батьки-дитина",
                "verbose_name_plural": "зв'язки батьків і дітей",
                "unique_together": {("parent", "child")},
            },
        ),
    ]
