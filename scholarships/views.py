import csv
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse
from .models import StudentProfile, Scholarship, Application, Notification


def home(request):
    scholarships = Scholarship.objects.filter(is_active=True, deadline__gte=date.today())
    return render(request, 'scholarships/home.html', {'scholarships': scholarships})

def register_student(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        display_username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        prn = request.POST.get('prn_number', '').strip()
        course = request.POST.get('course', '').strip()
        year = request.POST.get('current_year', '').strip()
        percentage = request.POST.get('percentage', '').strip()
        income = request.POST.get('annual_income', '').strip()
        category = request.POST.get('category', '').strip()
        phone = request.POST.get('phone', '').strip()

        # Only PRN must be strictly unique; display username can repeat
        if StudentProfile.objects.filter(prn_number__iexact=prn).exists() or User.objects.filter(username__iexact=prn).exists():
            messages.error(request, "PRN Number is already registered!")
            return redirect('register')

        # Use PRN as the unique internal Django User.username, and save the chosen username in first_name/profile
        full_first_name = f"{first_name} ({display_username})" if display_username else first_name

        user = User.objects.create_user(
            username=prn,  # Guaranteed unique per student
            email=email,
            password=password,
            first_name=full_first_name,
            last_name=last_name
        )
        StudentProfile.objects.create(
            user=user,
            prn_number=prn,
            course=course,
            current_year=year,
            percentage=percentage,
            annual_income=income,
            category=category,
            phone=phone
        )
        Notification.objects.create(
            user=user,
            message=f"Welcome {first_name}! Use your PRN ({prn}) to log in anytime."
        )
        messages.success(request, f"Registration successful! Log in using your PRN Number '{prn}' (or Username if unique).")
        return redirect('login')

    return render(request, 'scholarships/register.html')


def login_view(request):
    if request.method == 'POST':
        login_id = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        # 1. Check direct match on PRN / Django username (e.g., admin 'aditi' or student PRN '26440')
        user = authenticate(request, username=login_id, password=password)

        # 2. If not found, check StudentProfile by PRN (case-insensitive)
        if user is None:
            profile = StudentProfile.objects.filter(prn_number__iexact=login_id).select_related('user').first()
            if profile:
                user = authenticate(request, username=profile.user.username, password=password)

        # 3. If still not found, check matching display usernames/first names and test password
        if user is None:
            matching_users = User.objects.filter(first_name__icontains=f"({login_id})")
            for candidate in matching_users:
                auth_user = authenticate(request, username=candidate.username, password=password)
                if auth_user is not None:
                    user = auth_user
                    break

        if user is not None:
            login(request, user)
            if user.is_staff:
                return redirect('admin_dashboard')
            return redirect('student_dashboard')
        else:
            messages.error(request, "Invalid PRN / Username or Password. Please try again.")
    return render(request, 'scholarships/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')


def check_eligibility(student, scholarship):
    """Automated Eligibility Checking Logic"""
    reasons = []
    if student.percentage < scholarship.min_percentage:
        reasons.append(f"Requires min {scholarship.min_percentage}% (You have {student.percentage}%)")
    if student.annual_income > scholarship.max_income:
        reasons.append(f"Income must be <= Rs.{scholarship.max_income}")
    if scholarship.allowed_category != "ALL" and student.category != scholarship.allowed_category:
        reasons.append(f"Restricted to {scholarship.allowed_category} category")
    return (len(reasons) == 0, reasons)


@login_required
def student_dashboard(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')

    student = get_object_or_404(StudentProfile, user=request.user)
    all_scholarships = Scholarship.objects.filter(is_active=True)
    applied_ids = Application.objects.filter(student=student).values_list('scholarship_id', flat=True)

    scholarship_list = []
    for sch in all_scholarships:
        eligible, reasons = check_eligibility(student, sch)
        scholarship_list.append({
            'obj': sch,
            'eligible': eligible,
            'reasons': reasons,
            'already_applied': sch.id in applied_ids
        })

    applications = Application.objects.filter(student=student).order_by('-applied_on')
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]

    return render(request, 'scholarships/student_dashboard.html', {
        'student': student,
        'scholarship_list': scholarship_list,
        'applications': applications,
        'notifications': notifications,
    })


@login_required
def apply_scholarship(request, scholarship_id):
    student = get_object_or_404(StudentProfile, user=request.user)
    scholarship = get_object_or_404(Scholarship, id=scholarship_id)

    eligible, reasons = check_eligibility(student, scholarship)
    if not eligible:
        messages.error(request, "You are not eligible for this scholarship.")
        return redirect('student_dashboard')

    if Application.objects.filter(student=student, scholarship=scholarship).exists():
        messages.warning(request, "You have already applied for this scholarship.")
        return redirect('student_dashboard')

    if request.method == 'POST':
        Application.objects.create(
            student=student,
            scholarship=scholarship,
            marksheet=request.FILES['marksheet'],
            income_certificate=request.FILES['income_certificate'],
            id_proof=request.FILES['id_proof'],
        )
        Notification.objects.create(
            user=request.user,
            message=f"Application submitted for '{scholarship.title}'. Status: Pending."
        )
        messages.success(request, "Application & documents submitted successfully!")
        return redirect('student_dashboard')

    return render(request, 'scholarships/apply_scholarship.html', {
        'student': student,
        'scholarship': scholarship
    })


def is_admin(user):
    return user.is_staff


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    if request.method == 'POST' and 'add_scholarship' in request.POST:
        Scholarship.objects.create(
            title=request.POST['title'],
            provider=request.POST['provider'],
            amount=request.POST['amount'],
            description=request.POST['description'],
            min_percentage=request.POST['min_percentage'],
            max_income=request.POST['max_income'],
            allowed_category=request.POST['allowed_category'],
            deadline=request.POST['deadline'],
        )
        messages.success(request, "New scholarship scheme published!")
        return redirect('admin_dashboard')

    applications = Application.objects.all().order_by('-applied_on')
    scholarships = Scholarship.objects.all().order_by('-created_at')

    stats = {
        'total_apps': applications.count(),
        'pending': applications.filter(status='Pending').count(),
        'approved': applications.filter(status='Approved').count(),
        'rejected': applications.filter(status='Rejected').count(),
    }

    return render(request, 'scholarships/admin_dashboard.html', {
        'applications': applications,
        'scholarships': scholarships,
        'stats': stats
    })


@login_required
@user_passes_test(is_admin)
def update_application_status(request, app_id):
    if request.method == 'POST':
        app = get_object_or_404(Application, id=app_id)
        new_status = request.POST['status']
        remarks = request.POST.get('admin_remarks', '')
        app.status = new_status
        app.admin_remarks = remarks
        app.save()

        Notification.objects.create(
            user=app.student.user,
            message=f"Update on '{app.scholarship.title}': Status changed to {new_status}."
        )
        messages.success(request, f"Application #{app.id} marked as {new_status}.")
    return redirect('admin_dashboard')


@login_required
@user_passes_test(is_admin)
def export_report_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="scholarship_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['App ID', 'Student Name', 'PRN', 'Category', 'Percentage', 'Scholarship', 'Amount (INR)', 'Status', 'Applied Date'])

    for app in Application.objects.select_related('student__user', 'scholarship').all():
        writer.writerow([
            app.id,
            app.student.user.get_full_name(),
            app.student.prn_number,
            app.student.category,
            app.student.percentage,
            app.scholarship.title,
            app.scholarship.amount,
            app.status,
            app.applied_on.strftime('%Y-%m-%d')
        ])
    return response
