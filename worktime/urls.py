from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WorkModeViewSet, EmployeeWorkModeViewSet, LeaveTypeViewSet, 
    LeaveRequestViewSet, LeaveBalanceViewSet, WorkScheduleViewSet,
    WorkModeOverrideDateViewSet, AttendanceRecordViewSet, DailyAttendanceSummaryViewSet
)

router = DefaultRouter()
router.register(r'work-modes', WorkModeViewSet)
router.register(r'employee-work-modes', EmployeeWorkModeViewSet)
router.register(r'leave-types', LeaveTypeViewSet)
router.register(r'leave-requests', LeaveRequestViewSet)
router.register(r'leave-balances', LeaveBalanceViewSet)
router.register(r'work-schedules', WorkScheduleViewSet)
router.register(r'work-mode-override-dates', WorkModeOverrideDateViewSet)
router.register(r'attendance-records', AttendanceRecordViewSet)
router.register(r'attendance-summaries', DailyAttendanceSummaryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]