from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'nodes'
urlpatterns = [
    path('', views.index, name='index'),
    path('index', views.index, name='index'),
    path('visualiser', views.visualiser, name='visualiser'),
    path('nodes', views.nodes, name='nodes'),
    path('channels', views.channels, name='channels'),
    path('metrics', views.metrics, name='metrics'),
    path('search', views.search, name='search'),
    path('about', views.about, name='about'),
    path('nodes/<slug:nodePubKey>/<int:date_logged>', views.nodes_detail, name='node-detail'),
    path('channels/<slug:chanID>/<int:date_logged>', views.channels_detail, name='channel-detail'),
    path('nodes/<slug:nodePubKey>', views.nodes_detail, name='node-detail'),
    path('channels/<slug:chanID>', views.channels_detail, name='channel-detail'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
