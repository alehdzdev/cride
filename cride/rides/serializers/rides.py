"""Rides serializers"""
from datetime import timedelta

# Django
from django.utils import timezone

# Django Rest Framework
from rest_framework import serializers

# Local
from cride.rides.models import Ride
from cride.circles.models import Memberships
from cride.users.serializers import UserModelSerializer


class RideModelSerializer(serializers.ModelSerializer):
    """Ride model serializer."""

    offered_by = UserModelSerializer(read_only=True)
    offered_in = serializers.StringRelatedField()

    passengers = UserModelSerializer(read_only=True, many=True)

    class Meta:
        """Meta class."""
        model = Ride
        fields = '__all__'
        read_only_fields = (
            'offered_by',
            'offered_in',
            'rating'
        )

    def update(self, instance, data):
        """Allow update only before departure date."""
        now =  timezone.now()
        if instance.departure_date <= now:
            raise serializers.ValidationError('Ongoing rides cannot be modified.')
        return super().update(instance, data)


class CreateRideSerializer(serializers.ModelSerializer):
    """Create ride serializers."""
    offered_by = serializers.HiddenField(default=serializers.CurrentUserDefault)
    available_seat = serializers.IntegerField(min_value=1, max_value=15)

    class Meta:
        """Meta class."""
        model = Ride
        exclude = (
            'offered_in',
            'passengers',
            'rating',
            'is_active'
        )

    def validate_departure_date(self, data):
        """Verify date is not in the past."""
        min_date = timezone.now() + timedelta(minutes=10)
        if data < min_date:
            raise serializers.ValidationError(
                'Departure time must be at least pass the next 20 minutes window.'
            )
        return data

    def validate(self, data):
        """Validate

        Verify that the person who offers the ride is member
        and also the same user making the request.
        """
        if self.context['request'].user != data['offered_by']:
            raise serializers.ValidationError('Rides offered on behalf of others are not allowed.')

        user = data['offered_by']
        circle = self.context['circle']
        try:
            membership = Memberships.objects.get(
                user=user,
                circle=circle,
                is_active=True
            )
        except Memberships.DoesNotExist:
            raise serializers.ValidationError('User is not an active member of the circle.')

        if data['arrival_date'] <= data['departure_date']:
            raise serializers.ValidationError('Departure date must be after arrival date.')

        self.context['membership'] = membership
        return data

    def create(self, data):
        """Create ride and update stats."""
        circle = self. context['circle']
        ride = Ride.objects.create(**data, offered_in=circle)

        # Circle
        circle.rides_offered += 1
        circle.save()

        # Membership
        membership = self.context['membership']
        membership.rides_offered += 1
        membership.save()

        # Profile
        profile = data['offered_by'].profile
        profile.rides_offered += 1
        profile.save()

        return ride
