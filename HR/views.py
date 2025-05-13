from rest_framework import generics
from .models import StaffDetails, Attendance, LeaveRequest, LeaveComment, Loan, LoanComment, Overtime, OvertimeComment, Fine, FineComment, Appraisal, AppraisalComment
from rest_framework.exceptions import NotFound
from .serializers import StaffDetailsSerializer, VisaDetailsSerializer,OvertimeSerializer,AppraisalCommentSerializer, AppraisalSerializer, FineCommentSerializer, FineSerializer, OvertimeCommentSerializer, AttendanceSerializer, LeaveRequestSerializer, LeaveCommentSerializer, LoanSerializer, LoanCommentSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

class StaffDetailsListCreateView(generics.ListCreateAPIView):
    serializer_class = StaffDetailsSerializer

    def get_queryset(self):
        staff_type = self.kwargs['type'].capitalize()
        if staff_type not in ['Staff', 'Manpower']:
            raise NotFound("Invalid staff type. Must be 'staff' or 'manpower'.")
        return StaffDetails.objects.filter(staff_type=staff_type)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['type'] = self.kwargs['type']
        return context

class StaffDetailsRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = StaffDetailsSerializer
    lookup_field = 'staff_id'

    def get_queryset(self):
        staff_type = self.kwargs['type'].capitalize()
        if staff_type not in ['Staff', 'Manpower']:
            raise NotFound("Invalid staff type. Must be 'staff' or 'manpower'.")
        return StaffDetails.objects.filter(staff_type=staff_type)

    def get_object(self):
        obj = super().get_object()
        obj.visa_status = obj._get_visa_status()
        obj.save()
        return obj

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['type'] = self.kwargs['type']
        return context

class VisaDetailsListView(generics.ListAPIView):
    serializer_class = VisaDetailsSerializer

    def get_queryset(self):
        staff_type = self.kwargs['type'].capitalize()
        if staff_type not in ['Staff', 'Manpower']:
            raise NotFound("Invalid staff type. Must be 'staff' or 'manpower'.")
        return StaffDetails.objects.filter(staff_type=staff_type)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['type'] = self.kwargs['type']
        return context

class VisaDetailsRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = VisaDetailsSerializer
    lookup_field = 'staff_id'

    def get_queryset(self):
        staff_type = self.kwargs['type'].capitalize()
        if staff_type not in ['Staff', 'Manpower']:
            raise NotFound("Invalid staff type. Must be 'staff' or 'manpower'.")
        return StaffDetails.objects.filter(staff_type=staff_type)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['type'] = self.kwargs['type']
        return context

class AttendanceListCreateView(generics.ListCreateAPIView):
    serializer_class = AttendanceSerializer

    def get_queryset(self):
        staff_type = self.kwargs['type'].capitalize()
        if staff_type not in ['Staff', 'Manpower']:
            raise NotFound("Invalid staff type. Must be 'staff' or 'manpower'.")
        queryset = Attendance.objects.filter(staff__staff_type=staff_type)
        staff_id = self.request.query_params.get('staff_id')
        if staff_id:
            queryset = queryset.filter(staff__staff_id=staff_id)
        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['type'] = self.kwargs['type']
        return context

class AttendanceRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AttendanceSerializer
    lookup_url_kwarg = 'staff_id'

    def get_queryset(self):
        staff_type = self.kwargs['type'].capitalize()
        if staff_type not in ['Staff', 'Manpower']:
            raise NotFound("Invalid staff type. Must be 'staff' or 'manpower'.")
        return Attendance.objects.filter(staff__staff_type=staff_type)

    def get_object(self):
        staff_type = self.kwargs['type'].capitalize()
        staff_id = self.kwargs.get('staff_id')
        date = self.kwargs.get('date')
        try:
            attendance = Attendance.objects.get(
                staff__staff_id=staff_id,
                staff__staff_type=staff_type,
                date=date
            )
            return attendance
        except Attendance.DoesNotExist:
            raise NotFound("Attendance record not found for the given staff and date.")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['type'] = self.kwargs['type']
        return context

class LeaveRequestListCreateView(generics.ListCreateAPIView):
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        staff_type = self.kwargs['type'].capitalize()
        if staff_type not in ['Staff', 'Manpower']:
            raise NotFound("Invalid staff type. Must be 'staff' or 'manpower'.")
        queryset = LeaveRequest.objects.filter(staff__staff_type=staff_type)
        staff_id = self.request.query_params.get('staff_id')
        if staff_id:
            queryset = queryset.filter(staff__staff_id=staff_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user.username)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['type'] = self.kwargs['type']
        return context

class LeaveRequestRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        staff_type = self.kwargs['type'].capitalize()
        if staff_type not in ['Staff', 'Manpower']:
            raise NotFound("Invalid staff type. Must be 'staff' or 'manpower'.")
        return LeaveRequest.objects.filter(staff__staff_type=staff_type)

    def get_object(self):
        try:
            return super().get_object()
        except LeaveRequest.DoesNotExist:
            raise NotFound("Leave request not found.")

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['type'] = self.kwargs['type']
        return context

class LeaveCommentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, leave_request_id, type):
        staff_type = type.capitalize()
        if staff_type not in ['Staff', 'Manpower']:
            return Response(
                {"detail": "Invalid staff type. Must be 'staff' or 'manpower'."},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            leave_request = LeaveRequest.objects.get(id=leave_request_id, staff__staff_type=staff_type)
        except LeaveRequest.DoesNotExist:
            return Response(
                {"detail": "Leave request not found for the given ID and staff type."},
                status=status.HTTP_404_NOT_FOUND
            )
        data = {
            'leave_request': leave_request.id,
            'comment': request.data.get('comment'),
            'commenter': request.user.username,
        }
        serializer = LeaveCommentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LeaveCommentDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, leave_request_id, comment_id, type):
        staff_type = type.capitalize()
        if staff_type not in ['Staff', 'Manpower']:
            return Response(
                {"detail": "Invalid staff type. Must be 'staff' or 'manpower'."},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            leave_request = LeaveRequest.objects.get(id=leave_request_id, staff__staff_type=staff_type)
        except LeaveRequest.DoesNotExist:
            return Response(
                {"detail": "Leave request not found for the given ID and staff type."},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            comment = LeaveComment.objects.get(id=comment_id, leave_request=leave_request)
        except LeaveComment.DoesNotExist:
            return Response(
                {"detail": "Comment not found for the given ID."},
                status=status.HTTP_404_NOT_FOUND
            )
        if comment.commenter != request.user.username:
            return Response(
                {"detail": "You do not have permission to delete this comment."},
                status=status.HTTP_403_FORBIDDEN
            )
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class LoanListCreateView(generics.ListCreateAPIView):
    serializer_class = LoanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        staff_type = self.kwargs['type'].capitalize()
        if staff_type not in ['Staff', 'Manpower']:
            raise NotFound("Invalid staff type. Must be 'staff' or 'manpower'.")
        queryset = Loan.objects.filter(staff__staff_type=staff_type)
        staff_id = self.request.query_params.get('staff_id')
        if staff_id:
            queryset = queryset.filter(staff__staff_id=staff_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user.username)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['type'] = self.kwargs['type']
        return context

class LoanRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LoanSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        staff_type = self.kwargs['type'].capitalize()
        if staff_type not in ['Staff', 'Manpower']:
            raise NotFound("Invalid staff type. Must be 'staff' or 'manpower'.")
        return Loan.objects.filter(staff__staff_type=staff_type)

    def get_object(self):
        try:
            return super().get_object()
        except Loan.DoesNotExist:
            raise NotFound("Loan not found.")

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['type'] = self.kwargs['type']
        return context

class LoanCommentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, loan_id, type):
        staff_type = type.capitalize()
        if staff_type not in ['Staff', 'Manpower']:
            return Response(
                {"detail": "Invalid staff type. Must be 'staff' or 'manpower'."},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            loan = Loan.objects.get(id=loan_id, staff__staff_type=staff_type)
        except Loan.DoesNotExist:
            return Response(
                {"detail": "Loan not found for the given ID and staff type."},
                status=status.HTTP_404_NOT_FOUND
            )
        data = {
            'loan': loan.id,
            'comment': request.data.get('comment'),
            'commenter': request.user.username,
        }
        serializer = LoanCommentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoanCommentDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, loan_id, comment_id, type):
        staff_type = type.capitalize()
        if staff_type not in ['Staff', 'Manpower']:
            return Response(
                {"detail": "Invalid staff type. Must be 'staff' or 'manpower'."},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            loan = Loan.objects.get(id=loan_id, staff__staff_type=staff_type)
        except Loan.DoesNotExist:
            return Response(
                {"detail": "Loan not found for the given ID and staff type."},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            comment = LoanComment.objects.get(id=comment_id, loan=loan)
        except LoanComment.DoesNotExist:
            return Response(
                {"detail": "Comment not found for the given ID."},
                status=status.HTTP_404_NOT_FOUND
            )
        if comment.commenter != request.user.username:
            return Response(
                {"detail": "You do not have permission to delete this comment."},
                status=status.HTTP_403_FORBIDDEN
            )
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class OvertimeListCreateView(generics.ListCreateAPIView):
    serializer_class = OvertimeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        staff_type = self.kwargs['type'].capitalize()
        if staff_type not in ['Staff', 'Manpower']:
            raise NotFound("Invalid staff type. Must be 'staff' or 'manpower'.")
        queryset = Overtime.objects.filter(staff__staff_type=staff_type)
        staff_id = self.request.query_params.get('staff_id')
        if staff_id:
            queryset = queryset.filter(staff__staff_id=staff_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user.username)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['type'] = self.kwargs['type']
        return context

class OvertimeRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OvertimeSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        staff_type = self.kwargs['type'].capitalize()
        if staff_type not in ['Staff', 'Manpower']:
            raise NotFound("Invalid staff type. Must be 'staff' or 'manpower'.")
        return Overtime.objects.filter(staff__staff_type=staff_type)

    def get_object(self):
        try:
            return super().get_object()
        except Overtime.DoesNotExist:
            raise NotFound("Overtime request not found.")

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['type'] = self.kwargs['type']
        return context

class OvertimeCommentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, overtime_id, type):
        staff_type = type.capitalize()
        if staff_type not in ['Staff', 'Manpower']:
            return Response(
                {"detail": "Invalid staff type. Must be 'staff' or 'manpower'."},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            overtime = Overtime.objects.get(id=overtime_id, staff__staff_type=staff_type)
        except Overtime.DoesNotExist:
            return Response(
                {"detail": "Overtime request not found for the given ID and staff type."},
                status=status.HTTP_404_NOT_FOUND
            )
        data = {
            'overtime': overtime.id,
            'comment': request.data.get('comment'),
            'commenter': request.user.username,
        }
        serializer = OvertimeCommentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OvertimeCommentDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, overtime_id, comment_id, type):
        staff_type = type.capitalize()
        if staff_type not in ['Staff', 'Manpower']:
            return Response(
                {"detail": "Invalid staff type. Must be 'staff' or 'manpower'."},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            overtime = Overtime.objects.get(id=overtime_id, staff__staff_type=staff_type)
        except Overtime.DoesNotExist:
            return Response(
                {"detail": "Overtime request not found for the given ID and staff type."},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            comment = OvertimeComment.objects.get(id=comment_id, overtime=overtime)
        except OvertimeComment.DoesNotExist:
            return Response(
                {"detail": "Comment not found for the given ID."},
                status=status.HTTP_404_NOT_FOUND
            )
        if comment.commenter != request.user.username:
            return Response(
                {"detail": "You do not have permission to delete this comment."},
                status=status.HTTP_403_FORBIDDEN
            )
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class FineListCreateView(generics.ListCreateAPIView):
    serializer_class = FineSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        staff_type = self.kwargs['type'].capitalize()
        if staff_type not in ['Staff', 'Manpower']:
            raise NotFound("Invalid staff type. Must be 'staff' or 'manpower'.")
        queryset = Fine.objects.filter(staff__staff_type=staff_type)
        staff_id = self.request.query_params.get('staff_id')
        if staff_id:
            queryset = queryset.filter(staff__staff_id=staff_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user.username)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['type'] = self.kwargs['type']
        return context

class FineRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FineSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        staff_type = self.kwargs['type'].capitalize()
        if staff_type not in ['Staff', 'Manpower']:
            raise NotFound("Invalid staff type. Must be 'staff' or 'manpower'.")
        return Fine.objects.filter(staff__staff_type=staff_type)

    def get_object(self):
        try:
            return super().get_object()
        except Fine.DoesNotExist:
            raise NotFound("Fine not found.")

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['type'] = self.kwargs['type']
        return context

class FineCommentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, fine_id, type):
        staff_type = type.capitalize()
        if staff_type not in ['Staff', 'Manpower']:
            return Response(
                {"detail": "Invalid staff type. Must be 'staff' or 'manpower'."},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            fine = Fine.objects.get(id=fine_id, staff__staff_type=staff_type)
        except Fine.DoesNotExist:
            return Response(
                {"detail": "Fine not found for the given ID and staff type."},
                status=status.HTTP_404_NOT_FOUND
            )
        data = {
            'fine': fine.id,
            'comment': request.data.get('comment'),
            'commenter': request.user.username,
        }
        serializer = FineCommentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FineCommentDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, fine_id, comment_id, type):
        staff_type = type.capitalize()
        if staff_type not in ['Staff', 'Manpower']:
            return Response(
                {"detail": "Invalid staff type. Must be 'staff' or 'manpower'."},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            fine = Fine.objects.get(id=fine_id, staff__staff_type=staff_type)
        except Fine.DoesNotExist:
            return Response(
                {"detail": "Fine not found for the given ID and staff type."},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            comment = FineComment.objects.get(id=comment_id, fine=fine)
        except FineComment.DoesNotExist:
            return Response(
                {"detail": "Comment not found for the given ID."},
                status=status.HTTP_404_NOT_FOUND
            )
        if comment.commenter != request.user.username:
            return Response(
                {"detail": "You do not have permission to delete this comment."},
                status=status.HTTP_403_FORBIDDEN
            )
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class AppraisalListCreateView(generics.ListCreateAPIView):
    serializer_class = AppraisalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        staff_type = self.kwargs['type'].capitalize()
        if staff_type not in ['Staff', 'Manpower']:
            raise NotFound("Invalid staff type. Must be 'staff' or 'manpower'.")
        queryset = Appraisal.objects.filter(staff__staff_type=staff_type)
        staff_id = self.request.query_params.get('staff_id')
        if staff_id:
            queryset = queryset.filter(staff__staff_id=staff_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user.username)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['type'] = self.kwargs['type']
        return context

class AppraisalRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AppraisalSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        staff_type = self.kwargs['type'].capitalize()
        if staff_type not in ['Staff', 'Manpower']:
            raise NotFound("Invalid staff type. Must be 'staff' or 'manpower'.")
        return Appraisal.objects.filter(staff__staff_type=staff_type)

    def get_object(self):
        try:
            return super().get_object()
        except Appraisal.DoesNotExist:
            raise NotFound("Appraisal not found.")

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['type'] = self.kwargs['type']
        return context

class AppraisalCommentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, appraisal_id, type):
        staff_type = type.capitalize()
        if staff_type not in ['Staff', 'Manpower']:
            return Response(
                {"detail": "Invalid staff type. Must be 'staff' or 'manpower'."},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            appraisal = Appraisal.objects.get(id=appraisal_id, staff__staff_type=staff_type)
        except Appraisal.DoesNotExist:
            return Response(
                {"detail": "Appraisal not found for the given ID and staff type."},
                status=status.HTTP_404_NOT_FOUND
            )
        data = {
            'appraisal': appraisal.id,
            'comment': request.data.get('comment'),
            'commenter': request.user.username,
        }
        serializer = AppraisalCommentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AppraisalCommentDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, appraisal_id, comment_id, type):
        staff_type = type.capitalize()
        if staff_type not in ['Staff', 'Manpower']:
            return Response(
                {"detail": "Invalid staff type. Must be 'staff' or 'manpower'."},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            appraisal = Appraisal.objects.get(id=appraisal_id, staff__staff_type=staff_type)
        except Appraisal.DoesNotExist:
            return Response(
                {"detail": "Appraisal not found for the given ID and staff type."},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            comment = AppraisalComment.objects.get(id=comment_id, appraisal=appraisal)
        except AppraisalComment.DoesNotExist:
            return Response(
                {"detail": "Comment not found for the given ID."},
                status=status.HTTP_404_NOT_FOUND
            )
        if comment.commenter != request.user.username:
            return Response(
                {"detail": "You do not have permission to delete this comment."},
                status=status.HTTP_403_FORBIDDEN
            )
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)