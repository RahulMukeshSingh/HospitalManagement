from functools import reduce
from django.shortcuts import redirect, render
from django.urls import reverse
from accounts.models import Account, Department, Roles
from accounts.permissions import IsAdministrator
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
# from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from administration.serializers import AccountSerializer, DepartmentDropDownSerializer, DepartmentSerializer, DoctorSerializer, RolesDropDownSerializer, RolesSerializer, UpdatePasswordSerializer
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from accounts.models import Department
from rest_framework.decorators import action

# Create your views here.

#-----------------------------------COMMON FUNCTIONS---------------------------------------------------
def get_conditions(search_value, columns, date_columns = [], fk_columns = [], exclude = []):
    if not search_value: return None
    conditions = []
    for col in columns:
        if col in fk_columns:
            conditions.append(Q(**{col + "__name__icontains" : search_value}))
        elif col not in date_columns and col not in exclude: 
            conditions.append(Q(**{col + "__icontains" : search_value}))
    return reduce(lambda x,y : x | y, conditions)
    
def pagination_datatable(Model, columns, **kwargs):
    context = {}
    context['draw'] = int(kwargs.get('draw', None)[0]) #draw counter to handle async 
    rows_per_page = int(kwargs.get('length', None)[0]) #row length that we select in dropdown
    start_index = int(kwargs.get('start', None)[0]) #starting index
    search_value = (kwargs.get('search[value]', '')[0]).strip() #search value
    sort_column_index = int(kwargs.get('order[0][column]', None)[0]) #which column was sorted
    sort_direction = (kwargs.get('order[0][dir]', 'asc')[0]).strip() #contains values -> asc/desc
    sort_column_name = columns[sort_column_index]
    if sort_direction == 'desc': 
        sort_column_name = '-' + sort_column_name # - for descending
    #--------data--------
    context['data'] = Model.objects #queryset
    hospital = kwargs.get('hospital', None)
    date_columns = kwargs.get('date_columns', [])
    fk_columns = kwargs.get('fk_columns', [])
    date_filter = kwargs.get('date_filter',[])
    exclude = kwargs.get('exclude',[])
    date_col_filter = kwargs.get('date_col_filter','')
    if hospital:
        context['data'] = context['data'].filter(hospital = hospital)
    context['recordsTotal'] = context['data'].count() #Total Record count

    search_condition = get_conditions(search_value, columns, date_columns, fk_columns, exclude)
    if search_condition:
        context['data'] = context['data'].filter(search_condition)
    
    if date_filter:
        if date_filter[0] and date_filter[1]:
            context['data'] = context['data'].filter(**{date_col_filter + '__range' : date_filter})
        elif date_filter[0]:
            context['data'] = context['data'].filter(**{date_col_filter + '__gte' : date_filter[0]})
        elif date_filter[1]:
            context['data'] = context['data'].filter(**{date_col_filter + '__lte' : date_filter[1]})

    context['recordsFiltered'] = context['data'].count() #Filtered record count
    context['data'] = context['data'].order_by(sort_column_name)[start_index : (start_index + rows_per_page)] #One Page Data
    return context

#-----------------------------------DEPARTMENT---------------------------------------------------
# #------------UI-----------------
# @cache_control(no_cache = True, must_revalidate = True, no_store = True)
# @login_required    
# def department_request(request):
#     return render(request, 'department.html') 

#------------API---------------

class DepartmentView(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, IsAdministrator]
    
    def list(self, request):
        context = {}
        try:
            columns = ['id', "name", 'fees', 'date_created', "date_modified"]
            date_columns = ['date_created', "date_modified"]
            date_created_start = request.query_params.get('date_created_start','').strip()
            date_created_end = request.query_params.get('date_created_end','').strip()
            date_filter = [date_created_start,date_created_end]
            #------------------
            department_data = pagination_datatable(Department, columns, **request.query_params, 
            hospital = request.user.hospital, date_columns = date_columns, date_filter = date_filter, 
            date_col_filter = 'date_created')            
            #------------------
            serializer = DepartmentSerializer(department_data['data'], many = True)
            context['data'] = serializer.data
            context['draw'] = department_data['draw']
            context['recordsTotal'] = department_data['recordsTotal']
            context['recordsFiltered'] = department_data['recordsFiltered']
            return Response(context, status = status.HTTP_200_OK)
        except Exception as e:
            context['error'] = e
            return Response(context, status = status.HTTP_404_NOT_FOUND)


    def retrieve(self, request, pk):
        context = {}
        try:
            try:     
                department_data = self.queryset.get(id = pk, hospital = request.user.hospital)
            except Department.DoesNotExist:
                context['error'] = {"id": [_(f"ID: {pk} does not exist!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)
            serializer = DepartmentSerializer(department_data)    
            context['data'] = serializer.data
            return Response(context, status = status.HTTP_200_OK) 
        except Exception as e:
            context['error'] = e
        context['message'] = _('Department was not retrieved!')
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

    @action(detail = False, methods = ['get'])
    def department_dropdown(self, request):
        context = {}
        try:
            department_data = self.queryset.filter(hospital = request.user.hospital)
            serializer = DepartmentDropDownSerializer(department_data, many = True)
            context['data'] = serializer.data
            return Response(context, status = status.HTTP_200_OK)
        except Exception as e:
            context['error'] = e
        return Response(context, status = status.HTTP_400_BAD_REQUEST)            

    def create(self, request):
        context = {}
        try:
            serializer = DepartmentSerializer(data = request.data)
            serializer.context["hospital"] = request.user.hospital #pass context to serializer
            if serializer.is_valid():
                serializer.save()
                context['data'] = serializer.data
                context['message'] = _(f'Department: {serializer.data["name"]} created!') 
                return Response(context, status = status.HTTP_201_CREATED)
            context ['error'] = serializer.errors
        except Exception as e:
            context['error'] = e
        context['message'] = _('Department was not be created!')   
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk):
        context = {}
        data = request.data 
        try:
            try:      
                departmentData = self.queryset.get(id = pk, hospital = request.user.hospital)
            except Department.DoesNotExist:
                context['error'] = {"id": [_(f"ID: {pk} does not exist!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)

            if departmentData.name == 'admin':
                context['error'] = {"id": [_("cannot modify admin!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)      

            serializer = DepartmentSerializer(departmentData, data = data, partial = True)
            serializer.context["hospital"] = request.user.hospital
            if serializer.is_valid():
                serializer.save()
                context['data'] = serializer.data
                context['message'] =  _(f'Department: {serializer.data["name"]} updated!')
                return Response(context, status = status.HTTP_200_OK) 
            context ['error'] = serializer.errors
        except Exception as e:
            context['error'] = e
        context['message'] = _('Department was not updated!')
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk):
        context = {}
        data = request.data
        try:
            try:      
                departmentData = self.queryset.get(id = pk, hospital = request.user.hospital)
            except Department.DoesNotExist:
                context['error'] = {"id": [_(f"ID: {pk} does not exist!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)

            if departmentData.name == 'admin':
                context['error'] = {"id": [_("cannot modify admin!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)                

            serializer = DepartmentSerializer(departmentData, data = data)
            serializer.context["hospital"] = request.user.hospital
            if serializer.is_valid():
                serializer.save()
                context['data'] = serializer.data
                context['message'] =  _(f'Department: {serializer.data["name"]} updated!')
                return Response(context, status = status.HTTP_200_OK) 
            context ['error'] = serializer.errors
        except Exception as e:
            context['error'] = e
        context['message'] = _('Department was not updated!')
        return Response(context, status = status.HTTP_400_BAD_REQUEST) 

    def destroy(self, request, pk):
        context = {}
        try:
            try:      
                departmentData = self.queryset.get(id = pk, hospital = request.user.hospital)
            except Department.DoesNotExist:
                context['error'] = {"id": [_(f"ID: {pk} does not exist!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)

            if departmentData.name == 'admin':
                context['error'] = {"id": [_("cannot modify admin!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)                 

            departmentData.delete()
            context['message'] =  _(f"Department: {pk} deleted!")
            return Response(context, status = status.HTTP_204_NO_CONTENT) 
        except Exception as e:
            context['error'] = e
        context['message'] = _('Department was not deleted!')
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

#--------------------------------------ROLES------------------------------------------------

# #------------UI-----------------
# @cache_control(no_cache = True, must_revalidate = True, no_store = True)
# @login_required    
# def roles_request(request):
#     return render(request, 'roles.html') 

#------------API---------------

class RolesView(viewsets.ModelViewSet):
    queryset = Roles.objects.all()
    serializer_class = RolesSerializer
    permission_classes = [IsAuthenticated, IsAdministrator]
    
    def list(self, request):
        context = {}
        try:
            columns = ['id', "name", 'date_created', "date_modified"]
            date_columns = ['date_created', "date_modified"]
            date_created_start = request.query_params.get('date_created_start','').strip()
            date_created_end = request.query_params.get('date_created_end','').strip()
            date_filter = [date_created_start,date_created_end]
            #------------------
            roles_data = pagination_datatable(Roles, columns, **request.query_params, 
            hospital = request.user.hospital, date_columns = date_columns, date_filter = date_filter,
            date_col_filter = 'date_created')
            #------------------
            serializer = RolesSerializer(roles_data['data'], many = True)
            context['data'] = serializer.data
            context['draw'] = roles_data['draw']
            context['recordsTotal'] = roles_data['recordsTotal']
            context['recordsFiltered'] = roles_data['recordsFiltered']
            return Response(context, status = status.HTTP_200_OK)
        except Exception as e:
            context['error'] = e
            return Response(context, status = status.HTTP_404_NOT_FOUND)

    def retrieve(self, request, pk):
        context = {}
        try:
            try:     
                roles_data = self.queryset.get(id = pk, hospital = request.user.hospital)
            except Roles.DoesNotExist:
                context['error'] = {"id": [_(f"ID: {pk} does not exist!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)
            serializer = RolesSerializer(roles_data)    
            context['data'] = serializer.data
            return Response(context, status = status.HTTP_200_OK) 
        except Exception as e:
            context['error'] = e
        context['message'] = _('Role was not retrieved!')
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

    @action(detail = False, methods = ['get'])
    def roles_dropdown(self, request):
        context = {}
        try:
            roles_data = self.queryset.filter(hospital = request.user.hospital)
            serializer = RolesDropDownSerializer(roles_data, many = True)
            context['data'] = serializer.data
            return Response(context, status = status.HTTP_200_OK)
        except Exception as e:
            context['error'] = e
        return Response(context, status = status.HTTP_400_BAD_REQUEST)            

    def create(self, request):
        context = {}
        try:
            serializer = RolesSerializer(data = request.data)
            serializer.context["hospital"] = request.user.hospital #pass context to serializer
            if serializer.is_valid():
                serializer.save()
                context['data'] = serializer.data
                context['message'] = _(f'Roles: {serializer.data["name"]} created!') 
                return Response(context, status = status.HTTP_201_CREATED)
            context ['error'] = serializer.errors
        except Exception as e:
            context['error'] = e
        context['message'] = _('Roles was not created!')   
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk):
        context = {}
        data = request.data
        try:
            try:      
                rolesData = self.queryset.get(id = pk, hospital = request.user.hospital)
            except Roles.DoesNotExist:
                context['error'] = {"id": [_(f"ID: {pk} does not exist!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)

            if rolesData.name == 'admin':
                context['error'] = {"id": [_("cannot modify admin!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)    

            serializer = RolesSerializer(rolesData, data = data, partial = True)
            serializer.context["hospital"] = request.user.hospital
            if serializer.is_valid():
                serializer.save()
                context['data'] = serializer.data
                context['message'] =  _(f'Roles: {serializer.data["name"]} updated!')
                return Response(context, status = status.HTTP_200_OK) 
            context ['error'] = serializer.errors
        except Exception as e:
            context['error'] = e
        context['message'] = _('Roles was not updated!')
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk):
        context = {}
        data = request.data
        try:
            try:      
                rolesData = self.queryset.get(id = pk, hospital = request.user.hospital)
            except Roles.DoesNotExist:
                context['error'] = {"id": [_(f"ID: {pk} does not exist!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)

            if rolesData.name == 'admin':
                context['error'] = {"id": [_("cannot modify admin!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)  

            serializer = RolesSerializer(rolesData, data = data)
            serializer.context["hospital"] = request.user.hospital
            if serializer.is_valid():
                serializer.save()
                context['data'] = serializer.data
                context['message'] =  _(f'Roles: {serializer.data["name"]} updated!')
                return Response(context, status = status.HTTP_200_OK) 
            context ['error'] = serializer.errors
        except Exception as e:
            context['error'] = e
        context['message'] = _('Roles was not updated!')
        return Response(context, status = status.HTTP_400_BAD_REQUEST) 

    def destroy(self, request, pk):
        context = {}
        try:
            try:      
                rolesData = self.queryset.get(id = pk, hospital = request.user.hospital)
            except Roles.DoesNotExist:
                context['error'] = {"id": [_(f"ID: {pk} does not exist!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)

            if rolesData.name == 'admin':
                context['error'] = {"id": [_("cannot modify admin!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)      

            rolesData.delete()
            context['message'] =  _(f"Roles: {pk} deleted!")
            return Response(context, status = status.HTTP_204_NO_CONTENT) 
        except Exception as e:
            context['error'] = e
        context['message'] = _('Roles was not deleted!')
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

#--------------------------------------STAFF------------------------------------------------

# #------------UI-----------------
# @cache_control(no_cache = True, must_revalidate = True, no_store = True)
# @login_required    
# def staff_request(request):
#     return render(request, 'staff.html') 

#------------API---------------

class StaffView(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']        
    permission_classes = [IsAuthenticated, IsAdministrator]
    
    def list(self, request):
        context = {}
        try:
            columns = ['id','name','email',"mobile",'roles','department','last_login','date_joined','is_active']
            date_columns = ['last_login','date_joined']
            fk_columns = ['roles','department']
            date_joined_start = request.query_params.get('date_joined_start','').strip()
            date_joined_end = request.query_params.get('date_joined_end','').strip()
            date_filter = [date_joined_start,date_joined_end]
            #------------------
            account_data = pagination_datatable(Account, columns, **request.query_params, 
            hospital = request.user.hospital, date_columns = date_columns, fk_columns = fk_columns, 
            date_filter = date_filter, date_col_filter = 'date_joined')
            #------------------
            serializer = AccountSerializer(account_data['data'], many = True)
            context['data'] = serializer.data
            context['draw'] = account_data['draw']
            context['recordsTotal'] = account_data['recordsTotal']
            context['recordsFiltered'] = account_data['recordsFiltered']
            return Response(context, status = status.HTTP_200_OK)
        except Exception as e:
            context['error'] = e
            return Response(context, status = status.HTTP_404_NOT_FOUND)

    def retrieve(self, request, pk):
        context = {}
        try:
            try:     
                account_data = self.queryset.get(id = pk, hospital = request.user.hospital)
            except Account.DoesNotExist:
                context['error'] = {"id": [_(f"ID: {pk} does not exist!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)
            serializer = AccountSerializer(account_data)    
            context['data'] = serializer.data
            return Response(context, status = status.HTTP_200_OK) 
        except Exception as e:
            context['error'] = e
        context['message'] = _('Account was not retrieved!')
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

    def create(self, request):
        context = {}
        try:
            serializer = AccountSerializer(data = request.data)
            serializer.context["hospital"] = request.user.hospital #pass context to serializer
            if serializer.is_valid():
                serializer.save()
                context['data'] = serializer.data
                context['message'] = _(f'Account: {serializer.data["email"]} created!') 
                return Response(context, status = status.HTTP_201_CREATED)
            context ['error'] = serializer.errors
        except Exception as e:
            context['error'] = e
        context['message'] = _('Account was not created!')   
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk):
        context = {}
        data = request.data
        if len(data) == 0:
            context['error'] = {_("only ID supplied!")} 
            return Response(context, status = status.HTTP_400_BAD_REQUEST)     
        try:
            try:      
                account_data = self.queryset.get(id = pk, hospital = request.user.hospital)
            except Account.DoesNotExist:
                context['error'] = {"id": [_(f"ID: {data.get('id')} does not exist!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)

            if data.get('password') or data.get('password1'):
                context['error'] = {"password": [_("Password Field not required!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)                


            serializer = AccountSerializer(account_data, data = data, partial = True)
            serializer.context["hospital"] = request.user.hospital
            
            if serializer.is_valid():
                #-------There must be atleast one admin!---------
                if data.get('roles'):
                    role_name = Roles.objects.get(id = data.get('roles')).name
                    if account_data.roles.name == 'admin' and role_name != 'admin':
                        count = self.queryset.filter(roles__name = 'admin', 
                                                    hospital__name = request.user.hospital).count()
                        if count == 1:
                            context['error'] = {"id": [_(f"There must be atleast one admin!")]} 
                            return Response(context, status = status.HTTP_400_BAD_REQUEST)    
                #-------------------------------------------------
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
                account_data = self.queryset.get(id = pk, hospital = request.user.hospital)
            except Account.DoesNotExist:
                context['error'] = {"id": [_(f"ID: {pk} does not exist!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)
            if account_data.roles.name == 'admin':
                count = Account.objects.filter(roles__name = 'admin', hospital__name = request.user.hospital).count()
                if count == 1:
                    context['error'] = {"id": [_(f"There must be atleast one admin!")]} 
                    return Response(context, status = status.HTTP_400_BAD_REQUEST)
            account_data.delete()
            context['message'] =  _(f"Account: {pk} deleted!")
            return Response(context, status = status.HTTP_204_NO_CONTENT) 
        except Exception as e:
            context['error'] = e
        context['message'] = _('Account was not deleted!')
        return Response(context, status = status.HTTP_400_BAD_REQUEST)

    @action(detail = True, methods = ['patch'])
    def update_password(self, request, pk):
        context = {}
        data = request.data
        try:
            try:      
                account = self.queryset.get(id = pk, hospital = request.user.hospital)
            except Account.DoesNotExist:
                context['error'] = {"id": [_(f"ID: {pk} does not exist!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)
            serializer = UpdatePasswordSerializer(data = data)
            if serializer.is_valid():
                account.set_password(data.get("password"))
                account.save()
                context['message'] =  _('Password Updated')
                return Response(context, status = status.HTTP_200_OK) 
            context ['error'] = serializer.errors
        except Exception as e:
            context['error'] = e
        context['message'] = _('Password was not updated!')
        return Response(context, status = status.HTTP_400_BAD_REQUEST) 

#--------------------------------------------------------------------------------------

'''
@cache_control(no_cache = True, must_revalidate = True, no_store = True)
@login_required   
def department_add_request(request):
    context = {}
    if request.method == 'POST':
        dept_add_form = DepartmentAddForm(request.POST, hospital = request.user.hospital)
        if dept_add_form.is_valid():
            dept_add_form.save()
            messages.success(request, _('Department added successfully!'))
            return redirect(reverse('administration:department'))
        else:
            context['dept_add_form'] = dept_add_form #Validation Errors
    else:
        dept_add_form = DepartmentAddForm()
        context['dept_add_form'] = dept_add_form
    return render(request, 'department_add.html', context = context)
'''