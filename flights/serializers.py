from rest_framework import serializers

class ResultSerializer(serializers.Serializer):
    key = serializers.CharField()
    values = serializers.ListField(child=serializers.CharField())

class ResultsSerializer(serializers.Serializer):
    result = serializers.DictField(child=ResultSerializer())