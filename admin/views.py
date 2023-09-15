from django.shortcuts import render

from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent


def index(request):
    context = {}
    return render(request, BASE_DIR / 'templates/admin/home.html', context)
