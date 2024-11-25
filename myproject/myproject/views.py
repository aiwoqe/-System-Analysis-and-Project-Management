from django.http import HttpResponse

def home(request):
    return HttpResponse("欢迎来到主页")