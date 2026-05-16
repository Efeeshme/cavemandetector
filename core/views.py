from django.shortcuts import render

def home(request):
    return render(request, "core/home.html")


def privacy(request):
    from django.shortcuts import render
    return render(request, "core/privacy.html")

def terms(request):
    from django.shortcuts import render
    return render(request, "core/terms.html")
