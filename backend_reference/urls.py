from django.urls import path

from .views import TechnicalsFetchTriggerAPIView, TechnicalsSaveOutputTriggerAPIView

urlpatterns = [
    path("technicals/fetch/", TechnicalsFetchTriggerAPIView.as_view(), name="technicals-fetch-trigger"),
    path("technicals/save-output/", TechnicalsSaveOutputTriggerAPIView.as_view(), name="technicals-save-output-trigger"),
]
