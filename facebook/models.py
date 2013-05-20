# -*- coding: utf-8 -*-
from django.db import models
from django.conf import settings
import os.path

# Setup a temporary directory
TEMP_DIR = os.path.join(settings.TEMP_DIR, 'facebook')
