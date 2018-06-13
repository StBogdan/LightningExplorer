from django.urls import path
from . import views

app_name = 'nodes'
urlpatterns = [
    path('', views.index, name='index'),
    path('index', views.index, name='index'),
    path('nodes', views.nodes, name='nodes'),
    path('channels', views.channels, name='channels'),
    path('nodes/<slug:nodeID>', views.nodes_detail, name='node-detail'),
    path('channels/<slug:chanID>', views.channels_detail, name='channel-detail'),
]
