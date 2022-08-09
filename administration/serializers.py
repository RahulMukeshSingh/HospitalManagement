import re
from rest_framework import serializers
from accounts.models import Account, Department, Roles
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.password_validation import validate_password
#-----------------------------------DEPARTMENT---------------------------------------------------

class DepartmentSerializer(serializers.ModelSerializer):
    date_created = serializers.DateTimeField(required=False, read_only=True)
    date_modified = serializers.DateTimeField(required=False, read_only=True)
    #date_modified = serializers.DateTimeField(format = settings.DATETIME_FORMAT, required=False, read_only=True)
    
    class Meta:
        model = Department
        fields = ['id', 'name', 'fees', 'date_created', 'date_modified', 'hospital']
        extra_kwargs = {
            'name': {'required': True},
            'fees': {'required': True},            
            'hospital': {'required': False, 'read_only': True}
        }

    def to_representation(self, instance):
        self.fields['hospital'] =  serializers.StringRelatedField(read_only = True)        
        return super().to_representation(instance) 

    def validate_name(self, value):
        name = value.lower()
        try:
            Department.objects.get(name = name, hospital = self.context.get("hospital"))
        except Department.DoesNotExist:
            return name
        raise serializers.ValidationError(_(f'Department: {name} already exists!'))

    def validate(self, validated_data):
        validated_data['hospital'] = self.context.get("hospital")
        return validated_data


class DepartmentDropDownSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name']


#--------------------------------------ROLES------------------------------------------------

class RolesSerializer(serializers.ModelSerializer):
    date_created = serializers.DateTimeField(required=False, read_only=True)
    date_modified = serializers.DateTimeField(required=False, read_only=True)
    
    class Meta:
        model = Roles
        fields = ['id', 'name', 'date_created', 'date_modified', 'hospital']
        extra_kwargs = {
            'name': {'required': True},
            'hospital': {'required': False, 'read_only': True}
        }

    def to_representation(self, instance):
        self.fields['hospital'] =  serializers.StringRelatedField(read_only = True)        
        return super().to_representation(instance) 

    def validate_name(self, value):
        name = value.lower()
        try:
            Roles.objects.get(name = name, hospital = self.context.get("hospital"))
        except Roles.DoesNotExist:
            return name
        raise serializers.ValidationError(_(f'Roles: {name} already exists!'))

    def validate(self, validated_data):
        validated_data['hospital'] = self.context.get("hospital")
        return validated_data


class RolesDropDownSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = ['id', 'name']



#--------------------------------------ACCOUNT STAFF------------------------------------------------

class AccountSerializer(serializers.ModelSerializer):
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
            'roles': {'required': True},
            'department': {'required': True},
            'hospital': {'required': False, 'read_only': True}
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
            Account.objects.get(mobile = value, hospital = self.context.get("hospital"))
        except Account.DoesNotExist:
            return value
        raise serializers.ValidationError(_(f'Mobile No.: {value} already exists!'))

    def validate(self, validated_data):
        if(validated_data.get('password')):
            if validated_data['password'] != validated_data.get('password1', None):
                raise serializers.ValidationError({"password": "Password fields didn't match."})                
        validated_data['hospital'] = self.context.get("hospital")
        return validated_data
          
    def create(self, validated_data):
        validated_data.pop('password1')
        password = validated_data.pop('password')
        account = Account(**validated_data)
        account.set_password(password)
        account.save()
        return account


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account 
        fields = ['id', 'name', 'email']

class UpdatePasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only = True, required = True, validators = [validate_password])
    password1 = serializers.CharField(write_only = True, required = True)


    def validate(self, validated_data):
        if validated_data['password'] != validated_data['password1']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return validated_data    





        