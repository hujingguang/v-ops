from django.shortcuts import render
from django.contrib.auth.decorators import permission_required
import logging

logger = logging.getLogger('default')


def env_list(request):
    """env_list.

    Args:
        request:
    """
    return render(request, "envList.html", {})

def soft_list(request):
    """soft_list.

    Args:
        request:
    """
    return render(request, "softList.html", {})
