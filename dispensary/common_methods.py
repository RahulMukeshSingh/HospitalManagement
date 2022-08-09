from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER
from django.conf import settings
from django.core.mail import EmailMessage
from HospitalManagement.settings import MEDIA_ROOT
from dispensary.models import Transaction
from doctor.models import Diagnosis


def get_age(dob):
    dob = datetime.strptime(dob, "%Y-%m-%d")
    today = datetime.now()
    age = today.year - dob.year
    if dob.month > today.month: age -= 1
    elif dob.month == today.month and dob.day > today.day: age -= 1
    return age

def create_pdf(appointment_date, bill_id, patient_id, patient_name, patient_dob, patient_email, amount_paid, medicine_details, diagnosis_details, hospital_name, doctor_name, doctor_email): 
    pdf_location = f"{MEDIA_ROOT}BILLS/{patient_id}-Bill-{appointment_date}.pdf"
    doc = SimpleDocTemplate(pdf_location, pagesize=letter)
    flowables = []
    spacer = Spacer(1, 0.5 * inch)
    
    styles = getSampleStyleSheet()
    
    text_style = styles["Title"]
    text_style.fontSize = 30
    text_style.textColor = colors.gray
    flowables.append(Paragraph(hospital_name, text_style))
    flowables.append(Spacer(1, 0.25 * inch))

    center_style = styles['Normal']
    center_style.alignment = TA_CENTER
    details = []
    details.append(['BILL ID:', bill_id])
    details.append(['APPOINTMENT DATE:', appointment_date])
    details.append(['DIAGNOSED BY:', doctor_name])
    details.append(['DOCTOR EMAIL:', doctor_email])
    details.append(['PATIENT NAME:', patient_name])
    details.append(['AGE:', get_age(patient_dob)])
    details.append(['PATIENT EMAIL:', patient_email])
    table_style = TableStyle([
        ('TEXTCOLOR', (0, 0), (0, -1), colors.gray), #3rd and 4th parameters are start and end with each (col, row)
    ])
    table = Table(details)
    table.setStyle(table_style)
    flowables.append(table)
    flowables.append(spacer)

    text_style.fontSize = 15
    flowables.append(Paragraph("DIAGNOSIS", text_style))
    diagnosis = []
    diagnosis.append(['ID', 'Name', 'QUANTITY', 'DIRECTION'])

    for diagnosis_dict in diagnosis_details:
        diagnosis.append([diagnosis_dict['id'], diagnosis_dict['name'], diagnosis_dict['qty'], diagnosis_dict['direction']])
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.gray), #3rd and 4th parameters are start and end with each (col, row)
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ])
    table = Table(diagnosis)
    table.setStyle(table_style)
    flowables.append(table)
    flowables.append(spacer)
    
    flowables.append(Paragraph("BILL", text_style))
    bill = []
    bill.append(['ID', 'Name', 'QUANTITY', 'PRICE', 'DISCOUNT', 'TOTAL AMOUNT'])
    amount_payable = 0 
    for medicine in medicine_details["medicines"]:
        price = float(medicine['price'])
        qty = int(medicine['qty'])
        discount = float(medicine['discount_percent'])
        total_amount = price * (1 - (discount / 100)) * qty
        amount_payable += total_amount  
        bill.append([medicine['id'], medicine['name'], qty, price, discount, total_amount])

    amount_payable += float(medicine_details["Doctor Fees"])
    bill.append(['','','', '', 'Doctor Fees', medicine_details["Doctor Fees"]])
    bill.append(['','','','', 'Amount Payable', amount_payable])
    bill.append(['','','','', 'Amount Paid', amount_paid])
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.gray), #3rd and 4th parameters are start and end with each (col, row)
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (-2, -1), (-2, -1), colors.gray),
        ('TEXTCOLOR', (-2, -1), (-2, -1), colors.white)
        ])
    table = Table(bill)
    table.setStyle(table_style)
    flowables.append(table)

    doc.build(flowables)
    return pdf_location

def mail(appointment_date, pdf_location, patient_email, hospital_name):
    try:
        subject = f'DIAGNOSIS AND BILL FROM {hospital_name}'
        message = f'Diagnosis and Bill for appointment on {appointment_date} in {hospital_name}'
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [patient_email]
        mail = EmailMessage(subject, message, email_from, recipient_list)
        mail.attach_file(pdf_location)
        mail.send()
        return True
    except:
        return False    

def create_mail_pdf(bill_model):
    try:
        bill_id = bill_model.id
        hospital_name = bill_model.hospital.name
        medicine_details = bill_model.details
        appointment = bill_model.appointment
        appointment_date = appointment.appointment_date.strftime("%Y-%m-%d")  
        transaction = Transaction.objects.get(bill = bill_model)
        amount_paid = float(transaction.amount)
        patient = appointment.patient
        doctor = appointment.doctor
        patient_id = patient.id
        patient_name = patient.name
        patient_dob = patient.dob.strftime("%Y-%m-%d")
        patient_email = patient.email
        doctor_name = doctor.name
        doctor_email = doctor.email
        diagnosis_model = Diagnosis.objects.get(appointment = appointment)
        diagnosis_details = diagnosis_model.medicine

        pdf_location = create_pdf(appointment_date, bill_id, patient_id, patient_name, patient_dob, patient_email, 
        amount_paid, medicine_details, diagnosis_details, hospital_name, doctor_name, doctor_email)

        return mail(appointment_date, pdf_location, patient_email, hospital_name)
    except:
        return False
