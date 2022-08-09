from django.conf import settings
from django.contrib.auth import authenticate
from accounts.models import OTP, Account, Hospital
from accounts.serializers import AdminAccountSerializer, ForgetPasswordSerializer, LoginSerializer, OTPSerializer
from rest_framework.response import Response
from rest_framework import status, viewsets
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.tokens import RefreshToken, OutstandingToken, BlacklistedToken
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from random import randint
from django.core.mail import send_mail
from datetime import datetime, timedelta
# Create your views here.

#--------------------------------------LOGIN_REGISTER------------------------------------------------

#------------API---------------

class LoginRegisterView(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AdminAccountSerializer
    http_method_names = ['post']        

    def create(self, request):
        context = {}
        try:
            if not request.data.get('hospital'): 
                context['error'] = {"hospital": [_(f"Hospital name cannot be blank!")]} 
                return Response(context, status = status.HTTP_400_BAD_REQUEST)      
            hospital_name = request.data.get('hospital').lower()
            hospital, created = Hospital.objects.get_or_create(name = hospital_name)
            if created:
                request.data['hospital'] = hospital.id #return Hospital Object to store in Hospital field automatically
            else: #hospital is created, but account has not yet created. (case encountered : error in password validation)
                try:
                    Account.objects.get(hospital = hospital)
                    context['error'] = {"hospital": [_(f"Admin for {hospital_name} already exists!")]} 
                    return Response(context, status = status.HTTP_400_BAD_REQUEST) 
                except Account.DoesNotExist: #No admin assigned to that hospital
                    request.data['hospital'] = hospital.id
            serializer = AdminAccountSerializer(data = request.data)
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

    def login(self, request):
        context = {}
        serializer = LoginSerializer(data = request.data)
        if serializer.is_valid():
            user = authenticate(username = request.data['username'], password = request.data['password'])
            if user is not None:
                refresh = RefreshToken.for_user(user)
                context["refresh"] = str(refresh)
                context["access"] = str(refresh.access_token)
                return Response(context, status = status.HTTP_201_CREATED)
            else:
                context["message"] = _('Invalid email/mobile or password')
                return Response(context, status = status.HTTP_401_UNAUTHORIZED)
        else:
            context["message"] = serializer.errors
            return Response(context, status = status.HTTP_401_UNAUTHORIZED)

    def mail_otp(self, request):
        context = {}
        serializer = OTPSerializer(data = request.data)
        if serializer.is_valid():
            username = request.data.get('username')
            try:
                account = Account.objects.get(Q(email = username) | Q(mobile = username))
                otp = str(randint(100000, 999999))
                otp_model = OTP(account = account, otp = otp)
                otp_model.save()
                email_from = settings.EMAIL_HOST_USER
                send_mail('OTP (forget password)',
                    f'OTP: {otp}',
                    email_from,
                    [account.email],
                    fail_silently=False,
                )
                context["message"] = _('OTP MAILED!')
                return Response(context, status = status.HTTP_200_OK)                
            except Account.DoesNotExist:    
                context["message"] = _('Username does not exists')
                return Response(context, status = status.HTTP_401_UNAUTHORIZED)
            except:
                context["message"] = _('OTP was not mailed!')
                return Response(context, status = status.HTTP_400_BAD_REQUEST)    
        else:
            context["message"] = serializer.errors
            return Response(context, status = status.HTTP_401_UNAUTHORIZED)
    
    def forget_password(self, request):
        context = {}
        data = request.data
        serializer = ForgetPasswordSerializer(data = data)
        if serializer.is_valid():
            try:
                username = data.get("username")
                account = Account.objects.get(Q(email = username) | Q(mobile = username))
                five_minutes_ago = datetime.now() + timedelta(minutes = -5)
                otp_data = OTP.objects.get(account = account, generated_time__gte = five_minutes_ago)
                if otp_data.otp == data.get("otp"):
                    account.set_password(data.get("password"))
                    account.save()
                    otp = str(randint(100000, 999999))
                    otp_data.otp = otp #change otp, so that previous otp becomes invalid
                    otp_data.save() 
                    context["message"] = _("Password Changed!")
                    return Response(context, status = status.HTTP_200_OK)                     
                else:
                    context["message"] = _("OTP didn't matched!")
                    return Response(context, status = status.HTTP_401_UNAUTHORIZED) 
            except Account.DoesNotExist:
                context["message"] = _('Username does not exists!')
                return Response(context, status = status.HTTP_401_UNAUTHORIZED)
            except OTP.DoesNotExist:
                context["message"] = _('OTP does not exists!')
                return Response(context, status = status.HTTP_401_UNAUTHORIZED)                       
        else:
            context["message"] = serializer.errors
            return Response(context, status = status.HTTP_401_UNAUTHORIZED)


class LogoutView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ['post']

    def logout(self, request):
        context = {}
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            context['message'] = _('Successfully logged out!') 
            return Response(context, status = status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            context['error'] = _('Already logged out!') 
            return Response(context, status = status.HTTP_400_BAD_REQUEST)

    def logout_all_devices(self, request):
        context = {}
        try:
            tokens = OutstandingToken.objects.filter(user_id=request.user.id)
            for token in tokens:
                BlacklistedToken.objects.get_or_create(token=token)
            context['message'] = _('Successfully logged out from all devices!') 
            return Response(context, status = status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            context['error'] = _('Already logged out from all devices!') 
            return Response(context, status = status.HTTP_400_BAD_REQUEST) 
   