"""Users views."""
# Django

# Django Rest Framework
from rest_framework import status, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated
)

# Local
from cride.users.models.users import User
from cride.users.serializers.profiles import ProfileModelSerializer
from cride.users.serializers.users import UserLoginSerializer, UserModelSerializer, UserSignupSerializer, AccountVerificationSerialzier
from cride.users.permissions import IsAccountOwner
from cride.circles.models.circles import Circle
from cride.circles.serializers.circles import CircleModelSerializer

class UserViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """User view set.

    Handler sign up, login and account verification.
    """

    queryset = User.objects.filter(is_active=True, is_client=True)
    serializer_class = UserModelSerializer
    lookup_field = 'username'

    def get_permissions(self):
        """Assign permissions based on action."""
        if self.action in ['signup', 'login', 'verify']:
            permissions = [AllowAny]
        elif self.action in ['retrieve', 'update', 'partial_update']:
            permissions = [IsAuthenticated, IsAccountOwner]
        else:
            permissions = [IsAuthenticated]
        return [p() for p in permissions]

    @action(detail=False, methods=['POST'])
    def login(self, request):
        """User sign in"""
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, token = serializer.save()
        data = {
            'user': UserModelSerializer(user).data,
            'access_token': token
        }
        return Response(data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['POST'])
    def signup(self, request):
        """User sign up"""
        serializer = UserSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        data = UserModelSerializer(user).data
        return Response(data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['POST'])
    def verify(self, request):
        """User verification"""
        serializer = AccountVerificationSerialzier(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = {'message': 'OK'}
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['PUT', 'PATCH'])
    def profile(self, request, *args, **kwargs):
        """Update profile."""
        user = self.get_object()
        profile = user.profile
        partial = request.method == 'PATCH'
        serializer = ProfileModelSerializer(
            profile,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = UserModelSerializer(user).data
        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        """Add extra data to the response."""
        response = super(UserViewSet, self.retrieve(request, *args, **kwargs))
        circles = Circle.objects.filter(
            members=request.user,
            memberships__is_active=True
        )
        data = {
            'user': response.data,
            'circles': CircleModelSerializer(circles, many=True).data
        }
        response.data = data
        return response