from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import *
from company.models import Enterprise




class LookupTypeResource(resources.ModelResource):
    class Meta:
        model = LookupType


    enterprise = fields.Field(
        column_name='enterprise',
        attribute='enterprise',
        widget=ForeignKeyWidget(Enterprise, 'pk'))


    def after_import_instance(self, instance, new, **kwargs):
        if new or not instance.created_by:
            instance.created_by = kwargs['user']
        instance.last_update_by = kwargs['user']



class InsuranceRuleResource(resources.ModelResource):
    class Meta:
        model = InsuranceRule


    enterprise = fields.Field(
        column_name='enterprise_name',
        attribute='enterprise_name',
        widget=ForeignKeyWidget(Enterprise, 'pk'))



    def after_import_instance(self, instance, new, **kwargs):
        if new or not instance.created_by:
            instance.created_by = kwargs['user']
        instance.last_update_by = kwargs['user']



class TaxRuleResource(resources.ModelResource):
    class Meta:
        model = TaxRule


    enterprise = fields.Field(
        column_name='enterprise',
        attribute='enterprise',
        widget=ForeignKeyWidget(Enterprise, 'pk'))



    def after_import_instance(self, instance, new, **kwargs):
        if new or not instance.created_by:
            instance.created_by = kwargs['user']
        instance.last_update_by = kwargs['user']


class Tax_SectionsResource(resources.ModelResource):
    class Meta:
        model = Tax_Sections


    tax_rule_id = fields.Field(
        column_name='tax_rule_id',
        attribute='tax_rule_id',
        widget=ForeignKeyWidget(TaxRule, 'pk'))



    def after_import_instance(self, instance, new, **kwargs):
        if new or not instance.created_by:
            instance.created_by = kwargs['user']
        instance.last_update_by = kwargs['user']
