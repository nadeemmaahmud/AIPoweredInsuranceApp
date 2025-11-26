from rest_framework import serializers
from .models import Case
from django.core.validators import FileExtensionValidator
from django.core.files.storage import default_storage

class CaseSerializer(serializers.ModelSerializer):
    files = serializers.SerializerMethodField()

    files_upload = serializers.ListField(
        child=serializers.FileField(validators=[FileExtensionValidator(['pdf','jpg','png'])]),
        write_only=True,
        required=False
    )

    class Meta:
        model = Case
        fields = [
            'id',
            'user',
            'type_of_injury',
            'date_of_incident',
            'description',
            'files',
            'files_upload',
            'created_at'
        ]
        read_only_fields = ['created_at']

    def get_files(self, obj):
        request = self.context.get('request')
        file_urls = []
        for file_path in obj.files:
            if request:
                file_urls.append(request.build_absolute_uri(f'/media/{file_path}'))
            else:
                file_urls.append(file_path)
        return file_urls

    def create(self, validated_data):
        files = validated_data.pop('files_upload', [])
        case = Case.objects.create(**validated_data)
        uploaded_paths = []
        for file in files:
            path = default_storage.save(f'case_files/{file.name}', file)
            uploaded_paths.append(path)
        case.files = uploaded_paths
        case.save()
        return case

    def update(self, instance, validated_data):
        files = validated_data.pop('files_upload', [])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        for file in files:
            path = default_storage.save(f'case_files/{file.name}', file)
            instance.files.append(path)
        instance.save()
        return instance
