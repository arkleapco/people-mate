from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import *
from company.models import Enterprise




class SalaryStructureResource(resources.ModelResource):
    class Meta:
        model = SalaryStructure


    enterprise = fields.Field(
        column_name='enterprise',
        attribute='enterprise',
        widget=ForeignKeyWidget(Enterprise, 'pk'))


    def after_import_instance(self, instance, new, **kwargs):
        if new or not instance.created_by:
            instance.created_by = kwargs['user']
        instance.last_update_by = kwargs['user']



class StructureElementLinkResource(resources.ModelResource):
    class Meta:
        model = StructureElementLink


    salary_structure = fields.Field(
        column_name='salary_structure',
        attribute='salary_structure',
        widget=ForeignKeyWidget(SalaryStructure, 'pk'))


    element = fields.Field(
        column_name='element',
        attribute='element',
        widget=ForeignKeyWidget(Element, 'pk'))


    def after_import_instance(self, instance, new, **kwargs):
        if new or not instance.created_by:
            instance.created_by = kwargs['user']
        instance.last_update_by = kwargs['user']
