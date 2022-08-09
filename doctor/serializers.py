from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from dispensary.models import Medicine
from doctor.models import Diagnosis, DoctorAvailability

class DoctorAvailabilitySerializer(serializers.ModelSerializer):

    class Meta:
        model = DoctorAvailability
        fields = '__all__'
        extra_kwargs = {
            'doctor': {'required': True},
            'not_available': {'required': True},
            'hospital': {'required': False, 'read_only': True}
        }

    def to_representation(self, instance):
        self.fields['doctor'] =  serializers.StringRelatedField(read_only = True)                 
        self.fields['hospital'] =  serializers.StringRelatedField(read_only = True)        
        return super().to_representation(instance)

    def validate(self, validated_data):
        validated_data['hospital'] = self.context.get("hospital")
        return validated_data


class DiagnosisSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Diagnosis
        fields = '__all__'
        extra_kwargs = {
            'appointment': {'required': True},
            'diagnosis': {'required': True},
            'symptoms': {'required': True},
            'medicine': {'required': True},
            'hospital': {'required': False, 'read_only': True}
        }

    def validate_appointment(self, value):
        try:                 
            if  value.doctor != self.context.get("user"):
                raise serializers.ValidationError(_(f'There is no such Appointment: {value.id}!'))
            Diagnosis.objects.get(appointment = value)
        except Diagnosis.DoesNotExist:
            return value
        raise serializers.ValidationError(_(f'Appointment: {value.id} already exists!'))

    def validate_medicine(self, value):
        medicine_list = []
        medicine_id = []
        for medicine in value:
            try:
                if not medicine.get('id', None): raise serializers.ValidationError(('No Medicine ID provided!'))
                id = int(medicine['id'])
                qty = int(medicine.get('qty', 1))
                direction = medicine.get('direction', "No direction provided")
                medicine = Medicine.objects.get(pk = id, hospital = self.context.get("user").hospital)
                if qty > medicine.quantity:
                    raise serializers.ValidationError(_(f'Quantity cannot be more than {medicine.quantity}, for Medicine ID: {id}!'))
                if qty < 1:
                    raise serializers.ValidationError(_(f'Quantity cannot be less than 1, for Medicine ID: {id}!'))
                if id not in medicine_id:
                    medicine_list.append({'id' : medicine.id, 'name' : medicine.name, 'qty' : qty, 'direction' : direction})
                    medicine_id.append(id)
                else:
                    raise serializers.ValidationError(_(f'Medicine ID: {id} is added more than once!'))    
            except Medicine.DoesNotExist:
                raise serializers.ValidationError(_(f'Medicine ID: {id} is not correct!'))    
        return medicine_list    

    def to_representation(self, instance):
        self.fields['appointment'] =  serializers.StringRelatedField(read_only = True)               
        self.fields['hospital'] =  serializers.StringRelatedField(read_only = True)        
        return super().to_representation(instance)

    def validate(self, validated_data):
        validated_data['hospital'] = self.context.get("user").hospital
        return validated_data


           
