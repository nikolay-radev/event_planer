from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'event_planner.accounts'

    def ready(self):
        import event_planner.accounts.signals