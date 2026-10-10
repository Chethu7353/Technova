from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from google import genai
from google.genai import types

class Command(BaseCommand):
    help = 'Check that the configured Gemini model is available to the configured API key.'

    def handle(self, *args, **options):
        if not settings.GEMINI_API_KEY or not settings.GEMINI_MODEL:
            raise CommandError('GEMINI_API_KEY or GEMINI_MODEL is not configured.')
        client = genai.Client(api_key=settings.GEMINI_API_KEY, http_options=types.HttpOptions(timeout=15000))
        try:
            wanted = settings.GEMINI_MODEL.removeprefix('models/')
            available = False
            for model in client.models.list():
                name = (getattr(model, 'name', '') or '').removeprefix('models/')
                methods = getattr(model, 'supported_actions', None) or getattr(model, 'supported_generation_methods', None) or []
                if name == wanted and any('generatecontent' in str(method).replace('_','').lower() for method in methods):
                    available = True
                    break
            if not available:
                raise CommandError('Configured model is not listed with text generation support for this API key.')
            self.stdout.write(self.style.SUCCESS('Configured Gemini model is available for content generation.'))
        except CommandError:
            raise
        except Exception as exc:
            raise CommandError(f'Gemini model check failed ({type(exc).__name__}); credentials were not displayed.') from None
        finally:
            client.close()
