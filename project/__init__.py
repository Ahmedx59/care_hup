from __future__ import absolute_import, unicode_literals

# هذا يضمن تحميل app عند تشغيل Django
from .celery import app as celery_app

__all__ = ('celery_app',)
