from django.db import migrations

def update_user_email(apps, schema_editor):
    # Get the User model (as it was at the time of this migration)
    User = apps.get_model('core', 'User')
    
    # Try to find the user
    try:
        user = User.objects.get(username='testuser20')
        user.email = 'test20@gmail.com'
        user.save()
        print(f"Email successfully updated for user: {user.username}")
    except User.DoesNotExist:
        print("User 'testuser20' not found!")

def reverse_update(apps, schema_editor):
    # This is the reverse migration - we can't know what the original email was
    # so we just log that this operation happened
    print("Reverse migration executed, but original email not restored.")

class Migration(migrations.Migration):

    dependencies = [
        # You need to replace 'yourapp' with your actual app name
        # and 'xxxx_previous_migration' with the name of the last migration
        ('core', '0014_alter_user_email'),
    ]

    operations = [
        migrations.RunPython(update_user_email, reverse_update),
    ]