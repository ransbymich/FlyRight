from django.contrib.auth import authenticate
from users.tokens import account_activation_token
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from users.models import IcarusUser as User
from icarus_backend.pilot.PilotModel import Pilot
from icarus_backend.user.tasks import send_verification_email
from django.template.loader import render_to_string

import smtplib


class UserController:

    @staticmethod
    def register_user(username, email, password, first_name, last_name, domain) -> (int, str):
        user = User.objects.filter(email=email).first()
        if user is not None:
            return 400, 'Email address has already been taken.'
        user = authenticate(username=username, password=password)
        if user is None:
            user = User.objects.create_user(username=username,
                                            email=email,
                                            password=password,
                                            first_name=first_name,
                                            last_name=last_name,
                                            role='pilot')
            user.is_active = False
            user.save()
            send_verification_email.delay(user.username, user.email, user.id, domain)
            
            sender = 'no-reply-flyright@police.gatech.edu'
            receivers = ['michael.ransby@gmail.com']

            domain = 'http://flyright-api.police.gatech.edu:8000'
            uidb64 = urlsafe_base64_encode(force_bytes(user.id))
            token = account_activation_token.make_token(user.username)
            uid_text = force_text(urlsafe_base64_decode(uidb64))

            message = """From: GTPD Flyright <no-reply-flyright@police.gatech.edu>
To: To Person <""" + receivers[0] + """>
Subject: SMTP e-mail test

Link: """ + domain + """/user/activate/""" + uidb64 + """/""" + token + """
Token: """ + token + """
uid: """ + uid_text + """

This is a test e-mail message. (Sent from UserController.py)
                """
            other_message = render_to_string('acc_active_email.html', {
                    'user': user.username,
                    'domain': domain, 
                    'uid': uidb64,
                    'token': token
                    })


            print(other_message)
            try:
                smtpObj = smtplib.SMTP('outbound.gatech.edu')
                smtpObj.sendmail(sender, receivers, message)
                print("Successfully sent email")
            except SMTPException:
                print("Error: unable to send email")

            return 200, 'User successfully registered.'
        else:
            return 400, 'User already exists.'

    @staticmethod
    def change_password(email, old_password, new_password) -> (int, str):
        user = User.objects.filter(email=email).first()
        if not user.check_password(old_password):
            return 400, 'Incorrect old password.'
        user.set_password(new_password)
        user.save()
        return 200, 'Password successfully changed.'

    @staticmethod
    def get_user(id) -> (int, dict):
        user = User.objects.filter(id=id).first()
        if not user:
            return 400, {'message': 'No user with this id exists.'}
        response_dict = dict()
        response_dict['user'] = user.as_dict()
        pilot = Pilot.objects.filter(user=user).first()
        if pilot:
            response_dict['pilot'] = pilot.as_dict()
        return 200, response_dict

    @staticmethod
    def update(id, parsed_json):
        user = User.objects.filter(id=id).first()
        if 'email' in parsed_json and user.email != parsed_json['email']:
            user.email = parsed_json['email']
        if 'password' in parsed_json and user.password != parsed_json['password']:
            user.password = parsed_json['password']
        if 'username' in parsed_json and user.username != parsed_json['username']:
            check_user = User.objects.filter(username=parsed_json['username']).first()
            if check_user:
                return 401, {'message': 'Username already taken.'}
            user.username = parsed_json['username']
        if 'first_name' in parsed_json and user.first_name != parsed_json['first_name']:
            user.first_name = parsed_json['first_name']
        if 'last_name' in parsed_json and user.last_name != parsed_json['last_name']:
            user.last_name = parsed_json['last_name']
        if 'picture_url' in parsed_json and user.picture_url != parsed_json['picture_url']:
            user.picture_url = parsed_json['picture_url']
        user.save()
        return 200, {'message': 'Info updated successfully.'}
