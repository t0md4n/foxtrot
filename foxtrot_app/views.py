from django.shortcuts import render

def dashboard(request):
    return render(request, "dashboard.html")

def mailchimp(request):
    return render(request, "mailchimp.html")

def sharepoint(request):
    return render(request, "sharepoint.html")

def excel_upload(request):
    return render(request, "excel_upload.html")

def result(request):
    return render(request, "result.html")

def login_view(request):
    return render(request, "login.html")
