from rest_framework import serializers

class RecommendationRequestSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(min_value=1)
    subject_id = serializers.IntegerField(min_value=1)
    topic_id = serializers.IntegerField(min_value=1)

class RecommendationResponseSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    difficulty = serializers.FloatField()
    source = serializers.CharField()