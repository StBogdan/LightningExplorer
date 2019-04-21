import os
import django
"""
What: Check that required config is in place for startup
Why: Lots of pieces to put together, check for each install
"""

def check_environment():
    env_vars = os.environ
    has_required = True
    required_config = ["LNDMON_django_user", "LNDMON_django_pass", "LNDMON_django_config", "LNDMON_django_secret_key"]
    for value in required_config:
        if value not in env_vars:
            print(f"[Setup] Error, missing required env var {value}")
            has_required = False

    return has_required


if __name__ == '__main__':
    good_to_go = True

    print("[Setup] Checking project requirements")

    if not check_environment():
        print("[Setup][Error] Missing env vars")
        good_to_go = False

    # Django setup (run in the virtual environment)
    print("[Setup] Attempting django setup")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lightningExplorer.settings")
    django.setup()

    print(f"[Setup] Are you good to start ? {good_to_go}")
