import re
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from registration.models import Appointment, Patient, gender_choices


class PatientSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required = True)
    gender = serializers.ChoiceField(required = True, choices = gender_choices)
    
    class Meta:
        model = Patient
        fields = '__all__'
        extra_kwargs = {
            'name': {'required': True},
            'mobile': {'required': True},
            'dob': {'required': True},
            'department': {'required': True},
            'hospital': {'required': False, 'read_only': True},
            'register_date': {'required': False, 'read_only': True},
            'last_accessed': {'required': False, 'read_only': True}
        }

    def to_representation(self, instance):
        self.fields['gender'] = serializers.ChoiceField(required = True, choices = gender_choices, source='get_gender_display') 
        self.fields['hospital'] =  serializers.StringRelatedField(read_only = True)        
        return super().to_representation(instance)
        

    def validate_email(self, value):
        email = value.lower()
        try:
            Patient.objects.get(email = email, hospital = self.context.get("hospital"))
        except Patient.DoesNotExist:
            return email
        raise serializers.ValidationError(_(f'Email: {email} already exists!'))

    def validate_mobile(self, value):
        regex = re.compile("[6-9][0-9]{9}")
        if not regex.fullmatch(value):
            raise serializers.ValidationError(_('Enter a valid mobile number!'))
        try:
            Patient.objects.get(mobile = value, hospital = self.context.get("hospital"))
        except Patient.DoesNotExist:
            return value
        raise serializers.ValidationError(_(f'Mobile No.: {value} already exists!'))



    def validate(self, validated_data):
        validated_data['hospital'] = self.context.get("hospital")
        return validated_data
    

class AppointmentSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Appointment
        fields = '__all__'
        extra_kwargs = {
            'appointment_date': {'required': True},
            'patient': {'required': True},
            'doctor': {'required': True},
            'department': {'required': True},
            'present': {'required': False, 'read_only': True},
            'diagnosed': {'required': False, 'read_only': True},
            'hospital': {'required': False, 'read_only': True}
        }

    def to_representation(self, instance):
        self.fields['patient'] =  serializers.StringRelatedField(read_only = True)         
        self.fields['doctor'] =  serializers.StringRelatedField(read_only = True) 
        self.fields['department'] =  serializers.StringRelatedField(read_only = True)                 
        self.fields['hospital'] =  serializers.StringRelatedField(read_only = True)        
        return super().to_representation(instance)

    def validate(self, validated_data):
        validated_data['hospital'] = self.context.get("hospital")
        return validated_data


class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        exclude = ['appointment_date']
        extra_kwargs = {
            'patient': {'required': False, 'read_only': True},
            'doctor': {'required': False, 'read_only': True},
            'department': {'required': False, 'read_only': True},
            'present': {'required': False},
            'diagnosed': {'required': False, 'write_only': True},
            'hospital': {'required': False, 'read_only': True}
        }

    def to_representation(self, instance):
        self.fields['hospital'] =  serializers.StringRelatedField(read_only = True)        
        return super().to_representation(instance)

    def validate(self, validated_data):
        validated_data['hospital'] = self.context.get("hospital")
        return validated_data

