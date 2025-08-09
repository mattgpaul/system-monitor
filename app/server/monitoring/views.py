import logging

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

# Set up logging
logger = logging.getLogger(__name__)


@api_view(["GET"])
def health_check(request) -> None:
    """
    SImple health check endpoint to verify the server is running.
    """
    logger.info("Health check endpoint accessed")

    response_data = {
        "status": "healthy",
        "message": "Server is running",
        "service": "system-monitor-api",
    }

    logger.info(f"Health check response: {response_data}")
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["POST"])
def receive_telemetry(request) -> None:
    """
    Receive telemetry data from monitoring agents.
    """
    logger.info(f"Received telemetry data from {request.META.get('REMOTE_ADDR', 'unknown')}")
    logger.info(f"Telemetry payload: {request.data}")

    # Basica validation - check required fields
    required_fields = ["timestamp", "hostname", "metrics"]
    for field in required_fields:
        if field not in request.data:
            logger.error(f"Missing required field: {field}")
            return Response(
                {"error": f"Missing required field: {field}"}, status=status.HTTP_400_BAD_REQUEST
            )

    response_data = {
        "status": "received",
        "hostname": request.data.get("hostname"),
        "timestamp": request.data.get("timestamp"),
        "metrics_count": len(request.data.get("metrics", {})),
    }

    logger.info(f"Successfully processed telemetry from {request.data.get('hostname')}")
    return Response(response_data, status=status.HTTP_201_CREATED)
