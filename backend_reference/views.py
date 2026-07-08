"""
On-demand trigger endpoints for the two Celery tasks in tasks.py. Normal
operation should be Celery Beat (see celery_beat_schedule_snippet.py); these
exist for manual runs and testing.
"""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .tasks import fetch_and_push_technicals_input, save_technicals_output_to_db


class TechnicalsFetchTriggerAPIView(APIView):
    """
    POST body (optional): {"tickers": ["TSHA US", ...]}
    Defaults to every ticker in config.TICKER_DEAL_TYPES if omitted.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        tickers = request.data.get("tickers")
        task = fetch_and_push_technicals_input.delay(tickers)
        return Response({"task_id": task.id}, status=status.HTTP_202_ACCEPTED)


class TechnicalsSaveOutputTriggerAPIView(APIView):
    """Reads output/technicals_summary.json and saves it into QuantAgent."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        task = save_technicals_output_to_db.delay()
        return Response({"task_id": task.id}, status=status.HTTP_202_ACCEPTED)
