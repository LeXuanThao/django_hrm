from rest_framework import serializers
from .models import Employee, Account

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'email']  # Chỉ trả về id và email

class EmployeeSerializer(serializers.ModelSerializer):
    account = AccountSerializer()  # Sử dụng nested serializer cho account

    class Meta:
        model = Employee
        fields = '__all__'  # Bao gồm tất cả các trường trong model Employee