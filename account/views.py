import random
import smtplib

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Checkbox
from django import forms
from .models import *
from django.core.mail import send_mail, BadHeaderError
import socket

from django.core.mail import EmailMultiAlternatives
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags


# from captcha.fields import ReCaptchaField
# from captcha.widgets import ReCaptchaV2Checkbox
# from django import forms

# Create a temporary form for validating the reCAPTCHA field
# class CaptchaForm(forms.Form):
#    recaptcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)

# UNCOMMENT THIS VIEW FOR LOGIN WITH RECAPTCHA - MAKE SURE TO DO CHANGES IN Login Html and Settings.py
# def user_login(request):
#     if request.method == 'POST':
#         username = request.POST['username']
#         password = request.POST['password']
#         recaptcha_response = request.POST.get('g-recaptcha-response')
#         form = CaptchaForm(request.POST)
#
#         if form.is_valid():
#             # Authenticate the user
#             user = authenticate(request, username=username, password=password)
#
#             if user is not None:
#                 # The user is valid, so log them in
#                 login(request, user)
#                 # Redirect to a success page or wherever you want
#                 return redirect('dashboard')
#             else:
#                 # Authentication failed, handle it accordingly
#                 # For example, show an error message
#                 error = "Invalid login credentials."
#                 return render(request, 'account/login.html', {'error': error, 'form': form})
#         else:
#             return render(request, 'account/login.html', {'form': form, 'error': 'Invalid CAPTCHA response.'})
#
#     # If it's a GET request or authentication failed, render the login form
#     form = CaptchaForm()
#     return render(request, 'account/login.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        # Check the value of the bot_catcher input field
        bot_catcher_value = request.POST.get('bot_catcher', '')

        # If the bot_catcher field is not empty, redirect to YouTube
        if bot_catcher_value:
            return redirect('https://www.youtube.com/watch?v=dQw4w9WgXcQ')

        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            # The user is valid, so log them in
            login(request, user)
            # Redirect to a success page or wherever you want
            return redirect('dashboard')
        else:
            # Authentication failed, handle it accordingly
            # For example, show an error message
            error = "Invalid login credentials."
            return render(request, 'account/login.html', {'error': error, })

    return render(request, 'account/login.html')


def forgot_pass(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        # Check if the user exists
        try:
            user = Users.objects.get(email=email)
        except Users.DoesNotExist:
            return render(request, 'account/forgot_password.html', {'error': 'User does not exist.'})

        # Generate OTP
        otp = str(random.randint(100000, 999999))
        print("otp : ", otp)

        # Attempt to send OTP to user's email
        try:

            email_subject = 'OTP Request for password reset.'
            email_body = render_to_string('email/otp.html', {'otp': otp})
            text_content = strip_tags(email_body)

            email = EmailMultiAlternatives(email_subject, text_content, settings.EMAIL_HOST_USER, [user.email])

            email.attach_alternative(email_body, "text/html")
            email.send()

        except BadHeaderError:
            return render(request, 'account/forgot_password.html', {'error': 'Invalid email header.'})
        except smtplib.SMTPException as e:
            # Handle SMTP exceptions here
            print(f"Failed to send email: {str(e)}")
            return render(request, 'account/forgot_password.html',
                          {'error': 'Failed to send email. Please try again later.'})
        except socket.gaierror as e:
            # Handle gaierror exceptions here
            print(f"Failed to resolve domain name: {str(e)}")
            error_message = 'Failed to resolve domain name. Check your internet connection.'
            return render(request, 'account/forgot_password.html', {'error': error_message})

        # Store the OTP in the session
        request.session['otp'] = otp
        request.session['user_id'] = user.id

        return redirect('confirm_otp')  # Replace 'confirm_otp' with your desired URL
    else:
        return render(request, 'account/forgot_password.html')


def confirm_otp(request):
    if request.method == 'POST':
        otp = request.POST.get('otp')
        new_password = request.POST.get('new_password')
        re_new_password = request.POST.get('re_new_password')

        # Retrieve OTP and user ID from the session
        stored_otp = request.session.get('otp')
        user_id = request.session.get('user_id')
        user_email = Users.objects.get(id=user_id).email

        if new_password == re_new_password:
            if otp == stored_otp:
                # Reset the user's password
                try:
                    user = Users.objects.get(id=user_id)
                except Users.DoesNotExist:
                    return render(request, 'account/confirm_otp.html', {'error': 'User does not exist.'})

                user.set_password(new_password)
                user.save()

                # Check if the user exists

                email_subject = 'Password Changed'
                email_body = 'Your password has been changed successfully.'
                from_email = settings.EMAIL_HOST_USER  # Use the sender email from settings
                recipient_list = [user_email]

                email = EmailMessage(email_subject, email_body, from_email, recipient_list)
                email.send()

                # Clear the session
                del request.session['otp']
                del request.session['user_id']

                return redirect('change_success')  # Replace 'login' with your desired URL
            else:
                return render(request, 'account/confirm_otp.html', {'error': 'Invalid OTP.'})
        else:
            return render(request, 'account/confirm_otp.html', {'error': 'Passwords do not match.'})
    else:
        return render(request, 'account/confirm_otp.html')


def change_success(request):
    return render(request, 'account/change_success.html',)