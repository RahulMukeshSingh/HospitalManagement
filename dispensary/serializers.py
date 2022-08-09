from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from accounts.models import Department
from dispensary.models import Bill, Medicine, Transaction, payment_choices



class MedicineSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Medicine
        fields = '__all__'
        extra_kwargs = {
            'name': {'required': True},
            'used_for': {'required': True},
            'quantity': {'required': True},
            'price': {'required': True},
            'discount': {'required': False},
            'date_added': {'required': False, 'read_only': True},
            'last_modified': {'required': False, 'read_only': True},            
            'hospital': {'required': False, 'read_only': True}
        }

    def validate_name(self, value):
        name = value.lower()
        try:
            Medicine.objects.get(name = name, hospital = self.context.get("hospital"))
        except Medicine.DoesNotExist:
            return name
        raise serializers.ValidationError(_(f'Medicine: {name} already exists!'))

    def to_representation(self, instance):               
        self.fields['hospital'] =  serializers.StringRelatedField(read_only = True)        
        return super().to_representation(instance)

    def validate(self, validated_data):
        validated_data['hospital'] = self.context.get("hospital")
        return validated_data


class BillSerializer(serializers.ModelSerializer):
    total_amount = 0
    class Meta:
        model = Bill
        fields = '__all__'
        extra_kwargs = {
            'bill_date': {'required': False, 'read_only': True},
            'appointment': {'required': True},
            'details': {'required': True},
            'total_price': {'required': False, 'read_only': True},
            'hospital': {'required': False, 'read_only': True}
        }

    def validate_appointment(self, value):
        try:
            Bill.objects.get(appointment = value, hospital = self.context.get("hospital"))
        except Bill.DoesNotExist:
            return value
        raise serializers.ValidationError(_(f'Appointment: {value} already exists!'))

    def validate_details(self, value):
        medicine_list = []
        medicine_id = []
        for medicine in value:
            try:
                if not medicine.get('id', None): raise serializers.ValidationError(('No Medicine ID provided!'))
                id = int(medicine['id'])
                qty = int(medicine.get('qty', 1))
                medicine = Medicine.objects.get(pk = id, hospital = self.context.get("hospital"))
                if qty > medicine.quantity:
                    raise serializers.ValidationError(_(f'Quantity cannot be more than {medicine.quantity}, for Medicine ID: {id}!'))
                if qty < 1:
                    raise serializers.ValidationError(_(f'Quantity cannot be less than 1, for Medicine ID: {id}!'))
                if id not in medicine_id:
                    price = float(medicine.price)
                    discount = float(medicine.discount_percent)
                    medicine_list.append({'id' : medicine.id, 'name' : medicine.name, 'qty' : qty, 'price' : price, 
                    'discount_percent' : discount})
                    medicine_id.append(id)
                    self.total_amount += price * (1 - (discount / 100)) * qty
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
        if self.context.get("fees"):
            fees = float(self.context.get("fees"))
        else:    
            department = Department.objects.get(id = validated_data['appointment'].department.id)
            fees = float(department.fees)
        validated_data['details'] = {'Doctor Fees' : fees, 'medicines' : validated_data['details']}
        self.total_amount += fees
        validated_data['total_price'] = self.total_amount
        validated_data['hospital'] = self.context.get("hospital")
        return validated_data       


class TransactionSerializer(serializers.ModelSerializer):
    amount_paid = 0
    payment_mode = serializers.ChoiceField(required = True, choices = payment_choices)
    class Meta:
        model = Transaction
        fields = '__all__'
        extra_kwargs = {
            'transaction_date': {'required': False, 'read_only': True},            
            'bill': {'required': True},
            'amount': {'required': False, 'read_only': True},
            'hospital': {'required': False, 'read_only': True}
        }

    def validate_bill(self, value):
        if value.hospital != self.context.get("hospital"):
            raise serializers.ValidationError(_(f'No such Bill: {value.id} exists!'))
        try:
            Transaction.objects.get(bill = value, hospital = self.context.get("hospital"))
        except Transaction.DoesNotExist:
            self.amount_paid = value.total_price
            for medicine in value.details["medicines"]:
                try:
                    id = int(medicine['id'])
                    qty = int(medicine['qty'])
                    medicine = Medicine.objects.get(pk = id, hospital = self.context.get("hospital"))
                    if qty > medicine.quantity:
                        raise serializers.ValidationError(_(f'Quantity cannot be more than {medicine.quantity}, for Medicine ID: {id}!'))   
                except Medicine.DoesNotExist:
                    raise serializers.ValidationError(_(f'Medicine ID: {id} is not correct!'))  
            return value
        raise serializers.ValidationError(_(f'Bill: {value.id} already paid!'))       

    def to_representation(self, instance):               
        self.fields['hospital'] =  serializers.StringRelatedField(read_only = True)        
        return super().to_representation(instance)

    def validate(self, validated_data):
        validated_data['amount'] = self.amount_paid
        validated_data['hospital'] = self.context.get("hospital")
        return validated_data             