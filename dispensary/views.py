from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, viewsets
from accounts.models import Department
from administration.views import get_conditions, pagination_datatable
from django.utils.translation import gettext_lazy as _
from accounts.permissions import IsDispensary
from dispensary.common_methods import create_mail_pdf, create_pdf
from dispensary.models import Bill, Medicine, Transaction
from datetime import datetime
from dispensary.serializers import BillSerializer, MedicineSerializer, TransactionSerializer
from doctor.models import Diagnosis
from doctor.serializers import DiagnosisSerializer


from registration.models import Appointment
# Create your views here.

#-----------------------------------MEDICINE---------------------------------------------------
#------------API---------------
class MedicineView(viewsets.ModelViewSet):
    queryset = Medicine.objects.all()
    serializer_class = MedicineSerializer
    http_method_names = ['get', 'post', 'delete', 'patch']
    permission_classes = [IsAuthenticated, IsDispensary]    
    
    def list(self, request):
        context = {}
        try:          
            columns = ['id','name', 'used_for', 'quantity', 'price', "discount_percent", "date_added",'last_modified']
            date_columns = ['last_modified']
            last_modified_start = request.query_params.get('last_modified_start','').strip()
            last_modified_end = request.query_params.get('last_modified_end','').strip()
            date_filter = [last_modified_start, last_modified_end]
            #------------------
            medicine_data = pagination_datatable(Medicine, columns, **request.query_params, 
            hospital = request.user.hospital, date_columns = date_columns,
            date_filter = date_filter, date_col_filter = 'last_modified')
            #------------------
            serializer = MedicineSerializer(medicine_data['data'], many = True)
            context['data'] = serializer.data
            context['draw'] = medicine_data['draw']
            context['recordsTotal'] = medicine_data['recordsTotal']
            context['recordsFiltered'] = medicine_data['recordsFiltered']
            return Response(context, status = status.HTTP_200_OK)
        except Exception as e:
            context['error'] = e
            return Response(context, status = status.HTTP_404_NOT_FOUND)

    def retrieve(self, request, pk):
        context = {}
        try:
            try:     
                medicine_data = self.queryset.get(id = pk, hospital = request.user.hospital)
            except Medicine.DoesNotExist:
                context['error'] = {"id": [_(f"Medicine ID: {pk} does not exist!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)
            serializer = MedicineSerializer(medicine_data)    
            context['data'] = serializer.data
            return Response(context, status = status.HTTP_200_OK) 
        except Exception as e:
            context['error'] = e
        context['message'] = _('Medicine was not retrieved!')
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

    def create(self, request):
        context = {}
        data = request.data
        try:          
            serializer = MedicineSerializer(data = data)
            serializer.context["hospital"] = request.user.hospital #pass context to serializer
            if serializer.is_valid():
                serializer.save()
                context['data'] = serializer.data
                context['message'] = _(f'Medicine added!') 
                return Response(context, status = status.HTTP_201_CREATED)
            context ['error'] = serializer.errors
        except Exception as e:
            context['error'] = e
        context['message'] = _('Medicine was not added!')   
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk):
        context = {}
        data = request.data    
        try:
            try:      
                medicine_data = self.queryset.get(id = pk, hospital = request.user.hospital)
            except Medicine.DoesNotExist:
                context['error'] = {"id": [_(f"ID: {pk} does not exist!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)

            serializer = MedicineSerializer(medicine_data, data = data, partial = True)
            serializer.context["hospital"] = request.user.hospital
            
            if serializer.is_valid():
                serializer.save()
                context['data'] = serializer.data
                context['message'] =  _(f'Medicine: {serializer.data["id"]} updated!')
                return Response(context, status = status.HTTP_200_OK) 
            context ['error'] = serializer.errors
        except Exception as e:
            context['error'] = e
        context['message'] = _('Medicine was not updated!')
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk):
        context = {}
        try:
            try:     
                medicine_data = self.queryset.get(id = pk, hospital = request.user.hospital)
            except Medicine.DoesNotExist:
                context['error'] = {"id": [_(f"ID: {pk} does not exist!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)
            medicine_data.delete()
            context['message'] =  _(f"Medicine: {pk} deleted!")
            return Response(context, status = status.HTTP_204_NO_CONTENT) 
        except Exception as e:
            context['error'] = e
        context['message'] = _('Medicine was not deleted!')
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

#-----------------------------------BILL---------------------------------------------------
#------------API---------------
class BillView(viewsets.ModelViewSet):
    queryset = Bill.objects.all()
    serializer_class = BillSerializer
    http_method_names = ['get', 'post', 'patch']
    permission_classes = [IsAuthenticated, IsDispensary]    
    
    def list(self, request):
        context = {}
        try:        
            columns = ['id','bill_date', 'appointment', 'details', 'total_price']
            date_columns = ['bill_date']
            exclude = ['appointment']
            bill_date_start = request.query_params.get('bill_date_start','').strip()
            bill_date_end = request.query_params.get('bill_date_end','').strip()
            date_filter = [bill_date_start, bill_date_end]
            #------------------
            bill_data = pagination_datatable(Bill, columns, **request.query_params, 
            hospital = request.user.hospital, date_columns = date_columns,
            date_filter = date_filter, date_col_filter = 'appointment_date', exclude = exclude)
            #------------------
            serializer = BillSerializer(bill_data['data'], many = True)
            context['data'] = serializer.data
            context['draw'] = bill_data['draw']
            context['recordsTotal'] = bill_data['recordsTotal']
            context['recordsFiltered'] = bill_data['recordsFiltered']
            return Response(context, status = status.HTTP_200_OK)
        except Exception as e:
            context['error'] = e
            return Response(context, status = status.HTTP_404_NOT_FOUND)

    def retrieve(self, request, pk):
        context = {}
        try:
            try:     
                bill_data = self.queryset.get(id = pk, hospital = request.user.hospital)
            except Bill.DoesNotExist:
                context['error'] = {"id": [_(f"Bill ID: {pk} does not exist!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)
            serializer = BillSerializer(bill_data)    
            context['data'] = serializer.data
            return Response(context, status = status.HTTP_200_OK) 
        except Exception as e:
            context['error'] = e
        context['message'] = _('Bill was not retrieved!')
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

    def create(self, request):
        context = {}
        data = request.data
        try:          
            serializer = BillSerializer(data = data)
            serializer.context["hospital"] = request.user.hospital #pass context to serializer
            if serializer.is_valid():
                serializer.save()
                context['data'] = serializer.data
                context['message'] = _(f'Bill created!') 
                return Response(context, status = status.HTTP_201_CREATED)
            context ['error'] = serializer.errors
        except Exception as e:
            context['error'] = e
        context['message'] = _('Bill was not created!')   
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk):
        context = {}
        data = request.data
        if data.get('appointment'):
            context['error'] = {"appointment": [_(f"Cannot update appointment!")]} 
            return Response(context, status = status.HTTP_400_BAD_REQUEST)
        try:
            try:      
                bill_data = self.queryset.get(id = pk, hospital = request.user.hospital)
            except Bill.DoesNotExist:
                context['error'] = {"id": [_(f"ID: {pk} does not exist!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)

            try:      
                Transaction.objects.get(bill__id = pk, hospital = request.user.hospital)
                context['error'] = {"id": [_(f"ID: {pk} is already paid, Now cannot update this bill!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)
            except Transaction.DoesNotExist:
                pass

            serializer = BillSerializer(bill_data, data = data, partial = True)
            serializer.context["hospital"] = request.user.hospital
            serializer.context["fees"] = Department.objects.get(id = bill_data.appointment.department.id).fees
            if serializer.is_valid():
                serializer.save()
                context['data'] = serializer.data
                context['message'] =  _(f'Bill: {serializer.data["id"]} updated!')
                return Response(context, status = status.HTTP_200_OK) 
            context ['error'] = serializer.errors
        except Exception as e:
            context['error'] = e
        context['message'] = _('Bill was not updated!')
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

    @action(detail = False, methods = ['get'])
    def appointment_diagnosis(self, request):
        context = {}
        appointment_id = request.query_params.get('appointment_id', None)
        if not appointment_id:
            context['error'] = {"Appointment ID": [_(f"Appointment ID is required!")]}
            return Response(context, status = status.HTTP_400_BAD_REQUEST)
        try:
            try:
                medicine_data = Diagnosis.objects.get(appointment__id = appointment_id, hospital = request.user.hospital)
            except Diagnosis.DoesNotExist:
                context['error'] = {"id": [_(f"Diagnosis for Appointment ID: {appointment_id} does not exist!")]}
                return Response(context, status = status.HTTP_400_BAD_REQUEST)
            serializer = DiagnosisSerializer(medicine_data)    
            context['data'] = serializer.data
            return Response(context, status = status.HTTP_200_OK) 
        except Exception as e:
            context['error'] = e
        return Response(context, status = status.HTTP_400_BAD_REQUEST) 
        
#-----------------------------------TRANSACTION---------------------------------------------------
#------------API---------------

class TransactionView(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    http_method_names = ['get', 'post']
    permission_classes = [IsAuthenticated, IsDispensary]    
    
    def list(self, request):
        context = {}
        try:          
            columns = ['id','transaction_date', 'bill', 'amount', 'payment_mode']
            date_columns = ['transaction_date']

            transaction_date_start = request.query_params.get('transaction_date_start','').strip()
            transaction_date_end = request.query_params.get('transaction_date_end','').strip()
            date_filter = [transaction_date_start, transaction_date_end]
            #------------------
            transaction_data = pagination_datatable(Transaction, columns, **request.query_params, 
            hospital = request.user.hospital, date_columns = date_columns, 
            date_filter = date_filter, date_col_filter = 'transaction_date')
            #------------------
            serializer = TransactionSerializer(transaction_data['data'], many = True)
            context['data'] = serializer.data
            context['draw'] = transaction_data['draw']
            context['recordsTotal'] = transaction_data['recordsTotal']
            context['recordsFiltered'] = transaction_data['recordsFiltered']
            return Response(context, status = status.HTTP_200_OK)
        except Exception as e:
            context['error'] = e
            return Response(context, status = status.HTTP_404_NOT_FOUND)

    def retrieve(self, request, pk):
        context = {}
        try:
            try:     
                transaction_data = self.queryset.get(id = pk, hospital = request.user.hospital)
            except Transaction.DoesNotExist:
                context['error'] = {"id": [_(f"Transaction ID: {pk} does not exist!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)
            serializer = TransactionSerializer(transaction_data)    
            context['data'] = serializer.data
            return Response(context, status = status.HTTP_200_OK) 
        except Exception as e:
            context['error'] = e
        context['message'] = _('Transaction was not retrieved!')
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

    def create(self, request):
        context = {}
        data = request.data
        try:          
            serializer = TransactionSerializer(data = data)
            serializer.context["hospital"] = request.user.hospital #pass context to serializer
            if serializer.is_valid():
                serializer.save()
                bill = Bill.objects.get(pk = data.get('bill'))
                details = bill.details
                medicines = details["medicines"]
                for medicine in medicines:
                    medicine_model = Medicine.objects.get(pk = medicine["id"], hospital = request.user.hospital)   
                    medicine_model.quantity -= int(medicine["qty"])
                    medicine_model.save()
                
                msg = 'Transaction added!'
                if(not create_mail_pdf(bill)):
                    msg += '\nBill was not mailed!'

                context['data'] = serializer.data
                context['message'] = _(msg)

                return Response(context, status = status.HTTP_201_CREATED)
            context ['error'] = serializer.errors
        except Exception as e:
            context['error'] = e
        context['message'] = _('Transaction was not added!')   
        return Response(context, status = status.HTTP_400_BAD_REQUEST)
