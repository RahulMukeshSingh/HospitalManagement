import re
from django.conf import settings
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from accounts.models import Account, Department, Hospital, Roles
from django.contrib.auth.password_validation import validate_password

#--------------------------------------HOSPITAL------------------------------------------------

class HospitalSerializer(serializers.ModelSerializer):
    date_created = serializers.DateTimeField(format = settings.DATETIME_FORMAT, required=False, read_only=True)
    date_modified = serializers.DateTimeField(format = settings.DATETIME_FORMAT, required=False, read_only=True)

    class Meta:
        model = Hospital
        fields = ['id', 'name', 'date_created', 'date_modified']
        extra_kwargs = {
            'name': {'required': True}
        }

#--------------------------------------ACCOUNT------------------------------------------------

class AdminAccountSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required = True)
    last_login = serializers.DateTimeField(required=False, read_only=True)
    date_joined = serializers.DateTimeField(required=False, read_only=True)
    is_active = serializers.BooleanField(required = False)
    password = serializers.CharField(write_only = True, required = True, validators = [validate_password])
    password1 = serializers.CharField(write_only = True, required = True)
    class Meta:
        model = Account 
        exclude = ['is_staff', 'is_superuser', 'groups', 'user_permissions']
        extra_kwargs = {
            'name': {'required': True},
            'mobile': {'required': True},
            'hospital': {'required': True},
            'roles': {'required': False, 'read_only': True},
            'department': {'required': False, 'read_only': True}
        }

    def to_representation(self, instance):
        self.fields['roles'] =  serializers.StringRelatedField(read_only = True)
        self.fields['department'] =  serializers.StringRelatedField(read_only = True)
        self.fields['hospital'] =  serializers.StringRelatedField(read_only = True)        
        return super().to_representation(instance)
        

    def validate_email(self, value):
        email = value.lower()
        try:
            Account.objects.get(email = email)
        except Account.DoesNotExist:
            return email
        raise serializers.ValidationError(_(f'Email: {email} already exists!'))

    def validate_mobile(self, value):
        regex = re.compile("[6-9][0-9]{9}")
        if not regex.fullmatch(value):
            raise serializers.ValidationError(_('Enter a valid mobile number!'))
        try:
            Account.objects.get(mobile = value)
        except Account.DoesNotExist:
            return value
        raise serializers.ValidationError(_(f'Mobile No.: {value} already exists!'))

    def validate(self, validated_data):
        if(validated_data.get('password')):
            if validated_data['password'] != validated_data['password1']:
                raise serializers.ValidationError({"password": "Password fields didn't match."})        
        return validated_data
          
    def create(self, validated_data):
        validated_data.pop('password1')
        password = validated_data.pop('password')
        account = Account(**validated_data)
        account.set_password(password)
        roles, created = Roles.objects.get_or_create(name = 'admin', hospital = account.hospital)
        department, created = Department.objects.get_or_create(name = 'admin', hospital = account.hospital)
        account.roles = roles
        account.department = department
        account.save()
        return account

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required = True)
    password = serializers.CharField(write_only = True, required = True)

    def validate_username(self, value):
        if value.isnumeric():
            regex = re.compile("[6-9][0-9]{9}")
            if not regex.fullmatch(value):
                raise serializers.ValidationError(_('Enter a valid mobile number!'))
        else:
            regex = re.compile(r'([A-Za-z0-9]+[.-_+])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
            if not regex.fullmatch(value):
                raise serializers.ValidationError(_('Enter a valid email address!'))                    
        return value


class ForgetPasswordSerializer(serializers.Serializer):
    username = serializers.CharField(required = True)
    otp = serializers.CharField(max_length = 6, required = True)
    password = serializers.CharField(write_only = True, required = True, validators = [validate_password])
    password1 = serializers.CharField(write_only = True, required = True) 

    def validate_username(self, value):
        if value.isnumeric():
            regex = re.compile("[6-9][0-9]{9}")
            if not regex.fullmatch(value):
                raise serializers.ValidationError(_('Enter a valid mobile number!'))
        else:
            regex = re.compile(r'([A-Za-z0-9]+[.-_+])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
            if not regex.fullmatch(value):
                raise serializers.ValidationError(_('Enter a valid email address!'))                    
        return value 

    def validate(self, validated_data):
        if validated_data['password'] != validated_data['password1']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})        
        return validated_data       


class OTPSerializer(serializers.Serializer):
    username = serializers.CharField(required = True)

    def validate_username(self, value):
        if value.isnumeric():
            regex = re.compile("[6-9][0-9]{9}")
            if not regex.fullmatch(value):
                raise serializers.ValidationError(_('Enter a valid mobile number!'))
        else:
            regex = re.compile(r'([A-Za-z0-9]+[.-_+])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
            if not regex.fullmatch(value):
                raise serializers.ValidationError(_('Enter a valid email address!'))
        return value
