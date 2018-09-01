from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'nodes'
urlpatterns = [
    #Defaults
    path('', views.index, name='index'),
    path('index', views.index, name='index'),

    #Visualiser
    path('<slug:network>/visualiser/<int:date_logged>', views.visualiser, name='visualiser'),
    path('<slug:network>/visualiser', views.visualiser, name='visualiser'),

    #Nodes
        #Details
    path('<slug:network>/node/<slug:nodePubKey>/<int:date_logged>', views.nodes_detail, name='node-detail'),
    path('<slug:network>/node/<slug:nodePubKey>', views.nodes_detail, name='node-detail'),
        #Generals
    path('<slug:network>/nodes', views.nodes, name='nodes'),
    path('<slug:network>/nodes/<int:date_logged>', views.nodes, name='nodes'),

    #Channels
        #Details
    path('<slug:network>/channel/<slug:chanID>/<int:date_logged>', views.channel_detail, name='channel-detail'),
    path('<slug:network>/channel/<slug:chanID>', views.channel_detail, name='channel-detail'),
        #Generals
    path('<slug:network>/channels', views.channels, name='channels'),
    path('<slug:network>/channels/<int:date_logged>', views.channels, name='channel-detail'),


    #Metrics
    path('<slug:network>/metrics', views.metrics, name='metrics'),
    path('<slug:network>/metrics/<slug:metricID>', views.metric_detail, name='metric-detail'),

    #Active monitoring
    path('active', views.active_dashboard, name='active_dashboard'),
    path('active/<slug:node_pubkey>', views.active_node_detail, name='active_dashboard'),
    path('active/<slug:node_pubkey>/channels/<slug:chan_id>', views.active_channel_detail, name='active_dashboard'),


    #About & Misc.
    path('about', views.about, name='about'),
    path('<slug:network>/search', views.search, name='search')


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
