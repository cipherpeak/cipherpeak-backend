from django.contrib import admin
from .models import  MonthlyEmployeeReport, MonthlyClientReport,MonthlyIncomeReport,MonthlyExpenseReport

admin.site.register(MonthlyEmployeeReport)
admin.site.register(MonthlyClientReport)
admin.site.register(MonthlyIncomeReport)
admin.site.register(MonthlyExpenseReport)



