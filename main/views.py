from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from .models import *
from .filters import PatientFilter
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.contrib.auth.decorators import login_required
# PatientFilter = OrderFilter

# Create your vie

def login(request):
    if request.user.is_authenticated:
        return redirect('/')
    else:
        if request.method == 'POST':
            username = request.POST['username']
            password = request.POST['password']
            user = auth.authenticate(username=username, password=password)
            if user is not None:
                auth.login(request, user)
                return redirect('/')
            else:
                messages.error(request, 'Invalid username or password')
                return redirect('login')
        else:
            return render(request, 'main/login.html')


def signup(request):
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 != password2:
            messages.error(request, 'Passwords do not match')
            return redirect('signup')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken')
            return redirect('signup')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return redirect('signup')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
        )
        user.is_staff = True
        user.save()
        messages.success(request, 'Account created successfully! Please login.')
        return redirect('login')
    else:
        return render(request, 'main/signup.html')


@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    return redirect('/')




def dashboard(request):
    patients = Patient.objects.all()
    patient_count = patients.count()
    patients_recovered = Patient.objects.filter(status="Recovered")
    patients_deceased = Patient.objects.filter(status="Deceased")
    deceased_count = patients_deceased.count()
    recovered_count = patients_recovered.count()
    
    beds = Bed.objects.all()
    total_beds = beds.count()
    beds_available = Bed.objects.filter(occupied=False).count()
    beds_occupied = Bed.objects.filter(occupied=True).count()
    
    bed_occupancy_pct = int((beds_occupied / total_beds * 100)) if total_beds > 0 else 0
    
    critical_patients = Patient.objects.filter(status="Critical")
    critical_count = critical_patients.count()
    
    doctors = Doctor.objects.all()
    doctors_count = doctors.count()
    
    recent_patients = Patient.objects.all().order_by('-id')[:5]
    
    context = {
        'patient_count': patient_count,
        'recovered_count': recovered_count,
        'beds_available': beds_available,
        'beds_occupied': beds_occupied,
        'total_beds': total_beds,
        'bed_occupancy_pct': bed_occupancy_pct,
        'deceased_count': deceased_count,
        'critical_patients': critical_patients,
        'critical_count': critical_count,
        'doctors': doctors,
        'doctors_count': doctors_count,
        'recent_patients': recent_patients,
        'beds': beds
    }
    return render(request, 'main/dashboard.html', context)

def add_patient(request):
    beds = Bed.objects.filter(occupied=False)
    doctors = Doctor.objects.all()
    if request.method == "POST":
        name = request.POST.get('name', '')
        phone_num = request.POST.get('phone_num', '')
        patient_relative_name = request.POST.get('patient_relative_name', '')
        patient_relative_contact = request.POST.get('patient_relative_contact', '')
        address = request.POST.get('address', '')
        symptoms = request.POST.getlist('symptoms')
        prior_ailments = request.POST.get('prior_ailments', '')
        bed_num_sent = request.POST.get('bed_num', '')
        
        try:
            bed_num = Bed.objects.get(bed_number=bed_num_sent)
        except Bed.DoesNotExist:
            bed_num = Bed.objects.filter(occupied=False).first()
            if not bed_num:
                bed_num = Bed.objects.first()
                
        dob = request.POST.get('dob')
        if not dob:
            dob = None
            
        status = request.POST.get('status', 'Critical')
        doctor_sent = request.POST.get('doctor', '')
        
        try:
            doctor = Doctor.objects.get(name=doctor_sent)
        except Doctor.DoesNotExist:
            if doctor_sent:
                doctor = Doctor.objects.create(name=doctor_sent)
            else:
                doctor = Doctor.objects.first()
                
        patient = Patient.objects.create(
            name=name,
            phone_num=phone_num,
            patient_relative_name=patient_relative_name,
            patient_relative_contact=patient_relative_contact, 
            address=address, 
            symptoms=symptoms, 
            prior_ailments=prior_ailments, 
            bed_num=bed_num,
            dob=dob, 
            doctor=doctor,
            status=status
        )
        patient.save()

        if bed_num:
            bed_num.occupied = True
            bed_num.save()
            
        id = patient.id
        return redirect(f"/patient/{id}")
        
    context = {
        'beds': beds,
        'doctors': doctors
    }
    return render(request, 'main/add_patient.html', context)

def patient(request, pk):
    patient_obj = Patient.objects.get(id=pk)
    doctors = Doctor.objects.all()
    if request.method == "POST":
        doctor_sent = request.POST.get('doctor', '')
        doctor_time = request.POST.get('doctor_time', '')
        doctor_notes = request.POST.get('doctor_notes', '')
        mobile = request.POST.get('mobile', '')
        mobile2 = request.POST.get('mobile2', '')
        relativeName = request.POST.get('relativeName', '')
        address  = request.POST.get('location', '')
        status = request.POST.get('status', '')
        symptoms_sent = request.POST.get('symptons', '')
        
        try:
            doctor = Doctor.objects.get(name=doctor_sent)
        except Doctor.DoesNotExist:
            if doctor_sent:
                doctor = Doctor.objects.create(name=doctor_sent)
            else:
                doctor = None
                
        patient_obj.phone_num = mobile
        patient_obj.patient_relative_contact = mobile2
        patient_obj.patient_relative_name = relativeName
        patient_obj.address = address
        patient_obj.doctor = doctor
        patient_obj.doctors_visiting_time = doctor_time
        patient_obj.doctors_notes = doctor_notes
        patient_obj.status = status
        
        if symptoms_sent:
            patient_obj.symptoms = [s.strip() for s in symptoms_sent.split(',') if s.strip()]
            
        patient_obj.save()
        
        if status in ['Recovered', 'Deceased'] and patient_obj.bed_num:
            bed = patient_obj.bed_num
            bed.occupied = False
            bed.save()
            
    context = {
        'patient': patient_obj,
        'doctors': doctors,
    }
    return render(request, 'main/patient.html', context)


def patient_list(request):
    patients = Patient.objects.all()

    # filtering
    myFilter = PatientFilter(request.GET, queryset=patients)

    patients = myFilter.qs
    context = {
        'patients': patients,
        'myFilter': myFilter
    }

    return render(request, 'main/patient_list.html', context)

'''
def autocomplete(request):
    if patient in request.GET:
        name = Patient.objects.filter(name__icontains=request.GET.get(patient))
        name = ['js', 'python']
        
        names = list()
        names.append('Shyren')
        print(names)
        for patient_name in name:
            names.append(patient_name.name)
        return JsonResponse(names, safe=False)
    return render (request, 'main/patient_list.html')
'''

def autosuggest(request):
    query_original = request.GET.get('term')
    queryset = Patient.objects.filter(name__icontains=query_original)
    mylist = []
    mylist += [x.name for x in queryset]
    return JsonResponse(mylist, safe=False)

def autodoctor(request):
    query_original = request.GET.get('term')
    queryset = Doctor.objects.filter(name__icontains=query_original)
    mylist = []
    mylist += [x.name for x in queryset]
    return JsonResponse(mylist, safe=False)

def info(request):
    return render(request, "main/info.html")