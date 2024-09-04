from django.urls import path

from importer import views as importer_views

urlpatterns = [
    path('', importer_views.index, name='index'),
]
