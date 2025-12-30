"""
Management command to approve existing veterinarians
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from vet.models import Veterinarian


class Command(BaseCommand):
    help = 'Approve all existing veterinarians that are in pending status'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Approve all pending vets without confirmation',
        )

    def handle(self, *args, **options):
        pending_vets = Veterinarian.objects.filter(
            approval_status=Veterinarian.ApprovalStatus.PENDING
        )
        
        count = pending_vets.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No pending veterinarians found.'))
            return
        
        self.stdout.write(f'Found {count} pending veterinarian(s):')
        for vet in pending_vets:
            self.stdout.write(f'  - {vet.full_name} ({vet.user.username})')
        
        if not options['all']:
            confirm = input('\nApprove all pending veterinarians? (yes/no): ')
            if confirm.lower() not in ['yes', 'y']:
                self.stdout.write(self.style.WARNING('Operation cancelled.'))
                return
        
        # Approve all pending vets
        pending_vets.update(
            approval_status=Veterinarian.ApprovalStatus.APPROVED,
            approved_at=timezone.now()
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully approved {count} veterinarian(s).'
            )
        )
