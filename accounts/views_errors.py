from django.shortcuts import render


def forbidden(request, exception=None):
    return render(request, '403.html', status=403)
