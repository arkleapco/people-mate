from os import name
from pyexpat import model
from rest_framework import serializers
from company.models import Enterprise


class Enterpriseserializers(serializers.ModelSerializer):
    class Meta:
        model = Enterprise
        fields = ['id', 'name', 'arabic_name', 'reg_tax_num',
                  'commercail_record', 'address1', 'phone', 'mobile', 'fax', 'email', 'country', 'start_date', 'end_date', 'created_by']

    # def create(self, validated_data):
    #     name = self.context.get('name')
    #     if not name:
    #         raise ValidationError(detail={"name":})
