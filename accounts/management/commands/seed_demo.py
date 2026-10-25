from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from accounts.rbac import ROLES


class Command(BaseCommand):
    help = 'Create the four CHRS role groups and one demo user per role (password from --password).'

    def add_arguments(self, parser):
        parser.add_argument('--password', default='ChangeMe!2026')
        parser.add_argument('--no-users', action='store_true', help='Only create the role groups')

    def handle(self, *args, **opts):
        for role in ROLES:
            Group.objects.get_or_create(name=role)
        if opts['no_users']:
            return self.stdout.write('Role groups ready.')
        for role in ROLES:
            u, created = User.objects.get_or_create(username=role.lower(), defaults={'first_name': role, 'is_staff': role == 'Admin'})
            if created:
                u.set_password(opts['password'])
                u.save()
            u.groups.set([Group.objects.get(name=role)])
        self.stdout.write(self.style.SUCCESS('Groups and demo users (admin, physician, nurse, counselor) ready.'))
