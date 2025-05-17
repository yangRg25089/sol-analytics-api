import django.db.models.deletion
from django.db import migrations, models


def set_user_type_and_email(apps, schema_editor):
    User = apps.get_model("core", "User")
    for user in User.objects.all():
        if user.google_id:
            user.user_type = "google"
        else:
            user.user_type = "admin"
            if not user.email:
                user.email = f"admin_{user.id}@example.com"
        user.save()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_alter_user_google_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="user_type",
            field=models.CharField(
                choices=[("admin", "Admin User"), ("google", "Google User")],
                default="google",
                max_length=10,
            ),
        ),
        migrations.RunPython(set_user_type_and_email),
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.EmailField(
                blank=False, db_index=True, max_length=254, null=False, unique=True
            ),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(("user_type", "google"), ("google_id__isnull", False)),
                    models.Q(("user_type", "admin"), ("google_id__isnull", True)),
                    _connector="OR",
                ),
                name="valid_user_type_constraint",
            ),
        ),
        migrations.AlterModelOptions(
            name="user",
            options={},
        ),
    ]
