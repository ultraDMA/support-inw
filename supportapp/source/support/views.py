import requests
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.mixins import (CreateModelMixin, DestroyModelMixin,
                                   ListModelMixin, Response,
                                   RetrieveModelMixin, status)
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from support import tasks
from support.serializers import *


class TicketView(ListModelMixin,
                 CreateModelMixin,
                 RetrieveModelMixin,
                 DestroyModelMixin, GenericViewSet):
    queryset = TicketInstance.objects.all()
    permission_classes = [IsAuthenticated, ]
    serializer_class = TicketSerializer
    filter_backends = [DjangoFilterBackend, ]
    filterset_fields = ['status', 'id']
    pagination_class = PageNumberPagination

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user, from_user=self.request.user.username)

    def list(self, request, *args, **kwargs):
        # Staff User have access to all of tickets
        if request.user.is_staff:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            serializer = TicketSerializer(page, many=True, context={'request': request})
            return Response(serializer.data)
        else:
            # User have access only to all of their own tickets
            queryset = self.filter_queryset(self.get_queryset().filter(owner=request.user))
            page = self.paginate_queryset(queryset)
            serializer = TicketSerializer(page, many=True, context={'request': request})
            return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        # Staff User have access to any of ticket
        if request.user.is_staff:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            # User have access only to own ticket
            instance = self.get_object()
            if instance.owner != request.user:
                return Response({'error': 'forbidden'}, status=status.HTTP_403_FORBIDDEN)
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        if request.user.is_superuser:  # allows to delete Ticket instance only by Superuser
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response({'result': 'deleted'}, status=status.HTTP_200_OK)

        return Response({'error': 'forbidden'}, status=status.HTTP_403_FORBIDDEN)

    @action(methods=['POST'], detail=True)
    def answer(self, request, pk=None):
        """
        This action allows to registered user and staff user to send a comment messages
        to Ticket instance
        """
        ticket_instance = self.get_object()  # check is object exist
        serializer = AddCommentSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save(
                to_ticket=ticket_instance,  # TicketInstance.objects.filter(id=pk)[0],
                owner=self.request.user,
                from_user=self.request.user.username)
            if ticket_instance.owner != request.user:
                data_to_task = {
                    'email': ticket_instance.owner.email,
                    'ticket_message': ticket_instance.message,
                    'ticket_url': f'{request.build_absolute_uri(reverse("ticket-detail", kwargs={"pk": pk}))}',
                    'answer_message': serializer.data.get('message')
                }
                tasks.send_email_notify.delay(data_to_task)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=['POST'], detail=True)
    def set_status(self, request, **kwargs):
        """
        This action allows to staff user to change 'status' field of Ticket instance.
        Just make a POST request with {"status": "%status_code%"} in the body of a request.
        Accepted status codes are: 'u' - UNCOMPLETED, 'c' - COMPLETED, 'f' - FROZEN.
        Also user_id of staff user will be written in 'changed_status' field of Ticket instance,
        when staff user will change a 'status' field
        """
        if request.user.is_staff:
            instance = self.get_object()
            if request.data.get('status') is not None:
                serializer = TicketStatusSerializer(instance, data=request.data, partial=True)
                if serializer.is_valid(raise_exception=True):
                    serializer.update(instance, serializer.validated_data)
                    serializer.save(changed_status=request.user)
                return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
            return Response({'status': '/must be provided/ choices are "c""u""f"'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'forbidden'}, status=status.HTTP_403_FORBIDDEN)


class TicketCommentView(ListModelMixin,
                        RetrieveModelMixin,
                        DestroyModelMixin, GenericViewSet):
    queryset = TicketComment.objects.all()
    serializer_class = TicketCommentSerializer
    permission_classes = [IsAdminUser]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.request.method == 'GET' and (self.kwargs.get('pk', None) is not None):
            return [IsAuthenticated()]
        return [permission() for permission in self.permission_classes]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        user_owner = instance.to_ticket.owner  # user-owner of Ticket instance
        if request.user == user_owner or request.user.is_staff:
            serializer = TicketCommentSerializer(instance, context={'request': request})
            return Response(serializer.data)
        return Response({'error': 'forbidden'}, status=status.HTTP_403_FORBIDDEN)


class UserActivationView(APIView):
    """
    Custom Endpoint for email-link User activation
    """
    permission_classes = [AllowAny, ]

    def get(self, request, uid, token):
        protocol = 'https://' if request.is_secure() else 'http://'
        web_url = protocol + request.get_host()
        post_url = web_url + "/auth/users/activation/"
        post_data = {'uid': uid, 'token': token}
        result = requests.post(post_url, data=post_data)
        if result.status_code == 200:
            return Response({'detail': 'your account has been successfully activated'}, status=result.status_code)
        return Response({'detail': 'link expired'}, status=result.status_code)
