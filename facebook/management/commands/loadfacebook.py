# -*- coding: utf-8 -*-
"""Load data from a Facebook account"""

import fbconsole
import glob
import json
import os
import os.path

from django.conf import settings
from django.core import management

from facebook.models import TEMP_DIR


fbconsole.APP_ID = settings.FACEBOOK_API_ID
fbconsole.ACCESS_TOKEN_FILE = os.path.join(TEMP_DIR, 'fb_access_token')
fbconsole.AUTH_SCOPE = [
    'user_birthday', 'friends_birthday',
    'user_hometown', 'friends_hometown',
    'user_education_history', 'friends_education_history',
    'user_relationships', 'friends_relationships',
    'user_website', 'friends_website',
    'read_friendlists']

PROFILE_DIR = os.path.join(TEMP_DIR, 'profiles')


def load_data(filename):
    """Load temporary data"""
    try:
        return json.load(open(filename, 'r'))
    except:
        return


def save_data(filename, data):
    """Save temporary data"""
    dirname = os.path.dirname(filename)
    if not os.path.isdir(dirname):
        os.makedirs(dirname, 0o700)
    if not os.path.exists(filename):
        old_umask = os.umask(0o177)
        try:
            open(filename, 'a').close()
        finally:
            os.umask(old_umask)
    json.dump(data, open(filename, 'w'), indent=2)


def delete_data(filename):
    """Delete temporary data"""
    if os.path.exists(filename):
        os.unlink(filename)


def fbget_user():
    """Get current Facebook user"""
    user = load_data(os.path.join(TEMP_DIR, 'me.json'))
    if user is not None:
        return user
    user = fbconsole.get('/me')
    save_data(os.path.join(TEMP_DIR, 'me.json'), user)
    save_data(os.path.join(PROFILE_DIR, user['id'] + '.json'), user)
    return user


class Command(management.BaseCommand):
    args = ''
    help = 'Load data from Facebook'

    def handle(self, *args, **options):
        if not os.path.isdir(TEMP_DIR):
            os.makedirs(TEMP_DIR, 0o700)

        self.stdout.write("Loading data from Facebook...")
        fbconsole.authenticate()
        # Use fbconsole.logout() to log out

        # Retrieve user data
        user = fbget_user()
        self.stdout.write("User '{name}', ID {id}, username {username}".format(**user))

        # Load accounts cache
        cache = {user['id']: user}
        for filename in glob.glob(os.path.join(PROFILE_DIR, '*.json')):
            profile = load_data(filename)
            if not profile or 'id' not in profile:
                self.stderr.write("Nothing loaded in file '{0}'".format(filename))
            cache[profile['id']] = profile
        if len(cache) > 1:
            print("Loaded {0} profiles from cache".format(len(cache)))

        # Enumerate friends
        for friend in fbconsole.iter_pages(fbconsole.get('/me/friends')):
            fid = friend['id']
            fname = friend['name'].encode('ascii', 'replace')
            if fid not in cache:
                self.stdout.write("Retrieve profile of {0}, (ID={1})".format(fname, fid))
                profile = fbconsole.get('/' + fid)
                if profile['id'] != fid:
                    self.stderr.write("{0} has two IDs: {1} and {2}".format(fname, fid, profile['id']))
                save_data(os.path.join(PROFILE_DIR, profile['id'] + '.json'), profile)
                cache[profile['id']] = profile
                self.stdout.write(".. done")
