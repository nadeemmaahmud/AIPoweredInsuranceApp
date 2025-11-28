from rest_framework import serializers
from .models import Case, CaseFile

class CaseFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseFile
        fields = ['id', 'file', 'uploaded_at']

class CaseSerializer(serializers.ModelSerializer):
    files = CaseFileSerializer(many=True, read_only=True)

    class Meta:
        model = Case
        fields = ['id', 'user', 'type_of_injury', 'date_of_incident', 'description', 'created_at', 'files']
        read_only_fields = ['user', 'id', 'created_at']

class CaseCreateUpdateSerializer(serializers.ModelSerializer):
    files = serializers.ListField(
        child=serializers.FileField(max_length=100000, allow_empty_file=False, use_url=False),
        write_only=True,
        required=False
    )

    class Meta:
        model = Case
        fields = ['id', 'user', 'type_of_injury', 'date_of_incident', 'description', 'files']
        read_only_fields = ['user', 'id', 'created_at']

    def create(self, validated_data):
        files = validated_data.pop('files', [])
        case = Case.objects.create(**validated_data)
        for f in files:
            CaseFile.objects.create(case=case, file=f)
        return case

    def update(self, instance, validated_data):
        files = validated_data.pop('files', [])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        for f in files:
            CaseFile.objects.create(case=instance, file=f)
        return instance
