from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProjectViewSet, ProjectMemberViewSet, 
    TaskViewSet, TimeEntryViewSet,
    OvertimeRequestViewSet, OvertimePolicyViewSet
)

router = DefaultRouter()
router.register(r'projects', ProjectViewSet)
router.register(r'project-members', ProjectMemberViewSet)
router.register(r'tasks', TaskViewSet)
router.register(r'time-entries', TimeEntryViewSet)
router.register(r'overtime-requests', OvertimeRequestViewSet)
router.register(r'overtime-policies', OvertimePolicyViewSet)

urlpatterns = [
    path('', include(router.urls)),
]