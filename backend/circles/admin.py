from django.contrib import admin

from .models import Circle, Contribution, Membership, Round

admin.site.register([Circle, Membership, Round, Contribution])
