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
    path('api_export_csv_analysis/<uuid:pk>/', api_export_csv_analysis, name='api_export_csv_analysis'),
    path('api_export_temperatures_low_csv/<uuid:pk>/', api_export_temperatures_low_csv, name='api_export_temperatures_low_csv'),
    path('api_export_temperatures_up_csv/<uuid:pk>/', api_export_temperatures_up_csv, name='api_export_temperatures_up_csv'),
    path('api_export_temperatures_limits_csv/<uuid:pk>/', api_export_temperatures_limits_csv, name='api_export_temperatures_limits_csv'),
    path('trips/delete/<uuid:trip_id>/', DeleteTripView.as_view(), name='delete_trip'),
    path('sensors/delete/<uuid:sensor_id>/', DeleteSensorView.as_view(), name='delete_sensor'),

]
