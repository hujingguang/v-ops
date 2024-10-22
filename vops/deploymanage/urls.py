from django.urls import path
from deploymanage import views

urlpatterns = [
        path('serviceManage/', views.service_manage),
        path('serviceRead/', views.service_readme),
        path('bindService/', views.bind_service),
        path('bindServiceSelect/', views.get_bind_service_select),
        path('getRelationService/', views.get_relation_service_list),
        path('addService/', views.add_service),
        path('delService/', views.del_service),
        path('resetService/', views.reset_service),
        path('getService/', views.get_service),
        path('updateService/', views.update_service),
        path('versionTest/', views.version_test),
        path('versionTestServiceSelect/', views.get_add_version_service_select),
        path('versionTestBranchSelect/', views.get_add_version_branch_select),
        path('versionTestUserSelect/', views.get_add_version_user_select),
        path('versionTestEnvSelect/', views.get_add_version_env_select),
        path('addVersion/', views.add_version),
        path('getVersion/', views.get_version),
        path('updateVersion/', views.update_version),
        path('passVersion/', views.pass_version),
        path('deployVersion/', views.deploy_version),
        path('versionPublish/', views.version_publish),
        path('versionPublishServiceSelect/', views.get_deploy_versions_select),
        path('versionPublishRelationSelect/', views.get_deploy_relation_select),
        path('addPublish/', views.add_publish),
        path('getPublish/', views.get_publish),
        path('passPublish/', views.pass_publish),
        path('deletePublish/', views.delete_publish),
        path('mergeConflictPublish/', views.merge_conflict_publish),
        path('versionPublishEnvSelect/', views.get_add_publish_env_select),
        path('deployPublish/', views.deploy_publish),
        path('createRelease/', views.create_release),
        path('mergeRelease/', views.clear_and_merge_branch),
]
