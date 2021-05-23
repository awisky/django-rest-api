from rest_framework import viewsets, status

from .serializers import DocumentSerializer
from .models import Document

from rest_framework.decorators import action
from rest_framework.response import Response

import logging

_logger = logging.getLogger(__name__)


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all().order_by('name')
    serializer_class = DocumentSerializer
