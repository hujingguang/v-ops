from django.contrib import admin
from .models import AppInfo, AppRelationShip, DeployAppEnv, DeployAppRecord, DeployAppRecordDetail, AppVersionRecord, DeployAppPublishRecord, DeployAppPublishRecordDetail, AppVersionHistory
from .models import AppBranchStatus


@admin.register(AppInfo)
class AppInfoAdmin(admin.ModelAdmin):
    list_display = ('app_name', 'git_repo_address',
                    'pom_xml_path', 'app_type', 'create_time', 'update_time', 'create_user', 'app_function')
    ordering = ('app_name',)


@admin.register(AppRelationShip)
class AppRelationShipAdmin(admin.ModelAdmin):
    list_display = ('r_id', 'app_name', 'with_apps',
                    'create_time', 'update_time', 'create_user')


@admin.register(DeployAppEnv)
class DeployEnvAdmin(admin.ModelAdmin):
    list_display = ('env_id', 'env_name', 'env_description',
                    'env_kubeconf', 'env_namespace')


@admin.register(DeployAppRecord)
class DeployAppRecordAdmin(admin.ModelAdmin):
    list_display = ('deploy_id', 'app_name', 'feature_branch',
                    'feature_branch_uuid', 'auto_test_branch', 'auto_test_branch_uuid', 'deploy_status', 'create_time',
                    'update_time', 'create_user', 'test_user',
                    'test_status', 'publish_status',
                    'publish_time', 'description')


@admin.register(DeployAppRecordDetail)
class DeployAppRecordDetailAdmin(admin.ModelAdmin):
    list_display = ('detail_id', 'compile_log', 'deploy_log',
                    'update_log', 'test_image_url')


@admin.register(AppVersionRecord)
class AppVersionRecordAdmin(admin.ModelAdmin):
    list_display = ('version_id', 'publish_id', 'app_name',
                    'feature_branch', 'test_branch', 'test_branch_uuid', 'release_branch', 'release_branch_uuid',
                    'publish_tag', 'maven_jar_version'
                    )


@admin.register(DeployAppPublishRecord)
class DeployAppPublishRecordAdmin(admin.ModelAdmin):
    list_display = (
        'publish_id', 'description','deploy_ids',
        'create_user', 'create_time', 'update_time',
    )


@admin.register(DeployAppPublishRecordDetail)
class DeployAppPublishRecordDetailAdmin(admin.ModelAdmin):
    list_display = (
        'detail_id', 'compile_log', 'deploy_log', 'update_log',
        'release_image_url')


@admin.register(AppVersionHistory)
class AppVersionHistoryAdmin(admin.ModelAdmin):
    list_display = ('history_id', 'app_name', 'release_name','create_time')


@admin.register(AppBranchStatus)
class AppBranchStatusAdmin(admin.ModelAdmin):
    list_display = ('branch_id','app_name','branch_name','is_deleted','is_merged','create_time','create_by','branch_type')

