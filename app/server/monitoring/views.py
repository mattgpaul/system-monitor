
import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

# Set up logging
logger = logging.getLogger(__name__)

@api_view(['GET'])
def health_check(request):
    """
    SImple health check endpoint to verify the server is running.
    """
    logger.info("Health check endpoint accessed")

    response_data = {
        'status': 'healthy',
        'message': 'Server is running',
        'service': 'system-monitor-api',
    }

    logger.info(f"Health check response: {response_data}")
    return Response(response_data, status=status.HTTP_200_OK)
