from django.contrib import admin
from app.models import Product,Category,ProductImage,ProductVariants,CategoryAnime,AnimeCharacter,Variants

from django.utils.safestring import mark_safe


# Register your models here.

# class ProductImagesAdmin(admin.TabularInline):
#     model= ProductImage

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]

    list_display =['title','product_image','price','featured','status']

    def product_image(self, obj):
        if obj.image:  # Check if the 'image' field has a file associated with it
            return mark_safe('<img src="%s" width="50" height="50"/>' % obj.image.url)
        else:
            return "No image available"

    product_image.allow_tags = True
    product_image.short_description = 'Image'

    inlines = [ProductImageInline]


class CategoryAdmin(admin.ModelAdmin):
    list_display=['title','category_image']

class CategoryAnimeAdmin(admin.ModelAdmin):
    list_display=['title','Anime_image']


class AnimeCharacterAdmin(admin.ModelAdmin):
    list_display=['name','Character_image']


class ProductVariantAdmin(admin.ModelAdmin):
    list_display=['size','stock_count']

class VariantAdmin(admin.ModelAdmin):
    list_display = ['product','size','is_active']
    list_editable= ['is_active']


admin.site.register(Product,ProductAdmin)
admin.site.register(Category,CategoryAdmin)
admin.site.register(CategoryAnime,CategoryAnimeAdmin)
admin.site.register(AnimeCharacter,AnimeCharacterAdmin)
admin.site.register(ProductVariants,ProductVariantAdmin)
admin.site.register(Variants,VariantAdmin)





