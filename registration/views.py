from datetime import datetime
from tokenize import Token
from django.shortcuts import render
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, viewsets
from accounts.models import Account
from accounts.permissions import IsRegistration
from administration.serializers import DoctorSerializer
from administration.views import get_conditions, pagination_datatable
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.utils.translation import gettext_lazy as _
from doctor.models import DoctorAvailability
from doctor.views import doctor_availability
from registration.models import Appointment, Patient
from registration.serializers import AppointmentSerializer, PatientSerializer, TokenSerializer
# Create your views here.

#-----------------------------------PATIENT---------------------------------------------------
# #------------UI-----------------
# @cache_control(no_cache = True, must_revalidate = True, no_store = True)
# @login_required    
# def patient_request(request):
#     return render(request, 'patient.html') 

#------------API---------------

class PatientView(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    http_method_names = ['get', 'post', 'delete', 'patch']    
    permission_classes = [IsAuthenticated, IsRegistration]
    
    def list(self, request):
        context = {}
        try:
            columns = ['id','name','email',"mobile",'dob','gender','register_date','last_accessed']
            date_columns = ['register_date','last_accessed']
            last_accessed_start = request.query_params.get('last_accessed_start','').strip()
            last_accessed_end = request.query_params.get('last_accessed_end','').strip()
            date_filter = [last_accessed_start,last_accessed_end]
            #------------------
            patient_data = pagination_datatable(Patient, columns, **request.query_params, 
            hospital = request.user.hospital, date_columns = date_columns, 
            date_filter = date_filter, date_col_filter = 'last_accessed')
            #------------------
            serializer = PatientSerializer(patient_data['data'], many = True)
            context['data'] = serializer.data
            context['draw'] = patient_data['draw']
            context['recordsTotal'] = patient_data['recordsTotal']
            context['recordsFiltered'] = patient_data['recordsFiltered']
            return Response(context, status = status.HTTP_200_OK)
        except Exception as e:
            context['error'] = e
            return Response(context, status = status.HTTP_404_NOT_FOUND)

    def retrieve(self, request, pk):
        context = {}
        try:
            try:     
                patient_data = self.queryset.get(id = pk, hospital = request.user.hospital)
            except Patient.DoesNotExist:
                context['error'] = {"id": [_(f"ID: {pk} does not exist!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)
            serializer = PatientSerializer(patient_data)    
            context['data'] = serializer.data
            return Response(context, status = status.HTTP_200_OK) 
        except Exception as e:
            context['error'] = e
        context['message'] = _('Patient Account was not retrieved!')
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

    def create(self, request):
        context = {}
        try:
            request.data['gender'] = request.data['gender'].lower()
            serializer = PatientSerializer(data = request.data)
            serializer.context["hospital"] = request.user.hospital #pass context to serializer
            if serializer.is_valid():
                serializer.save()
                context['data'] = serializer.data
                context['message'] = _(f'Account: {serializer.data["email"]} created!') 
                return Response(context, status = status.HTTP_201_CREATED)
            context ['error'] = serializer.errors
        except Exception as e:
            context['error'] = e
        context['message'] = _('Patient Account was not created!')   
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk):
        context = {}
        data = request.data
        if len(data) == 0:
            context['error'] = {_("only ID supplied!")} 
            return Response(context, status = status.HTTP_400_BAD_REQUEST)     
        try:
            try:      
                patient_data = self.queryset.get(id = pk, hospital = request.user.hospital)
            except Patient.DoesNotExist:
                context['error'] = {"id": [_(f"ID: {pk} does not exist!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)

            serializer = PatientSerializer(patient_data, data = data, partial = True)
            serializer.context["hospital"] = request.user.hospital
            
            if serializer.is_valid():
                serializer.save()
                context['data'] = serializer.data
                context['message'] =  _(f'Staff: {serializer.data["id"]} updated!')
                return Response(context, status = status.HTTP_200_OK) 
            context ['error'] = serializer.errors
        except Exception as e:
            context['error'] = e
        context['message'] = _('Staff was not updated!')
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk):
        context = {}
        try:
            try:     
                patient_data = self.queryset.get(id = pk, hospital = request.user.hospital)
            except Patient.DoesNotExist:
                context['error'] = {"id": [_(f"ID: {pk} does not exist!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)
            patient_data.delete()
            context['message'] =  _(f"Account: {pk} deleted!")
            return Response(context, status = status.HTTP_204_NO_CONTENT) 
        except Exception as e:
            context['error'] = e
        context['message'] = _('Account was not deleted!')
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

#-----------------------------------APPOINTMENT---------------------------------------------------
# #------------UI-----------------
# @cache_control(no_cache = True, must_revalidate = True, no_store = True)
# @login_required    
# def appointment_request(request):
#     return render(request, 'appointment.html') 

#------------API---------------
class AppointmentView(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    http_method_names = ['get', 'post', 'delete', 'put']
    permission_classes = [IsAuthenticated, IsRegistration]    
    
    def list(self, request):
        context = {}
        try:          
            columns = ['id','appointment_date', 'present', 'diagnosed', 'patient',"doctor",'department']
            date_columns = ['appointment_date']
            fk_columns = ['patient',"doctor",'department']
            appointment_date_start = request.query_params.get('appointment_date_start','').strip()
            appointment_date_end = request.query_params.get('appointment_date_end','').strip()
            date_filter = [appointment_date_start, appointment_date_end]
            #------------------
            appointment_data = pagination_datatable(Appointment, columns, **request.query_params, 
            hospital = request.user.hospital, date_columns = date_columns, fk_columns = fk_columns,
            date_filter = date_filter, date_col_filter = 'appointment_date')
            #------------------
            serializer = AppointmentSerializer(appointment_data['data'], many = True)
            context['data'] = serializer.data
            context['draw'] = appointment_data['draw']
            context['recordsTotal'] = appointment_data['recordsTotal']
            context['recordsFiltered'] = appointment_data['recordsFiltered']
            return Response(context, status = status.HTTP_200_OK)
        except Exception as e:
            context['error'] = e
            return Response(context, status = status.HTTP_404_NOT_FOUND)

    def retrieve(self, request, pk):
        context = {}
        try:
            try:     
                appointment_data = self.queryset.get(id = pk, hospital = request.user.hospital)
            except Appointment.DoesNotExist:
                context['error'] = {"id": [_(f"ID: {pk} does not exist!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)
            serializer = AppointmentSerializer(appointment_data)    
            context['data'] = serializer.data
            return Response(context, status = status.HTTP_200_OK) 
        except Exception as e:
            context['error'] = e
        context['message'] = _('Appointment was not retrieved!')
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

    def create(self, request):
        context = {}
        data = request.data
        try:
            department_id = data.get('department')
            try:      
                Account.objects.get(id = data.get('doctor'), 
                                    department__id = department_id, roles__name = 'doctor')
            except Account.DoesNotExist:
                context['error'] = {"doctor": [_(f"This doctor is not in Department:{department_id}")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)
            
            appointment_date = data.get("appointment_date")
            doctor_id = data.get('doctor')
            patient_id = data.get('patient')

            try:
                appointment_date = datetime.strptime(appointment_date, "%Y-%m-%d").date()
                if appointment_date < datetime.now().date():
                    context['error'] = {"date": [_("You cannot have appointment in past, invent Time Machine!")]} 
                    return Response(context, status = status.HTTP_400_BAD_REQUEST)
                appointment_date = appointment_date.strftime("%Y-%m-%d")                    
            except Exception:
                context['error'] = {"date": [_("Not in format yyyy-mm-dd or incorrect date!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)
            
            try:
                doctor_availability(department_id,appointment_date,request.user.hospital).get(id = doctor_id)
            except Account.DoesNotExist:
                context['error'] = {"doctor": [_("Doctor is not available!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)

            
            total_appoint = self.queryset.filter(doctor__id = doctor_id, appointment_date = appointment_date)    
            total_appoint_count = total_appoint.count()

            total_appoint_possible = 6
            if total_appoint_count >= total_appoint_possible:
                context['error'] = {"doctor": [_(f"Doctor already have {total_appoint_possible} appointments on {appointment_date}!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)
            elif total_appoint == 0: pass    
            else:    
                try:
                    total_appoint.get(patient__id = patient_id, department__id = department_id)
                    context['error'] = {"id": [_("Same Appointment can't exist twice!")]} 
                    return Response(context, status = status.HTTP_400_BAD_REQUEST)                
                except Appointment.DoesNotExist:
                    pass                

            serializer = AppointmentSerializer(data = data)
            serializer.context["hospital"] = request.user.hospital #pass context to serializer
            if serializer.is_valid():
                serializer.save()
                context['data'] = serializer.data
                context['message'] = _(f'Appointment created!') 
                return Response(context, status = status.HTTP_201_CREATED)
            context ['error'] = serializer.errors
        except Exception as e:
            context['error'] = e
        context['message'] = _('Appointment was not created!')   
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk):
        context = {}
        data = request.data    
        try:
            try:      
                appointment_data = self.queryset.get(id = pk, hospital = request.user.hospital)
            except Appointment.DoesNotExist:
                context['error'] = {"id": [_(f"ID: {pk} does not exist!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)

            #--------------
            department_id = data.get('department')
            try:      
                Account.objects.get(id = data.get('doctor'), 
                                    department__id = department_id, roles__name = 'doctor')
            except Account.DoesNotExist:
                context['error'] = {"doctor": [_(f"This doctor is not in Department:{department_id}")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)
            
            appointment_date = data.get("appointment_date")
            doctor_id = data.get('doctor')
            patient_id = data.get('patient')

            try:
                appointment_date = datetime.strptime(appointment_date, "%Y-%m-%d").date()
                if appointment_date < datetime.now().date():
                    context['error'] = {"date": [_("You cannot have appointment in past, invent Time Machine!")]} 
                    return Response(context, status = status.HTTP_400_BAD_REQUEST)
                appointment_date = appointment_date.strftime("%Y-%m-%d")                    
            except Exception:
                context['error'] = {"date": [_("Not in format yyyy-mm-dd or incorrect date!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)
            
            try:
                doctor_availability(department_id,appointment_date,request.user.hospital).get(id = doctor_id)
            except Account.DoesNotExist:
                context['error'] = {"doctor": [_("Doctor is not available!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)

            
            total_appoint = self.queryset.filter(doctor__id = doctor_id, appointment_date = appointment_date)    
            total_appoint_count = total_appoint.count()

            total_appoint_possible = 6

            if total_appoint_count >= total_appoint_possible and (appointment_data.doctor.id != doctor_id or appointment_data.appointment_date.strftime("%Y-%m-%d") != appointment_date):
                context['error'] = {"doctor": [_(f"Doctor already have {total_appoint_possible} appointments on {appointment_date}!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)
            elif total_appoint == 0: pass    
            else:    
                try:
                    total_appoint.get(patient__id = patient_id, department__id = department_id)
                    context['error'] = {"id": [_("Already this appointment exists!")]} 
                    return Response(context, status = status.HTTP_400_BAD_REQUEST)                
                except Appointment.DoesNotExist:
                    pass                
            #--------------

            serializer = AppointmentSerializer(appointment_data, data = data)
            serializer.context["hospital"] = request.user.hospital
            
            if serializer.is_valid():
                serializer.save()
                context['data'] = serializer.data
                context['message'] =  _(f'Appointment: {serializer.data["id"]} updated!')
                return Response(context, status = status.HTTP_200_OK) 
            context ['error'] = serializer.errors
        except Exception as e:
            context['error'] = e
        context['message'] = _('Appointment was not updated!')
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk):
        context = {}
        try:
            try:     
                appointment_data = self.queryset.get(id = pk, hospital = request.user.hospital)
            except Appointment.DoesNotExist:
                context['error'] = {"id": [_(f"ID: {pk} does not exist!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)
            appointment_data.delete()
            context['message'] =  _(f"Appointment: {pk} deleted!")
            return Response(context, status = status.HTTP_204_NO_CONTENT) 
        except Exception as e:
            context['error'] = e
        context['message'] = _('Appointment was not deleted!')
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

    @action(detail = False, methods = ['get'])
    def doctor_dept(self, request):
        context = {}
        try:
            department_id =  request.query_params.get('department', None)
            if department_id:
                account_data = Account.objects.filter(roles__name = 'doctor',department__id = department_id, hospital = request.user.hospital)
                serializer = DoctorSerializer(account_data, many = True)
                context['data'] = serializer.data
                return Response(context, status = status.HTTP_200_OK)
        except Exception as e:
            context['error'] = e
        return Response(context, status = status.HTTP_400_BAD_REQUEST)   
        

#-----------------------------------TOKEN---------------------------------------------------
# #------------UI-----------------
# @cache_control(no_cache = True, must_revalidate = True, no_store = True)
# @login_required    
# def token_request(request):
#     return render(request, 'token.html') 

#------------API---------------
class TokenView(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = TokenSerializer
    http_method_names = ['get', 'patch']
    permission_classes = [IsAuthenticated, IsRegistration]

      
    def list(self, request):
        context = {}
        try:          
            columns = ['id', 'present', 'patient', "doctor", 'department']
            fk_columns = ['patient',"doctor",'department']
            #------------------
            context['draw'] = int(request.query_params.get('draw', None)) #draw counter to handle async 
            rows_per_page = int(request.query_params.get('length', None)) #row length that we select in dropdown
            start_index = int(request.query_params.get('start', None)) #starting index
            search_value = request.query_params.get('search[value]', '').strip() #search value

            #--------data--------
            today = datetime.now().date().strftime("%Y-%m-%d")
            context['data'] = self.queryset.filter(hospital = request.user.hospital, appointment_date = today)
            context['recordsTotal'] = context['data'].count() #Total Record count
            search_condition = get_conditions(search_value, columns, [], fk_columns)

            if search_condition:
                context['data'] = context['data'].filter(search_condition)

            context['recordsFiltered'] = context['data'].count() #Filtered record count
            context['data'] = context['data'].order_by('-present', 'id')[start_index : (start_index + rows_per_page)] #One Page Data
            #------------------
            serializer = TokenSerializer(context['data'], many = True)
            context['data'] = serializer.data
            return Response(context, status = status.HTTP_200_OK)
        except Exception as e:
            context['error'] = e
            return Response(context, status = status.HTTP_404_NOT_FOUND)

    def retrieve(self, request, pk):
        context = {}
        try:
            try:
                today = datetime.now().date().strftime("%Y-%m-%d")     
                appointment_data = self.queryset.get(id = pk, hospital = request.user.hospital, appointment_date = today)
            except Appointment.DoesNotExist:
                context['error'] = {"id": [_(f"ID: {pk} does not exist!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)
            serializer = AppointmentSerializer(appointment_data)    
            context['data'] = serializer.data
            return Response(context, status = status.HTTP_200_OK) 
        except Exception as e:
            context['error'] = e
        context['message'] = _('Token was not retrieved!')
        return Response(context, status = status.HTTP_400_BAD_REQUEST)


    def partial_update(self, request, pk):
        context = {}
        data = request.data    
        try:
            if data.get('present', None) == None:
                context['error'] = {"present": [_("This is required field")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)
            try:
                today = datetime.now().date().strftime("%Y-%m-%d")      
                appointment_data = self.queryset.get(id = pk, hospital = request.user.hospital, appointment_date = today)
            except Appointment.DoesNotExist:
                context['error'] = {"id": [_(f"There is no Appointment: {pk} for today!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)

            serializer = TokenSerializer(appointment_data, data = data, partial = True)
            serializer.context["hospital"] = request.user.hospital
            
            if serializer.is_valid():
                serializer.save()
                context['data'] = serializer.data
                context['message'] =  _(f'Appointment: {serializer.data["id"]} updated!')
                return Response(context, status = status.HTTP_200_OK) 
            context ['error'] = serializer.errors
        except Exception as e:
            context['error'] = e
        context['message'] = _('Appointment was not updated!')
        return Response(context, status = status.HTTP_400_BAD_REQUEST)
