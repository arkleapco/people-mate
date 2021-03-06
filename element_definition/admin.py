from django.contrib import admin
from element_definition.models import (Element_Batch,
                                       Element_Batch_Master, Element_Link, SalaryStructure, Element,
                                       StructureElementLink, ElementHistory,ElementFormula
                                       )
from import_export.forms import ImportForm, ConfirmImportForm
from import_export.admin import ImportExportModelAdmin, ImportMixin
from .resources import *


####################################### Inlines Goes Here #############################################
class ElementBatchMasterInline(admin.TabularInline):
    model = Element_Batch_Master
    fields = (
        'element_master_fk',
        'element_batch_fk',
        'start_date',
        'end_date',
    )


class StructureElementLinkInline(admin.TabularInline):
    model = StructureElementLink

class ElementFormulaInline(admin.TabularInline):
    model = ElementFormula

####################################### Admin Forms #############################################
@admin.register(SalaryStructure)
class SalaryStructureAdmin(ImportExportModelAdmin):
    class Meta:
        resource_class = SalaryStructureResource


    inlines = [
        StructureElementLinkInline
    ]
    list_display = ('structure_name','enterprise')

@admin.register(Element_Batch)
class ElementBatchAdmin(admin.ModelAdmin):
    class Meta:
        model = Element_Batch

    fields = (
        'payroll_fk',
        'batch_name',
        'start_date',
        'end_date',
    )
    inlines = [
        ElementBatchMasterInline
    ]


@admin.register(Element_Link)
class Element_Link_Admin(admin.ModelAdmin):
    class Meta:
        model = Element_Link

    fields = (
        'element_master_fk',
        'payroll_fk',
        'element_dept_id_fk',
        'element_job_id_fk',
        'element_grade_fk',
        'element_position_id_fk',
        'assignment_category',
        'standard_flag',
        'link_to_all_payroll_flag',
        'start_date',
        'end_date',
    )


@admin.register(Element)
class ElementAdmin(ImportExportModelAdmin):
    class Meta:
        model = Element
    list_display = ('element_name','enterprise', 'element_type')


@admin.register(ElementFormula)
class ElementFormulaAdmin(ImportExportModelAdmin):
    class Meta:
        model = ElementFormula
    list_display = ('id', 'element')


@admin.register(StructureElementLink)
class StructureElementAdmin(ImportExportModelAdmin):
    class Meta:
        resource_class = StructureElementLinkResource


@admin.register(ElementHistory)
class ElementHistoryAdmin(admin.ModelAdmin):
    class Meta:
        model = ElementHistory

    list_display = ('element_name','enterprise')