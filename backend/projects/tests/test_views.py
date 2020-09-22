import pytest
from mixer.backend.django import mixer
from rest_framework.test import APIClient
from projects.models import Project, ProjectMembership
from projects.serializers import ProjectSerializer, ProjectMembershipSerializer
from users.models import User


pytestmark = pytest.mark.django_db


class TestProjectList:
    def test_get(self):
        user = mixer.blend(User)
        project1 = mixer.blend(Project, owner=user)
        project2 = mixer.blend(Project, owner=user)
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get('/projects/')
        assert response.status_code == 200
        assert len(response.data) == 2
    def test_post(self):
        user1 = mixer.blend(User)
        client = APIClient()
        client.force_authenticate(user1)
        response = client.post('/projects/', {
            "title": "Trial",
            "description": "stuff",
            "profile_picture": ""
        })
        assert response.status_code == 201

class TestProjectDetail:    
    @pytest.fixture
    def make_proj(self):
        user1 = mixer.blend(User)
        proj  = mixer.blend(Project, owner=user1)
        return (user1, proj)

    @pytest.fixture
    def make_proj_user(self):
        user1 = mixer.blend(User)
        user2 = mixer.blend(User)
        proj  = mixer.blend(Project, owner=user1)
        return (user1,user2,proj)

    def test_get_permission(self, make_proj_user):
        (user1, user2, proj) = make_proj_user
        client = APIClient()
        client.force_authenticate(user=user2)
        response = client.get('/projects/1')
        assert response.status_code == 403
        client.force_authenticate(user=user1)
        response = client.get('/projects/1')
        assert response.status_code == 200

    def test_put_permission(self, make_proj_user):
        (user1, user2, proj) = make_proj_user
        client = APIClient()
        client.force_authenticate(user=user2)
        modproj = ProjectSerializer(proj).data
        del modproj['owner']
        del modproj['profile_picture']
        response = client.put('/projects/1', modproj)
        assert response.status_code == 403
        client.force_authenticate(user=user1)
        response = client.put('/projects/1', modproj)
        assert response.status_code == 200
    
    def test_put_inconsistent(self, make_proj):
        (user1, proj) = make_proj
        client = APIClient()
        client.force_authenticate(user=user1)
        req = ProjectSerializer(proj).data
        req['owner'] = 3
        response = client.put('/projects/1', req)
        assert response.status_code == 400

    def test_delete_permission(self, make_proj_user):
        (user1, user2, proj) = make_proj_user
        client = APIClient()
        client.force_authenticate(user=user2)
        response = client.delete('/projects/1')
        assert response.status_code == 403
        client.force_authenticate(user=user1)
        response = client.delete('/projects/1')
        assert response.status_code == 200

    def test_authenticated(self):
        user1  = mixer.blend(User)
        proj   = mixer.blend(Project, owner=user1)
        client = APIClient()
        client.force_authenticate(user=mixer.blend(User))
        response = client.get('/projects/1')
        assert response.status_code == 403
        client.force_authenticate(user=user1)
        response = client.get('/projects/1')
        assert response.status_code == 200
    
    def test_get_consistent(self, make_proj):
        (user1, proj) = make_proj
        client = APIClient()
        client.force_authenticate(user=user1)
        response = client.get('/projects/1')
        assert response.data == ProjectSerializer(proj).data

    def test_put_consistent(self, make_proj):
        (user1, proj) = make_proj
        client = APIClient()
        client.force_authenticate(user=user1)
        modproj = ProjectSerializer(proj).data
        del modproj['owner']
        del modproj['profile_picture']
        response = client.put('/projects/1', modproj)
        assert response.data == ProjectSerializer(proj).data
    
    def test_delete_consistent(self, make_proj):
        (user1, proj) = make_proj
        client = APIClient()
        client.force_authenticate(user=user1)
        response = client.delete('/projects/1')
        assert response.data is None

class TestProjectMember:
    @pytest.fixture
    def make_proj(self):
        user1 = mixer.blend(User)
        proj  = mixer.blend(Project, owner=user1)
        return (user1, proj)
    
    def test_all_get(self, make_proj):
        (user1, proj) = make_proj
        client = APIClient()
        client.force_authenticate(user=user1)
        response = client.get('/projects/1/members')
        assert response.status_code == 200
        user2 = mixer.blend(User)
        client.force_authenticate(user2)
        response = client.get('/projects/1/members')
        assert response.status_code == 200
    
    def test_owner_put(self, make_proj):
        (user1, proj) = make_proj
        pmem = mixer.blend(ProjectMembership, project=proj, access_level=1)
        client = APIClient()
        client.force_authenticate(user=user1)
        response = client.put('/projects/1/members/1', {
            "access_level" : 2
        })
        assert response.data['access_level'] == 2
    
    def test_admin_put(self, make_proj):
        (user1, proj) = make_proj
        pmem1 = mixer.blend(ProjectMembership, project=proj, access_level=2)
        pmem2 = mixer.blend(ProjectMembership, project=proj, access_level=1)
        client = APIClient()
        client.force_authenticate(pmem1.member)
        response = client.put('/projects/1/members/2', {
            "access_level" : 2
        })
        assert response.data['access_level'] == 2
    
    def test_unauth_put(self, make_proj):
        (user1, proj) = make_proj
        pmem1 = mixer.blend(ProjectMembership, project=proj, access_level=1)
        client = APIClient()
        client.force_authenticate(pmem1.member)
        response = client.put('/projects/1/members/1', { "access_level" : 2 })
        assert response.status_code == 403
    
    def test_owner_delete(self, make_proj):
        (user1, proj) = make_proj
        pmem = mixer.blend(ProjectMembership, project=proj, access_level=1)
        client = APIClient()
        client.force_authenticate(user=user1)
        response = client.delete('/projects/1/members/1')
        assert response.status_code == 204
    
    def test_admin_delete(self, make_proj):
        (user1, proj) = make_proj
        pmem1 = mixer.blend(ProjectMembership, project=proj, access_level=2)
        pmem2 = mixer.blend(ProjectMembership, project=proj, access_level=1)
        client = APIClient()
        client.force_authenticate(pmem1.member)
        response = client.delete('/projects/1/members/2')
        assert response.status_code == 204
    
    def test_unauth_delete(self, make_proj):
        (user1, proj) = make_proj
        pmem1 = mixer.blend(ProjectMembership, project=proj, access_level=1)
        client = APIClient()
        client.force_authenticate(pmem1.member)
        response = client.delete('/projects/1/members/1')
        assert response.status_code == 403
    
    def test_put_inconsistent(self, make_proj):
        (user1,proj) = make_proj
        pmem1 = mixer.blend(ProjectMembership, project=proj)
        client = APIClient()
        client.force_authenticate(user1)
        modproj = ProjectMembershipSerializer(pmem1).data
        modproj['access_level'] = 3
        response = client.put('/projects/1/members/1', modproj, format='json')
        assert response.status_code == 400

    def test_project_members_get(self, make_proj):
        (user1, proj) = make_proj
        pmem1 = mixer.blend(ProjectMembership, project=proj)
        client = APIClient()
        response = client.get('/projects/2/members')
        assert response.status_code == 404