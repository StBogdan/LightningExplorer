from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'nodes'
urlpatterns = [
    path('', views.index, name='index'),
    path('index', views.index, name='index'),
    path('nodes', views.nodes, name='nodes'),
    path('channels', views.channels, name='channels'),
    path('metrics', views.metrics, name='metrics'),
    path('search', views.search, name='search'),
    path('nodes/<slug:nodeID>', views.nodes_detail, name='node-detail'),
    path('channels/<slug:chanID>', views.channels_detail, name='channel-detail'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
