from django.urls import path, register_converter
from .views import (
    StaffDetailsListCreateView, StaffDetailsRetrieveUpdateDestroyView,
    VisaDetailsListView, VisaDetailsRetrieveUpdateView,
    AttendanceListCreateView, AttendanceRetrieveUpdateDestroyView,
    LeaveRequestListCreateView, LeaveRequestRetrieveUpdateDestroyView,
    LeaveCommentCreateView, LeaveCommentDeleteView,
    LoanListCreateView, LoanRetrieveUpdateDestroyView,
    LoanCommentCreateView, LoanCommentDeleteView,
    OvertimeListCreateView, OvertimeRetrieveUpdateDestroyView,
    OvertimeCommentCreateView, OvertimeCommentDeleteView,
    FineListCreateView, FineRetrieveUpdateDestroyView,
    FineCommentCreateView, FineCommentDeleteView,
    AppraisalListCreateView, AppraisalRetrieveUpdateDestroyView,
    AppraisalCommentCreateView, AppraisalCommentDeleteView
)


from datetime import datetime

class DateConverter:
    regex = r'\d{4}-\d{2}-\d{2}'

    def to_python(self, value):
        return datetime.strptime(value, '%Y-%m-%d').date()

    def to_url(self, value):
        return value.strftime('%Y-%m-%d')

register_converter(DateConverter, 'date')


urlpatterns = [
    path('<str:type>/staffdetails/', StaffDetailsListCreateView.as_view(), name='staffdetails-list-create'),
    path('<str:type>/staffdetails/<str:staff_id>/', StaffDetailsRetrieveUpdateDestroyView.as_view(), name='staffdetails-retrieve-update-destroy'),
    path('<str:type>/visa-details/', VisaDetailsListView.as_view(), name='visa-details-list'),
    path('<str:type>/visa-details/<str:staff_id>/', VisaDetailsRetrieveUpdateView.as_view(), name='visa-details-retrieve-update'),
    path('<str:type>/attendance/', AttendanceListCreateView.as_view(), name='attendance-list-create'),
    path('<str:type>/attendance/<str:staff_id>/<date:date>/', AttendanceRetrieveUpdateDestroyView.as_view(), name='attendance-retrieve-update-destroy'),
    path('<str:type>/leaverequests/', LeaveRequestListCreateView.as_view(), name='leave-request-list-create'),
    path('<str:type>/leaverequests/<int:id>/', LeaveRequestRetrieveUpdateDestroyView.as_view(), name='leave-request-retrieve-update-destroy'),
    path('<str:type>/leaverequests/<int:leave_request_id>/comments/', LeaveCommentCreateView.as_view(), name='leave-comment-create'),
    path('<str:type>/leaverequests/<int:leave_request_id>/comments/<int:comment_id>/', LeaveCommentDeleteView.as_view(), name='leave-comment-delete'),
    path('<str:type>/loans/', LoanListCreateView.as_view(), name='loan-list-create'),
    path('<str:type>/loans/<int:id>/', LoanRetrieveUpdateDestroyView.as_view(), name='loan-retrieve-update-destroy'),
    path('<str:type>/loans/<int:loan_id>/comments/', LoanCommentCreateView.as_view(), name='loan-comment-create'),
    path('<str:type>/loans/<int:loan_id>/comments/<int:comment_id>/', LoanCommentDeleteView.as_view(), name='loan-comment-delete'),
    path('<str:type>/overtimes/', OvertimeListCreateView.as_view(), name='overtime-list-create'),
    path('<str:type>/overtimes/<int:id>/', OvertimeRetrieveUpdateDestroyView.as_view(), name='overtime-retrieve-update-destroy'),
    path('<str:type>/overtimes/<int:overtime_id>/comments/', OvertimeCommentCreateView.as_view(), name='overtime-comment-create'),
    path('<str:type>/overtimes/<int:overtime_id>/comments/<int:comment_id>/', OvertimeCommentDeleteView.as_view(), name='overtime-comment-delete'),
    path('<str:type>/fines/', FineListCreateView.as_view(), name='fine-list-create'),
    path('<str:type>/fines/<int:id>/', FineRetrieveUpdateDestroyView.as_view(), name='fine-retrieve-update-destroy'),
    path('<str:type>/fines/<int:fine_id>/comments/', FineCommentCreateView.as_view(), name='fine-comment-create'),
    path('<str:type>/fines/<int:fine_id>/comments/<int:comment_id>/', FineCommentDeleteView.as_view(), name='fine-comment-delete'),
    path('<str:type>/appraisals/', AppraisalListCreateView.as_view(), name='appraisal-list-create'),
    path('<str:type>/appraisals/<int:id>/', AppraisalRetrieveUpdateDestroyView.as_view(), name='appraisal-retrieve-update-destroy'),
    path('<str:type>/appraisals/<int:appraisal_id>/comments/', AppraisalCommentCreateView.as_view(), name='appraisal-comment-create'),
    path('<str:type>/appraisals/<int:appraisal_id>/comments/<int:comment_id>/', AppraisalCommentDeleteView.as_view(), name='appraisal-comment-delete'),
]