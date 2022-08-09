from bisect import bisect_left
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, viewsets
from accounts.models import Account
from administration.serializers import DoctorSerializer
from administration.views import get_conditions, pagination_datatable
from django.utils.translation import gettext_lazy as _
from accounts.permissions import IsDoctor, IsRegistrationOrDoctor
from dispensary.models import Medicine
from dispensary.serializers import MedicineSerializer
from doctor.models import Diagnosis, DoctorAvailability
from doctor.serializers import DiagnosisSerializer, DoctorAvailabilitySerializer
from datetime import datetime
from registration.models import Appointment
from registration.serializers import AppointmentSerializer, TokenSerializer

# Create your views here.
#-----------------------------------DOCTOR_AVAILABILITY METHODS---------------------------------------------------   

def doctor_availability(department_id, appointment_date, hospital):
    doctors_dept = Account.objects.filter(department__id = department_id, roles__name = 'doctor', hospital = hospital)
    available_doctors_id = DoctorAvailability.objects.exclude(doctor__in = doctors_dept, not_available__date__contains = appointment_date).values_list('doctor')
    return doctors_dept.filter(id__in = available_doctors_id).order_by('id')   

#-----------------------------------DOCTOR_AVAILABILITY---------------------------------------------------   

#------------API---------------   
class DoctorAvailabilityView(viewsets.ModelViewSet):
    queryset = DoctorAvailability.objects.all()
    serializer_class = DoctorAvailabilitySerializer
    http_method_names = ['get', 'post', 'delete']
    permission_classes = [IsAuthenticated, IsRegistrationOrDoctor]
    
    def list(self, request):
        context = {}
        try: 
            doctor_avail_data = self.queryset.filter(doctor__id = request.user.id)
            serializer = DoctorAvailabilitySerializer(doctor_avail_data, many = True)
            context['data'] = serializer.data
            return Response(context, status = status.HTTP_200_OK)
        except Exception as e:
            context['error'] = e
            return Response(context, status = status.HTTP_404_NOT_FOUND)

    def create(self, request):
        context = {}
        not_avail_date = request.data.get('date')
        if not not_avail_date:
            context['error'] = {"date": [_("No Date!")]} 
            return Response(context, status = status.HTTP_400_BAD_REQUEST)
        try:
            not_avail_date = datetime.strptime(not_avail_date, "%Y-%m-%d").date()
            if not_avail_date < datetime.now().date():
                context['error'] = {"date": [_("You cannot have holiday in past, invent Time Machine!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)
            not_avail_date = not_avail_date.strftime("%Y-%m-%d")                    
        except Exception:
            context['error'] = {"date": [_("Not in format yyyy-mm-dd or incorrect date!")]} 
            return Response(context, status = status.HTTP_400_BAD_REQUEST)
        data = {}
        data['doctor'] = request.user.id
        not_available = {}
        not_available['date'] = []
        try:
            try: #Append date
                doctor_avail_data = self.queryset.get(doctor__id = request.user.id)
                not_available['date'] = doctor_avail_data.not_available['date'][:] #slicing for shallow copy
                insert_index = bisect_left(not_available['date'], not_avail_date)
                if insert_index != len(not_available['date']) and not_available['date'][insert_index] == not_avail_date:
                        context['error'] = {"date": [_("Already Exists!")]} 
                        return Response(context, status = status.HTTP_400_BAD_REQUEST)                        
                not_available['date'].insert(insert_index, not_avail_date)
                data['not_available'] = not_available
                serializer = DoctorAvailabilitySerializer(doctor_avail_data, data = data)
            except DoctorAvailability.DoesNotExist: #Create
                not_available['date'].append(not_avail_date)
                data['not_available'] = not_available   
                serializer = DoctorAvailabilitySerializer(data = data)
            serializer.context["hospital"] = request.user.hospital
            if serializer.is_valid():
                serializer.save()
                context['data'] = serializer.data
                context['message'] = _(f'Holiday added!') 
                return Response(context, status = status.HTTP_201_CREATED)
            context ['error'] = serializer.errors
        except Exception as e:
            context['error'] = e
        context['message'] = _('Holiday could not be added!')   
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, date_delete = None):
        context = {}
        data = {}
        data['doctor'] = request.user.id
        not_available = {}
        not_available['date'] = []
        if not date_delete:
            context['error'] = {"date": [_("No Date Provided to delete!")]} 
            return Response(context, status = status.HTTP_400_BAD_REQUEST)
        try:
            date_delete = datetime.strptime(date_delete, "%Y-%m-%d").date().strftime("%Y-%m-%d")
        except Exception:
            context['error'] = {"date": [_("Not in format yyyy-mm-dd or incorrect date!")]} 
            return Response(context, status = status.HTTP_400_BAD_REQUEST)    
        try:
            try:     
                doctor_avail_data = self.queryset.get(doctor__id = request.user.id)
                not_available['date'] = doctor_avail_data.not_available['date'][:] #slicing for shallow copy
                delete_index = bisect_left(not_available['date'], date_delete)
                if delete_index != len(not_available['date']) and not_available['date'][delete_index] == date_delete:
                    not_available['date'].pop(delete_index)
                    data['not_available'] = not_available     
                    serializer = DoctorAvailabilitySerializer(doctor_avail_data, data = data) 
                else:
                    context['error'] = {"date": [f"date: {date_delete} does not exists!"]} 
                    return Response(context, status = status.HTTP_400_BAD_REQUEST)  
            except DoctorAvailability.DoesNotExist:
                context['error'] = {"date": [_("No Holidays are recorded!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)
            serializer.context["hospital"] = request.user.hospital
            if serializer.is_valid():
                serializer.save()
                context['data'] = serializer.data
                context['message'] =  _(f"date: {date_delete} deleted!")
                return Response(context, status = status.HTTP_204_NO_CONTENT)
            context ['error'] = serializer.errors     
        except Exception as e:
            context['error'] = e
        context['message'] = _(f"date: {date_delete} not deleted!")
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

    @action(detail = False, methods = ['get'])
    def get_doctors_availability(self, request):
        context = {}
        try:
            dept_no = request.query_params.get('dept_no', None)
            appointment_date = request.query_params.get('appointment_date', None)

            try:
                appointment_date = datetime.strptime(appointment_date, "%Y-%m-%d").date()
                appointment_date = appointment_date.strftime("%Y-%m-%d")                    
            except Exception:
                context['error'] = {"date": [_("Not in format yyyy-mm-dd or incorrect date!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)

            available_doctors = doctor_availability(dept_no,appointment_date, request.user.hospital)
            serializer = DoctorSerializer(available_doctors, many = True)
            context['data'] = serializer.data
            return Response(context, status = status.HTTP_200_OK)
        except Exception as e:
            context['error'] = e
            return Response(context, status = status.HTTP_404_NOT_FOUND)


#-----------------------------------DOCTOR_APPOINTMENT---------------------------------------------------   

#------------API---------------   
class DoctorAppointmentView(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = DoctorAvailabilitySerializer
    http_method_names = ['get']
    permission_classes = [IsAuthenticated, IsDoctor]
    
        
    def list(self, request):
        context = {}
        try:          
            columns = ['id','appointment_date', 'present', 'diagnosed', 'patient',"doctor",'department']
            date_columns = ['appointment_date']
            fk_columns = ['patient',"doctor",'department']
            appointment_date_start = request.query_params.get('appointment_date_start','').strip()
            appointment_date_end = request.query_params.get('appointment_date_end','').strip()
            date_filter = [appointment_date_start, appointment_date_end]
            hospital = request.user.hospital
            date_col_filter = 'appointment_date'
            #------------------
            context['draw'] = int(request.query_params.get('draw', None)) #draw counter to handle async 
            rows_per_page = int(request.query_params.get('length', None)) #row length that we select in dropdown
            start_index = int(request.query_params.get('start', None)) #starting index
            search_value = request.query_params.get('search[value]', '').strip() #search value
            sort_column_index = int(request.query_params.get('order[0][column]', None)[0]) #which column was sorted
            sort_direction = (request.query_params.get('order[0][dir]', 'asc')[0]).strip() #contains values -> asc/desc
            sort_column_name = columns[sort_column_index]
            if sort_direction == 'desc': 
                sort_column_name = '-' + sort_column_name # - for descending
            #--------data--------
            context['data'] = self.queryset #queryset
            if hospital:
                context['data'] = context['data'].filter(hospital = hospital, doctor = request.user)
            context['recordsTotal'] = context['data'].count() #Total Record count

            search_condition = get_conditions(search_value, columns, date_columns, fk_columns)
            if search_condition:
                context['data'] = context['data'].filter(search_condition)

            if date_filter[0] and date_filter[1]:
                context['data'] = context['data'].filter(**{date_col_filter + '__range' : date_filter})
            elif date_filter[0]:
                context['data'] = context['data'].filter(**{date_col_filter + '__gte' : date_filter[0]})
            elif date_filter[1]:
                context['data'] = context['data'].filter(**{date_col_filter + '__lte' : date_filter[1]})

            context['recordsFiltered'] = context['data'].count() #Filtered record count
            context['data'] = context['data'].order_by(sort_column_name)[start_index : (start_index + rows_per_page)] #One Page Data
            #------------------
            serializer = AppointmentSerializer(context['data'], many = True)
            context['data'] = serializer.data
            return Response(context, status = status.HTTP_200_OK)
        except Exception as e:
            context['error'] = e
            return Response(context, status = status.HTTP_404_NOT_FOUND)

    def retrieve(self, request, pk):
        context = {}
        try:
            try:     
                appointment_data = self.queryset.get(id = pk, hospital = request.user.hospital, doctor = request.user)
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

#-----------------------------------DOCTOR_TOKEN---------------------------------------------------   

#------------API---------------   
class DoctorTokenView(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = TokenSerializer
    http_method_names = ['get', 'patch']
    permission_classes = [IsAuthenticated, IsDoctor]

      
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
            context['data'] = self.queryset.filter(hospital = request.user.hospital, appointment_date = today, doctor = request.user)
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
                appointment_data = self.queryset.get(id = pk, hospital = request.user.hospital, appointment_date = today, doctor = request.user)
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

#diagnosed = True Update
    def partial_update(self, request, pk):
        context = {}
        data = request.data    
        try:
            diagnosed = data.get('diagnosed', None)
            if diagnosed == None:
                context['error'] = {"diagnosed": [_("This is required field")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)
            try:
                today = datetime.now().date().strftime("%Y-%m-%d")      
                appointment_data = self.queryset.get(id = pk, hospital = request.user.hospital, appointment_date = today, doctor = request.user)
            except Appointment.DoesNotExist:
                context['error'] = {"id": [_(f"There is no Appointment: {pk} for today!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)

            serializer = TokenSerializer(appointment_data, data = data, partial = True)
            serializer.context["hospital"] = request.user.hospital
            
            if serializer.is_valid():
                serializer.save()
                if diagnosed:
                    context['message'] =  _(f'Appointment: {serializer.data["id"]} diagnosed!')
                else:
                    context['message'] =  _(f'Appointment: {serializer.data["id"]} not diagnosed!')
                return Response(context, status = status.HTTP_200_OK) 
            context ['error'] = serializer.errors
        except Exception as e:
            context['error'] = e
        context['message'] = _('Appointment was not diagnosed!')
        return Response(context, status = status.HTTP_400_BAD_REQUEST)



#-----------------------------------DIAGNOSIS---------------------------------------------------   

#------------API--------------- 



class DiagnosisView(viewsets.ModelViewSet):
    queryset = Diagnosis.objects.all()
    serializer_class = DiagnosisSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = [IsAuthenticated, IsDoctor]    
    
    def list(self, request):
        context = {}
        try:          
            columns = ['id','appointment', 'diagnosis', 'symptoms', 'medicine']
            exclude = ['appointment'] 
            #It is not date column, but in order to avoid searching search_value in appointment (get_conditions()), I did this
            #------------------
            context['draw'] = int(request.query_params.get('draw', None)) #draw counter to handle async 
            rows_per_page = int(request.query_params.get('length', None)) #row length that we select in dropdown
            start_index = int(request.query_params.get('start', None)) #starting index
            search_value = request.query_params.get('search[value]', '').strip() #search value
            sort_column_index = int(request.query_params.get('order[0][column]', None)[0]) #which column was sorted
            sort_direction = (request.query_params.get('order[0][dir]', 'asc')[0]).strip() #contains values -> asc/desc
            sort_column_name = columns[sort_column_index]
            if sort_direction == 'desc': 
                sort_column_name = '-' + sort_column_name # - for descending
            #--------data--------
            context['data'] = self.queryset.filter(appointment__doctor = request.user, hospital = request.user.hospital)
            context['recordsTotal'] = context['data'].count() #Total Record count
            search_condition = get_conditions(search_value, columns, exclude = exclude)

            if search_condition:
                context['data'] = context['data'].filter(search_condition)
            
            context['recordsFiltered'] = context['data'].count() #Filtered record count
            context['data'] = context['data'].order_by(sort_column_name)[start_index : (start_index + rows_per_page)] #One Page Data
            #------------------
            serializer = DiagnosisSerializer(context['data'], many = True)
            context['data'] = serializer.data
            return Response(context, status = status.HTTP_200_OK)
        except Exception as e:
            context['error'] = e
            return Response(context, status = status.HTTP_404_NOT_FOUND)

    def retrieve(self, request, pk):
        context = {}
        try:
            try:     
                diagnosis_data = self.queryset.get(id = pk, appointment__doctor = request.user, hospital = request.user.hospital)
            except Diagnosis.DoesNotExist:
                context['error'] = {"id": [_(f"Diagnosis ID: {pk} does not exist!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)
            serializer = DiagnosisSerializer(diagnosis_data)    
            context['data'] = serializer.data
            return Response(context, status = status.HTTP_200_OK) 
        except Exception as e:
            context['error'] = e
        context['message'] = _('Diagnosis was not retrieved!')
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

    def create(self, request):
        context = {}
        data = request.data
        try:          
            serializer = DiagnosisSerializer(data = data)
            serializer.context["user"] = request.user #pass context to serializer
            if serializer.is_valid():
                serializer.save()
                context['data'] = serializer.data
                context['message'] = _(f'Diagnosis added!') 
                return Response(context, status = status.HTTP_201_CREATED)
            context ['error'] = serializer.errors
        except Exception as e:
            context['error'] = e
        context['message'] = _('Diagnosis was not added!')   
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk):
        context = {}
        data = request.data    
        try:
            try:      
                diagnosis_data = self.queryset.get(id = pk,  appointment__doctor = request.user, hospital = request.user.hospital)
            except Diagnosis.DoesNotExist:
                context['error'] = {"id": [_(f"ID: {pk} does not exist!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)

            serializer = DiagnosisSerializer(diagnosis_data, data = data, partial = True)
            serializer.context["user"] = request.user
            
            if serializer.is_valid():
                serializer.save()
                context['data'] = serializer.data
                context['message'] =  _(f'Diagnosis: {serializer.data["id"]} updated!')
                return Response(context, status = status.HTTP_200_OK) 
            context ['error'] = serializer.errors
        except Exception as e:
            context['error'] = e
        context['message'] = _('Diagnosis was not updated!')
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk):
        context = {}
        try:
            try:     
                diagnosis_data = self.queryset.get(id = pk,  appointment__doctor = request.user, hospital = request.user.hospital)
            except Diagnosis.DoesNotExist:
                context['error'] = {"id": [_(f"ID: {pk} does not exist!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)
            diagnosis_data.delete()
            context['message'] =  _(f"Diagnosis: {pk} deleted!")
            return Response(context, status = status.HTTP_204_NO_CONTENT) 
        except Exception as e:
            context['error'] = e
        context['message'] = _('Diagnosis was not deleted!')
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

    @action(detail = False, methods = ['get'])
    def available_medicine_list(self, request):
        context = {}
        try:
            name = request.query_params.get('name', None)
            medicine_data = None
            if name:
                medicine_data = Medicine.objects.filter(name__icontains = name, quantity__gt = 0,hospital = request.user.hospital)
            else:
                medicine_data = Medicine.objects.filter(quantity__gt = 0, hospital = request.user.hospital)
            serializer = MedicineSerializer(medicine_data, many = True)    
            context['data'] = serializer.data
            return Response(context, status = status.HTTP_200_OK) 
        except Exception as e:
            context['error'] = e
        return Response(context, status = status.HTTP_400_BAD_REQUEST)
