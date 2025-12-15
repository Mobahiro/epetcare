from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.models import Count


class Command(BaseCommand):
    help = 'Remove duplicate users keeping only the first created'

    def handle(self, *args, **options):
        # Find usernames with multiple users
        duplicates = User.objects.values('username').annotate(
            count=Count('id')
        ).filter(count__gt=1)

        if not duplicates:
            self.stdout.write(self.style.SUCCESS('No duplicate users found!'))
            return

        self.stdout.write(f'Found {len(duplicates)} duplicate usernames')
        
        total_deleted = 0
        for dup in duplicates:
            username = dup['username']
            users = User.objects.filter(username=username).order_by('id')
            self.stdout.write(f"\nUsername: {username} has {users.count()} records")
            
            # Keep the first, delete the rest
            first_user = users.first()
            duplicates_to_delete = users.exclude(id=first_user.id)
            
            for user in duplicates_to_delete:
                self.stdout.write(f"  Deleting user ID {user.id} (created: {user.date_joined})")
                user.delete()
                total_deleted += 1
        
        self.stdout.write(self.style.SUCCESS(f'\nDeleted {total_deleted} duplicate users!'))
