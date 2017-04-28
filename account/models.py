# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User

#User._meta.get_field_by_name('email')[0]._unique = True

def user_new_unicode(self):
    user_name = self.first_name or self.username
    return "%s[%s]" % (user_name, self.last_name)

User._meta.get_field('first_name').verbose_name = '姓名'
User._meta.get_field('last_name').verbose_name = '部门'
User.__unicode__ = user_new_unicode
