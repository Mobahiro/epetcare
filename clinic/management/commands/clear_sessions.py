from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session


class Command(BaseCommand):
    help = 'Clear all sessions and show user statistics'

    def handle(self, *args, **options):
        # Show user statistics
        total_users = User.objects.count()
        self.stdout.write(f'Total users: {total_users}')
        
        # Show all users
        self.stdout.write('\nAll users:')
        for user in User.objects.all().order_by('id'):
            self.stdout.write(f'  ID: {user.id}, Username: {user.username}, Email: {user.email}, Created: {user.date_joined}')
        
        # Check for duplicate IDs (shouldn't be possible but let's verify)
        from django.db.models import Count
        duplicate_ids = User.objects.values('id').annotate(count=Count('id')).filter(count__gt=1)
        if duplicate_ids:
            self.stdout.write(self.style.ERROR(f'\nERROR: Found {len(duplicate_ids)} duplicate IDs (database corruption!)'))
        
        # Check for duplicate usernames
        duplicate_usernames = User.objects.values('username').annotate(count=Count('id')).filter(count__gt=1)
        if duplicate_usernames:
            self.stdout.write(self.style.WARNING(f'\nFound {len(duplicate_usernames)} duplicate usernames:'))
            for dup in duplicate_usernames:
                users = User.objects.filter(username=dup['username'])
                self.stdout.write(f'  Username "{dup["username"]}" has {users.count()} records:')
                for u in users:
                    self.stdout.write(f'    - ID: {u.id}, Email: {u.email}, Created: {u.date_joined}')
        
        # Clear all sessions
        session_count = Session.objects.count()
        Session.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'\nCleared {session_count} sessions. All users must log in again.'))
