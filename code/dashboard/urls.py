from django.urls import path
from .views import *

urlpatterns = [
    path('', Trips.as_view(), name='home'),  # Updated to make this the new home
    path('trip/<uuid:pk>/', DetailViewTrip.as_view(), name='detail_trip'),
    path('add_trip/', AddTrip.as_view(), name='add_trip'),
    path('detail/<uuid:pk>/', DetailViewSensor.as_view(), name='detail'),
    path('analysis/<uuid:pk>/', AnalysisViewSensor.as_view(), name='analysis'),
    path('add_records/<uuid:trip_id>/', RecordAdd.as_view(), name='add_records'),
    path('api/generate-graph/<uuid:pk>/', api_generate_graph, name='api_generate_graph'),
    path('api_generate_temperatures_up/<uuid:pk>/', api_generate_temperatures_up, name='api_generate_temperatures_up'),
    path('api_generate_temperatures_low/<uuid:pk>/', api_generate_temperatures_low, name='api_generate_temperatures_low'),
    path('api_generate_temperatures_limits/<uuid:pk>/', api_generate_temperatures_limits, name='api_generate_temperatures_limits'),

    
]
