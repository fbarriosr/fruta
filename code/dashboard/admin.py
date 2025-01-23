from django.contrib import admin
from django.shortcuts import redirect
from django.contrib import messages
from search_admin_autocomplete.admin import SearchAutoCompleteAdmin
from admin_auto_filters.filters import AutocompleteFilter
from .models import *

# Define a custom action to efficiently delete records
def delete_selected_efficiently(modeladmin, request, queryset):
    """
    Efficiently deletes selected records to avoid performance issues.
    """
    num_deleted, _ = queryset.delete()  # Bulk delete records
    messages.success(request, f"{num_deleted} records deleted successfully.")

# Configure admin for the Record model
@admin.register(Record)
class RecordAdmin(SearchAutoCompleteAdmin, admin.ModelAdmin):
    search_fields = ["number"]  # Search fields
    list_display = ("sensor", "number", "time", "temperature")  # Visible fields in the list
    list_filter = ('sensor',)
    ordering = ["number"]
    actions = [delete_selected_efficiently]  # Add custom action
    list_per_page = 10  # Number of records per page

# Configure admin for the Record model
@admin.register(DecisionMessage)
class DecisionMessageAdmin(SearchAutoCompleteAdmin, admin.ModelAdmin):
    search_fields = ["decision"]  # Search fields
    list_display = ("decision", "descripcion")  # Visible fields in the list
    list_filter = ('decision',)
    ordering = ["decision"]
    list_per_page = 10  # Number of records per page

# Configure admin for the Sensor model
@admin.register(Sensor)
class SensorAdmin(SearchAutoCompleteAdmin, admin.ModelAdmin):
    search_fields = ["serial_number","trip"]  # Search fields
    list_display = ("serial_number", 'tag', "device", "pallet_location", "sensor_position")  # Updated visible fields
    list_filter = ('trip', 'sensor_position','pallet_location')  # Filters by related fields
    actions = [delete_selected_efficiently]  # Add custom action
    list_per_page = 10  # Number of records per page

# Configure admin for the Trip model
@admin.register(Trip)
class TripAdmin(SearchAutoCompleteAdmin, admin.ModelAdmin):
    search_fields = ["license_plate"]  # Search fields
    list_display = ("license_plate", "shipment","departure_date", "arrival_date", "origin", "destination", "product", "microorganism")  # Updated visible fields
    list_filter = ('product', 'microorganism')  # Filters by related fields
    list_per_page = 10  # Number of records per page

@admin.register(Parameters)
class ParametersAdmin(SearchAutoCompleteAdmin, admin.ModelAdmin):
    search_fields = ["name"]  # Search fields
    list_display = ("name", "value")  # Visible fields in the list
    list_per_page = 10  # Number of records per page

# Configure admin for the ProductType model
@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    search_fields = ["name"]  # Search fields
    list_display = ("name", "description")  # Visible fields in the list
    list_per_page = 10  # Number of records per page

# Configure admin for the Microorganism model
@admin.register(Microorganism)
class MicroorganismAdmin(admin.ModelAdmin):
    search_fields = ["name"]  # Search fields
    list_display = ("name", "description")  # Visible fields in the list
    list_per_page = 10  # Number of records per page

# Configure admin for the PalletLocation model
@admin.register(PalletLocation)
class PalletLocationAdmin(admin.ModelAdmin):
    search_fields = ["position"]  # Search fields
    list_display = ("id", "position")  # Visible fields in the list
    list_per_page = 10  # Number of records per page

# Configure admin for the SensorLocation model
@admin.register(SensorLocation)
class SensorLocationAdmin(admin.ModelAdmin):
    search_fields = ["name"]  # Search fields
    list_display = ("name", "description")  # Visible fields in the list
    list_per_page = 10  # Number of records per page

# Configurar el admin para el modelo Equation
@admin.register(Equation)
class EquationAdmin(admin.ModelAdmin):
    search_fields = [ "product__name", "microorganism__name"]  # Búsqueda por nombre y relaciones
    list_display = (
        "microorganism",
        "product",
        "LPD_form",
        "b_form",
        "n_form",
        "created_at",
        "updated_at",
    )  # Campos visibles en la lista
    list_filter = ("created_at", "updated_at", "product", "microorganism")  # Filtros
    ordering = ["microorganism__name", "product__name"]  # Orden predeterminado
    list_per_page = 10  # Registros por página


    