from django.contrib import admin
from .models import User, Prize, Task, Referral, ReferredUser, UserTask, Subscription
from django.utils.html import format_html
# Register your models here.

admin.site.register(Subscription)

class UserAdmin(admin.ModelAdmin):
    list_display_links = ['photo_thumbnail', 'username',]
    list_display = ['photo_thumbnail','telegram_id', 'username', 'first_name', 'score']
    search_fields  = ['username']
    order_by = ['score']

    def photo_thumbnail(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" style="width:50px; height:50px; border-radius:10px; object-fit: cover;" />'.format(obj.avatar.url))
        return 'No image'

    photo_thumbnail.short_description = 'Photo'


class PrizeAdmin(admin.ModelAdmin):
    list_display_links = ['photo_thumbnail', 'title']
    list_display = ['photo_thumbnail', 'title', 'desc', 'quantity']

    def photo_thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width:50px; height:50px; border-radius:10px; object-fit: cover;" />'.format(obj.image.url))
        return 'No image'

    photo_thumbnail.short_description = 'Image'

    def desc(self, obj):
        if obj.description:
            return obj.description[:15]
        return 'NO_DESC'
    desc.short_description = 'Description'

class TaskAdmin(admin.ModelAdmin):
    list_display_links = ['source','photo_thumbnail', 'title']
    list_display = ['source','photo_thumbnail', 'title', 'score']

    def photo_thumbnail(self, obj):
        if obj.source_image:
            return format_html('<img src="{}" style="width:50px; height:50px; border-radius:10px; object-fit: cover;" />'.format(obj.source_image.url))
        return 'No image'

    photo_thumbnail.short_description = 'Source_image'

    
class ReferralAdmin(admin.ModelAdmin):
    list_display_links = ['user','referral_code']
    list_display = ['user', 'referral_code']

class ReferredUserAdmin(admin.ModelAdmin):
    list_display_links = ['referred_by']
    list_display = ['referred_by', 'referred_user']


class UserTaskAdmin(admin.ModelAdmin):
    list_display_links = ['user']
    list_display = ['user', 'task']


admin.site.register(User,  UserAdmin)
admin.site.register(Prize, PrizeAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(Referral, ReferralAdmin)
admin.site.register(ReferredUser, ReferredUserAdmin)
admin.site.register(UserTask, UserTaskAdmin)