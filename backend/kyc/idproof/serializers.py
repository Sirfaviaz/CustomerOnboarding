from rest_framework import serializers
from .models import CustomerModel, CustomerDocumentModel, CountryModel, DocumentSetModel

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = CountryModel
        fields = ['id', 'name']

class DocumentSetSerializer(serializers.ModelSerializer):
    countries = CountrySerializer(many=True)

    class Meta:
        model = DocumentSetModel
        fields = ['id', 'name_of_document', 'countries', 'has_backside', 'ocr_labels']

class CustomerSerializer(serializers.ModelSerializer):
    nationality = CountrySerializer()
    created_by = serializers.StringRelatedField()

    class Meta:
        model = CustomerModel
        fields = ['id', 'surname', 'first_name', 'nationality', 'gender', 'created_by']

class CustomerDocumentSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer()

    class Meta:
        model = CustomerDocumentModel
        fields = ['id', 'customer', 'attached_file', 'extracted_json', 'created_at']
