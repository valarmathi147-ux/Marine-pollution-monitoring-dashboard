from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('analysis/', views.analysis_view, name='analysis'),
    path('report/', views.search_filter_view, name='report'),
    path('download_csv/', views.generate_report_view, name='download'),
]
