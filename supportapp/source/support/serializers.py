from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from djoser.conf import settings
from rest_framework import serializers
from support.models import *


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(style={"input_type": "password"}, write_only=True)
    tickets = serializers.HyperlinkedRelatedField(many=True, read_only=True, view_name='ticket-detail')
    email = serializers.EmailField(max_length=254, required=True, allow_blank=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'email', 'is_active', 'tickets']
        read_only_fields = ['is_active']

    def validate(self, attrs):
        user = User(**attrs)
        password = attrs.get("password")

        try:
            validate_password(password, user)
        except ValidationError as e:
            serializer_error = serializers.as_serializer_error(e)
            raise serializers.ValidationError(
                {"password": serializer_error["non_field_errors"]}
            )

        return attrs

    def create(self, validated_data):
        try:
            user = self.perform_create(validated_data)
        except IntegrityError:
            self.fail("cannot_create_user")

        return user

    def perform_create(self, validated_data):
        with transaction.atomic():
            user = User.objects.create_user(**validated_data)
            if settings.SEND_ACTIVATION_EMAIL:
                user.is_active = False
                user.save(update_fields=["is_active"])
        return user


class TicketSerializer(serializers.ModelSerializer):
    from_user_id = serializers.ReadOnlyField(source='owner.id')
    from_user = serializers.ReadOnlyField(source='owner.username')
    answers = serializers.HyperlinkedRelatedField(many=True, read_only=True, view_name='comment-detail')
    changed_status = serializers.PrimaryKeyRelatedField(read_only=True)
    status = serializers.ReadOnlyField()

    class Meta:
        model = TicketInstance
        fields = ['id', 'from_user_id', 'from_user', 'message', 'status', 'changed_status', 'answers', 'created_at']


class TicketStatusSerializer(serializers.ModelSerializer):
    changed_status = serializers.PrimaryKeyRelatedField(read_only=True)  # user_id of staff user, who has change status

    class Meta:
        model = TicketInstance
        fields = ['status', 'changed_status']


class TicketCommentSerializer(serializers.ModelSerializer):
    from_user_id = serializers.ReadOnlyField(source='owner.id')
    to_ticket = serializers.HyperlinkedRelatedField(read_only=True, view_name='ticket-detail')

    class Meta:
        model = TicketComment
        fields = ['id', 'from_user_id', 'from_user', 'to_ticket', 'message', 'answered_at']


class AddCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketComment
        fields = ['id', 'message']
