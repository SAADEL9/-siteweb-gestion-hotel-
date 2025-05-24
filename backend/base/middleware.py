from django.shortcuts import redirect
from django.urls import reverse

class AdminDashboardRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Vérifier si l'utilisateur est connecté et accède à la page d'index de l'admin
        if (request.user.is_authenticated and 
            request.user.is_staff and 
            request.path == '/django-admin/'):
            return redirect('admin_dashboard')
            
        return response 