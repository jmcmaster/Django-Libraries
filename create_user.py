#!/usr/bin/env python
"""This is a helper class for creating users and role profiles"""

from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings
from student.models import *
from datetime import datetime
import dateutil.parser
import random, string

class MyApp_CreateUser:

    def __init__(self, user_info):
        """Returns Self"""
        self.user_info = user_info
        pass

    def random_string(self, length):
        """Returns a random string, containing lowercase,
        uppercase and digits of the requested length"""
        return ''.join( random.choice( string.ascii_lowercase + string.ascii_uppercase + string.digits ) for i in range(length) )

    def create_user(self):
        """Returns new User"""
        self.password = self.random_string(8)

        self.user = User.objects.create_user(
                email = self.user_info.cleaned_data['email'],
                username = self.user_info.cleaned_data['email'],
                first_name = self.user_info.cleaned_data['first_name'],
                last_name = self.user_info.cleaned_data['last_name'],
            )
        self.user.password = make_password( self.password, None, 'default')
        self.user.is_active  = True
        self.user.save()

        profile = self.create_role_profile(self.user_info.cleaned_data['profile'])

        return self.user.first_name + ' ' + self.user.last_name

    def create_role_profile(self, profile):
        """Returns new profile Object"""
        return {
            'student': self.create_student_profile(),
            'manager': self.create_manager_profile(),
            'university': self.create_university_profile(),
            'liaison': self.create_liaison_profile(),
            'admin': self.create_admin_profile(),
            'super_admin': self.create_super_admin_profile(),
        }[profile]

    def create_student_profile(self):
        """Returns new Student"""

        if self.user_info.cleaned_data['profile'] != 'student':
            return False

        # Assign the Student group to the user
        self.assign_group('Student')

        # Now lets make a student from the user
        student = Student( user = self.user )

        # Save the student to the DB
        student.fiscal_year = settings.FISCAL_YEAR
        student.modified = datetime.now()
        student.optin = self.user_info.cleaned_data['optin']
        student.has_applied_before = self.user_info.cleaned_data['has_applied_before']
        student.save()

        self.send_notification('Student')

        return student

    def create_manager_profile(self):
        """Returns new Manager"""

        if self.user_info.cleaned_data['profile'] != 'manager':
            return False

        # Assign the Manager group to the user
        self.assign_group('Manager')

        # Now lets make a manager from the user
        manager = Manager( user = self.user )

        # Save the manager to the DB
        manager.name = '{} {}'.format( self.user.first_name, self.user.last_name )
        manager.title = self.user_info.cleaned_data['title']
        manager.unit = self.user_info.cleaned_data['unit']
        manager.status = self.user_info.cleaned_data['status']
        manager.save()

        self.send_notification('Manager')

        return manager

    def create_university_profile(self):
        """Returns new University"""

        if self.user_info.cleaned_data['profile'] != 'university':
            return False

        # Assign the University group to the user
        self.assign_group('University')

        # Get or Create University
        # Lets see if the university exists, if not we will create one
        if self.user_info.cleaned_data['country'] is not None and self.user_info.cleaned_data['university'] != 'other':

            school = School.objects.get( pk = self.user_info.cleaned_data['university'] )

            try:
                university = University.objects.get( name = school.name )
            except University.DoesNotExist:
                university,created = University.objects.get_or_create(
                    name = school.name,
                    recommended = False,
                    country = school.country_code
                )

        if self.user_info.cleaned_data['write_in_university'] is not None and self.user_info.cleaned_data['country'] is not None and self.user_info.cleaned_data['university'] == 'other':

            write_in_university = self.user_info.cleaned_data['write_in_university']
            school = School.objects.filter( name = write_in_university ).first()

            if school is None:
                # We couldnt find the school in our system, lets create a school and university object
                school,created = School.objects.get_or_create(
                    name = self.user_info.cleaned_data['write_in_university'],
                    country_code = self.user_info.cleaned_data['country']
                )
                university,created = University.objects.get_or_create(
                    name = self.user_info.cleaned_data['write_in_university'],
                    recommended = False,
                    country = self.user_info.cleaned_data['country'],
                )
            else:
                # We found your school, lets see if we have a University object for it
                university = University.objects.filter( name = school.name ).first()
                if university is None:
                    university,created = University.objects.get_or_create(
                        name = self.user_info.cleaned_data['write_in_university'],
                        recommended = False,
                        country = self.user_info.cleaned_data['country']
                    )

        contact, created    = Contact.objects.get_or_create(
            university = university,
            user = self.user,
            email = self.user_info.cleaned_data['email'],
            name = self.user_info.cleaned_data['first_name'] + ' ' + self.user_info.cleaned_data['last_name'],
            title = self.user_info.cleaned_data['title']
        )

        self.send_notification('University')

        return university

    def create_liaison_profile(self):
        """Returns new Liaison"""

        if self.user_info.cleaned_data['profile'] != 'liaison':
            return False

        # Assign the Liaison group to the user
        self.assign_group('Liaison')

        # Now lets make a manager from the user
        liaison = Liaison( user =self.user )

        # Save the manager to the DB
        liaison.first_name = self.user_info.cleaned_data['first_name']
        liaison.last_name = self.user_info.cleaned_data['last_name']
        liaison.title = self.user_info.cleaned_data['title']
        liaison.status = self.user_info.cleaned_data['status']
        liaison.save()

        liaison_country = LiaisonCountry( liaison = liaison, country_code = self.user_info.cleaned_data['country'] )
        liaison_country.save()

        if self.user_info.cleaned_data['country_2'] is not None and self.user_info.cleaned_data['country_2'] != '' and self.user_info.cleaned_data['country_2'] != 'default':
            liaison_country_2 = LiaisonCountry( liaison = liaison, country_code = self.user_info.cleaned_data['country_2'] )
            liaison_country_2.save()

        if self.user_info.cleaned_data['country_3'] is not None and self.user_info.cleaned_data['country_3'] != '' and self.user_info.cleaned_data['country_3'] != 'default':
            liaison_country_3 = LiaisonCountry( liaison = liaison, country_code = self.user_info.cleaned_data['country_3'] )
            liaison_country_3.save()

        if self.user_info.cleaned_data['country_4'] is not None and self.user_info.cleaned_data['country_4'] != '' and self.user_info.cleaned_data['country_4'] != 'default':
            liaison_country_4 = LiaisonCountry( liaison = liaison, country_code = self.user_info.cleaned_data['country_4'] )
            liaison_country_4.save()

        self.send_notification('Country Liaison')

        return liaison

    def create_admin_profile(self):
        """Returns new admin"""

        if self.user_info.cleaned_data['profile'] != 'admin':
            return False

        # Assign the group to the user
        self.assign_group('Admin')

        self.send_notification('Admin')

        return self.user

    def create_super_admin_profile(self):
        """Returns new Super Admin"""

        if self.user_info.cleaned_data['profile'] != 'super_admin':
            return False

        # Assign the Super Admin group to the user
        self.assign_group('Super Admin')

        admin = None

        self.send_notification('Super Admin')

        return admin

    def assign_group(self, group):
        # Assign the group to the user
        group = Group.objects.get( name = group )
        group.user_set.add( self.user )

    def send_notification(self, role):
        # TODO: Add notification logic

    def get_user_name(self):
        return self.user.first_name + ' ' + self.user.last_name

    def get_role(self):
        return string.replace( self.user_info.cleaned_data['profile'].title(), '_', ' ' )

    def get_password(self):
        return self.password
