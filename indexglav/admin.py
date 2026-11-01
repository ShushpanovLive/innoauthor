from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Newspost, Tag
from .models import Expert

# Register your models here.
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(Newspost)
class NewspostAdmin(admin.ModelAdmin):
    readonly_fields = ['image_preview']
    list_display = ('namepost', 'humanpost', 'postdate')
    list_filter = ('tags', 'postdate')
    search_fields = ('namepost', 'soderjanie', 'humanpost')
    prepopulated_fields = {'slug': ('namepost',)}
    filter_horizontal = ('tags',)

    def image_preview(self, obj):
        if obj.post_photo:
            return mark_safe(f'<img src="{obj.post_photo.url}" style="max-width: 100px; max-height: 100px;">')
        return 'No image'

    image_preview.short_description = 'Preview'

@admin.register(Expert)
class ExpertAdmin(admin.ModelAdmin):
    list_display = ['name', 'text']
    erbose_name = 'Эксперт'           
    verbose_name_plural = 'Эксперты'   
