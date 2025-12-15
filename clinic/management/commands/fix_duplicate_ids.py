from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import connection


class Command(BaseCommand):
    help = 'Fix duplicate user IDs by reassigning unique IDs'

    def handle(self, *args, **options):
        # Get all users ordered by date
        users = list(User.objects.all().order_by('date_joined'))
        
        self.stdout.write(f'Found {len(users)} users')
        
        # Show current state
        self.stdout.write('\nCurrent users:')
        for user in users:
            self.stdout.write(f'  ID: {user.id}, Username: {user.username}, Created: {user.date_joined}')
        
        # Get the next safe ID
        with connection.cursor() as cursor:
            cursor.execute("SELECT MAX(id) FROM auth_user")
            max_id = cursor.fetchone()[0] or 0
        
        next_id = max_id + 1
        self.stdout.write(f'\nStarting reassignment from ID {next_id}')
        
        # Reassign IDs to duplicates
        seen_ids = set()
        for user in users:
            if user.id in seen_ids:
                old_id = user.id
                # Update the user with a new ID directly in SQL
                with connection.cursor() as cursor:
                    # Update auth_user
                    cursor.execute(
                        "UPDATE auth_user SET id = %s WHERE id = %s AND username = %s",
                        [next_id, old_id, user.username]
                    )
                    # Update clinic_owner if exists
                    cursor.execute(
                        "UPDATE clinic_owner SET user_id = %s WHERE user_id = %s",
                        [next_id, old_id]
                    )
                
                self.stdout.write(self.style.SUCCESS(
                    f'  Reassigned {user.username} from ID {old_id} to ID {next_id}'
                ))
                next_id += 1
            else:
                seen_ids.add(user.id)
        
        # Update the sequence
        with connection.cursor() as cursor:
            cursor.execute("SELECT setval('auth_user_id_seq', (SELECT MAX(id) FROM auth_user))")
        
        self.stdout.write(self.style.SUCCESS('\nFixed! Showing updated users:'))
        for user in User.objects.all().order_by('id'):
            self.stdout.write(f'  ID: {user.id}, Username: {user.username}')
