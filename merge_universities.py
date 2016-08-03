#!/usr/bin/env python
"""This is a helper class for merging univrsities and all related objects"""

from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings
from student.models import *
import random, string
import dateutil.parser

from student.models import *

class MyApp_MergeUniversities:

    def __init__(self, old_university_id, new_university_id):
        """Returns Self"""
        self.old_university_id = old_university_id
        self.new_university_id = new_university_id
        pass

    def merge_universities(self):
        self.students_updated = 0
        self.contacts_updated = 0
        self.notifications_updated = 0
        response_data = {}

        # find all contacts related to old_university_id
        contacts = Contact.objects.filter( university = self.old_university_id )

        # update their university with new_university_id
        self.contacts_updated = self.update_university_relation( contacts, self.new_university_id )

        # find all students related to old_university_id
        students = Student.objects.filter( university = self.old_university_id )

        # update their university with new_university_id
        self.students_updated = self.update_university_relation( students, self.new_university_id )

        notifications = Notification.objects.filter( university = self.old_university_id )
        self.notifications_updated = self.update_university_relation( notifications, self.new_university_id )

        # Soft delete
        university = University.objects.get( pk = self.old_university_id )
        university.is_active = False

        # repsonse data
        response_data['result'] = 'success'
        response_data['contacts_updated'] = self.contacts_updated
        response_data['students_updated'] = self.students_updated
        response_data['notifications_updated'] = self.notifications_updated
        response_data['new_university_id'] = str(self.new_university_id.id)

        return response_data

    def update_university_relation(self, qs, university):
        counter = 0
        for item in qs:
            item.university = university
            item.save()
            counter += 1

        return counter

