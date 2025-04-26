from rest_framework import serializers
from .models import MessageName

class MessageNameSerializer(serializers.ModelSerializer):
    bg_color_display = serializers.CharField(source='get_bg_color_display', read_only=True)
    text_color_display = serializers.CharField(source='get_text_color_display', read_only=True)
    occupancy_display = serializers.CharField(source='get_occupancy_display', read_only=True)

    class Meta:
        model = MessageName
        fields = [
            'id',
            'number',
            'name',
            'bg_color',
            'bg_color_display',
            'text_color',
            'text_color_display',
            'occupancy',
            'occupancy_display',
            'updated',
            'created'
        ]
