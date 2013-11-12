# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2013 Jeremy Lainé
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import json
import os
import shutil
import tempfile

from django.conf import settings
from django.test import TestCase

from coconuts.views import clean_path

class BaseTest(TestCase):
    maxDiff = None

    def assertJson(self, response, data, status_code=200):
        self.assertEquals(response.status_code, status_code)
        self.assertEquals(response['Content-Type'], 'application/json')
        self.assertEquals(json.loads(response.content), data)

    def setUp(self):
        """
        Creates temporary directories.
        """
        for path in [settings.COCONUTS_CACHE_ROOT, settings.COCONUTS_DATA_ROOT]:
            os.makedirs(path)

    def tearDown(self):
        """
        Removes temporary directories.
        """
        for path in [settings.COCONUTS_CACHE_ROOT, settings.COCONUTS_DATA_ROOT]:
            shutil.rmtree(path)

class PathTest(BaseTest):
    def test_clean(self):
        self.assertEquals(clean_path(''), '')
        self.assertEquals(clean_path('.'), '')
        self.assertEquals(clean_path('..'), '')
        self.assertEquals(clean_path('/'), '')
        self.assertEquals(clean_path('/foo'), 'foo')
        self.assertEquals(clean_path('/foo/'), 'foo')
        self.assertEquals(clean_path('/foo/bar'), 'foo/bar')
        self.assertEquals(clean_path('/foo/bar/'), 'foo/bar')

    def test_clean_bad(self):
        with self.assertRaises(ValueError):
            clean_path('\\')
        with self.assertRaises(ValueError):
            clean_path('\\foo')

class EmptyFolderContentTest(BaseTest):
    fixtures = ['test_users.json']

    def test_home_as_anonymous(self):
        """
        Anonymous users need to login.
        """
        response = self.client.get('/images/contents/')
        self.assertRedirects(response, '/accounts/login/?next=/images/contents/')

    def test_home_as_superuser(self):
        """
        Authenticated super-user can browse the home folder.
        """
        self.client.login(username="test_user_1", password="test")
        response = self.client.get('/images/contents/')
        self.assertJson(response, {
            'can_manage': True,
            'can_write': True,
            'files': [],
            'folders': [],
            'name': '',
            'path': '/',
        })

    def test_home_as_user(self):
        """
        Authenticated user cannot browse the home folder.
        """
        self.client.login(username="test_user_2", password="test")
        response = self.client.get('/images/contents/')
        self.assertEquals(response.status_code, 403)

class FolderContentTest(BaseTest):
    fixtures = ['test_users.json']

    def setUp(self):
        super(FolderContentTest, self).setUp()
        os.makedirs(os.path.join(settings.COCONUTS_DATA_ROOT, 'Foo'))
        for name in ['test.jpg', 'test.txt']:
            source_path = os.path.join(os.path.dirname(__file__), name)
            dest_path = os.path.join(settings.COCONUTS_DATA_ROOT, name)
            shutil.copyfile(source_path, dest_path)

    def test_file_as_anonymous(self):
        response = self.client.get('/images/contents/test.jpg')
        self.assertRedirects(response, '/accounts/login/?next=/images/contents/test.jpg')

    def test_file_as_superuser(self):
        self.client.login(username="test_user_1", password="test")
        response = self.client.get('/images/contents/test.jpg')
        self.assertEquals(response.status_code, 404)

    def test_file_as_user(self):
        self.client.login(username="test_user_2", password="test")
        response = self.client.get('/images/contents/test.jpg')
        self.assertEquals(response.status_code, 403)

    def test_home_as_anonymous(self):
        """
        Anonymous users need to login.
        """
        response = self.client.get('/images/contents/')
        self.assertRedirects(response, '/accounts/login/?next=/images/contents/')

    def test_home_as_superuser(self):
        """
        Authenticated super-user can browse the home folder.
        """
        self.client.login(username="test_user_1", password="test")
        response = self.client.get('/images/contents/')
        self.assertJson(response, {
            'can_manage': True,
            'can_write': True,
            'files': [],
            'files': [
                {
                    'image': {
                        'camera': 'Canon EOS 450D',
                        'settings': u'f/10.0, 1/125\xa0sec, 48\xa0mm',
                        'size': [1024, 683],
                    },
                    'mimetype': 'image/jpeg',
                    'name': 'test.jpg',
                    'path': '/test.jpg',
                    'size': 186899,
                },
                {
                    'mimetype': 'text/plain',
                    'name': 'test.txt',
                    'path': '/test.txt',
                    'size': 6,
                }
            ],
            'folders': [
                {
                    'name': 'Foo',
                    'path': '/Foo/',
                    'size': 4096,
                },
            ],
            'name': '',
            'path': '/',
        })

    def test_home_as_user(self):
        """
        Authenticated user cannot browse the home folder.
        """
        self.client.login(username="test_user_2", password="test")
        response = self.client.get('/images/contents/')
        self.assertEquals(response.status_code, 403)

class HomeTest(BaseTest):
    fixtures = ['test_users.json']

    def test_home_as_anonymous(self):
        """
        Anonymous user needs to login.
        """
        response = self.client.get('/')
        self.assertRedirects(response, '/accounts/login/?next=/')

    def test_home_as_user(self):
        """
        Authenticated user can browse home folder.
        """
        self.client.login(username="test_user_2", password="test")
        response = self.client.get('/')
        self.assertEquals(response.status_code, 200)

    def test_other_as_anonymous(self):
        """
        Anonymous user needs to login.
        """
        response = self.client.get('/other/')
        self.assertRedirects(response, '/accounts/login/?next=/other/')

    def test_other_as_user(self):
        """
        Authenticated user can browse other folder.
        """
        self.client.login(username="test_user_2", password="test")
        response = self.client.get('/other/')
        self.assertRedirects(response, '/#/other/')

class AddFileTest(BaseTest):
    fixtures = ['test_users.json']

    def test_as_superuser(self):
        """
        Authenticated super-user can create a folder.
        """
        self.client.login(username="test_user_1", password="test")

        # GET fails
        response = self.client.get('/images/add_file/')
        self.assertEquals(response.status_code, 405)

        # POST succeeds
        source_path = os.path.join(os.path.dirname(__file__), 'folder.png')
        response = self.client.post('/images/add_file/', {'upload': open(source_path, 'rb')})
        self.assertJson(response, {
            'can_manage': True,
            'can_write': True,
            'files': [
                {
                    'mimetype': 'image/png',
                    'name': 'folder.png',
                    'path': '/folder.png',
                    'size': 548,
                }
             ],
            'folders': [],
            'name': '',
            'path': '/',
        })

        # check folder
        data_path = os.path.join(settings.COCONUTS_DATA_ROOT, 'folder.png')
        self.assertTrue(os.path.exists(data_path))

class AddFolderTest(BaseTest):
    fixtures = ['test_users.json']

    def test_as_superuser(self):
        """
        Authenticated super-user can create a folder.
        """
        self.client.login(username="test_user_1", password="test")

        # GET fails
        response = self.client.get('/images/add_folder/')
        self.assertEquals(response.status_code, 405)

        # POST succeeds
        response = self.client.post('/images/add_folder/', {'name': 'New folder'})
        self.assertJson(response, {
            'can_manage': True,
            'can_write': True,
            'files': [],
            'folders': [
                {
                    'name': 'New folder',
                    'path': '/New folder/',
                    'size': 4096,
                },
            ],
            'name': '',
            'path': '/',
        })

        # check folder
        data_path = os.path.join(settings.COCONUTS_DATA_ROOT, 'New folder')
        self.assertTrue(os.path.exists(data_path))

    def test_as_user(self):
        """
        Authenticated user cannot create a folder.
        """
        self.client.login(username="test_user_2", password="test")

        # GET fails
        response = self.client.get('/images/add_folder/')
        self.assertEquals(response.status_code, 405)

        # POST fails
        response = self.client.post('/images/add_folder/', {'name': 'New folder'})
        self.assertEquals(response.status_code, 403)

class DeleteFileTest(BaseTest):
    fixtures = ['test_users.json']

    def test_as_superuser(self):
        """
        Authenticated super-user can delete a file.
        """
        self.client.login(username="test_user_1", password="test")

        data_path = os.path.join(settings.COCONUTS_DATA_ROOT, 'folder.png')
        open(data_path, 'w').write('foo')

        # GET fails
        response = self.client.get('/images/delete/folder.png')
        self.assertEquals(response.status_code, 405)
        self.assertTrue(os.path.exists(data_path))

        # POST succeeds
        response = self.client.post('/images/delete/folder.png')
        self.assertJson(response, {
            'can_manage': True,
            'can_write': True,
            'files': [],
            'folders': [],
            'name': '',
            'path': '/',
        })
        self.assertFalse(os.path.exists(data_path))

    def test_as_user(self):
        """
        Authenticated user cannot delete a file.
        """
        self.client.login(username="test_user_2", password="test")

        data_path = os.path.join(settings.COCONUTS_DATA_ROOT, 'folder.png')
        open(data_path, 'w').write('foo')

        # GET fails
        response = self.client.get('/images/delete/folder.png')
        self.assertEquals(response.status_code, 405)
        self.assertTrue(os.path.exists(data_path))

        # POST fails
        response = self.client.post('/images/delete/folder.png')
        self.assertEquals(response.status_code, 403)
        self.assertTrue(os.path.exists(data_path))

class DeleteFolderTest(BaseTest):
    fixtures = ['test_users.json']

    def test_as_superuser(self):
        """
        Authenticated super-user can delete a file.
        """
        self.client.login(username="test_user_1", password="test")

        data_path = os.path.join(settings.COCONUTS_DATA_ROOT, 'Foo')
        os.makedirs(data_path)

        # GET fails
        response = self.client.get('/images/delete/Foo/')
        self.assertEquals(response.status_code, 405)
        self.assertTrue(os.path.exists(data_path))

        # POST succeeds
        response = self.client.post('/images/delete/Foo/')
        self.assertJson(response, {
            'can_manage': True,
            'can_write': True,
            'files': [],
            'folders': [],
            'name': '',
            'path': '/',
        })
        self.assertFalse(os.path.exists(data_path))

    def test_as_user(self):
        """
        Authenticated user cannot delete a file.
        """
        self.client.login(username="test_user_2", password="test")

        data_path = os.path.join(settings.COCONUTS_DATA_ROOT, 'Foo')
        os.makedirs(data_path)

        # GET fails
        response = self.client.get('/images/delete/Foo/')
        self.assertEquals(response.status_code, 405)
        self.assertTrue(os.path.exists(data_path))

        # POST fails
        response = self.client.post('/images/delete/Foo/')
        self.assertEquals(response.status_code, 403)
        self.assertTrue(os.path.exists(data_path))

class DownloadFileTest(BaseTest):
    fixtures = ['test_users.json']

    def setUp(self):
        super(DownloadFileTest, self).setUp()
        for name in ['test.jpg']:
            source_path = os.path.join(os.path.dirname(__file__), name)
            dest_path = os.path.join(settings.COCONUTS_DATA_ROOT, name)
            shutil.copyfile(source_path, dest_path)

    def test_as_superuser(self):
        """
        Authenticated super-user can download a file.
        """
        self.client.login(username="test_user_1", password="test")

        # bad path
        response = self.client.get('/images/download/notfound.jpg')
        self.assertEquals(response.status_code, 404)

        # good path
        response = self.client.get('/images/download/test.jpg')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response['Content-Type'], 'image/jpeg')
        self.assertEquals(response['Content-Disposition'], 'attachment; filename="test.jpg"')
        self.assertFalse('Expires' in response)
        self.assertTrue('Last-Modified' in response)

    def test_as_user(self):
        """
        Authenticated user cannot download a file.
        """
        self.client.login(username="test_user_2", password="test")

        # bad path
        response = self.client.get('/images/download/notfound.jpg')
        self.assertEquals(response.status_code, 403)

        # good path
        response = self.client.get('/images/download/test.jpg')
        self.assertEquals(response.status_code, 403)

class RenderFileTest(BaseTest):
    fixtures = ['test_users.json']

    def setUp(self):
        super(RenderFileTest, self).setUp()
        for name in ['test.jpg']:
            source_path = os.path.join(os.path.dirname(__file__), name)
            dest_path = os.path.join(settings.COCONUTS_DATA_ROOT, name)
            shutil.copyfile(source_path, dest_path)

    def test_as_superuser(self):
        """
        Authenticated super-user can render a file.
        """
        self.client.login(username="test_user_1", password="test")

        # no size
        response = self.client.get('/images/render/test.jpg')
        self.assertEquals(response.status_code, 400)

        # bad size
        response = self.client.get('/images/render/test.jpg?size=123')
        self.assertEquals(response.status_code, 400)

        # good size, bad path
        response = self.client.get('/images/render/notfound.jpg?size=1024')
        self.assertEquals(response.status_code, 404)

        # good size, good path
        response = self.client.get('/images/render/test.jpg?size=1024')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response['Content-Type'], 'image/jpeg')
        self.assertTrue('Expires' in response)
        self.assertTrue('Last-Modified' in response)

    def test_as_user(self):
        """
        Authenticated user cannot render a file.
        """
        self.client.login(username="test_user_2", password="test")

        # no size
        response = self.client.get('/images/render/test.jpg')
        self.assertEquals(response.status_code, 400)

        # bad size
        response = self.client.get('/images/render/test.jpg?size=123')
        self.assertEquals(response.status_code, 400)

        # good size, bad path
        response = self.client.get('/images/render/notfound.jpg?size=1024')
        self.assertEquals(response.status_code, 403)

        # good size, good path
        response = self.client.get('/images/render/test.jpg?size=1024')
        self.assertEquals(response.status_code, 403)
