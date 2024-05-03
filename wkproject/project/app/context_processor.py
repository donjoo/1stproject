from app.models import Product,ProductImage,Category

def default(request):
    categories = Category.objects.filter(delete='False')
    # address = Address.objects.get(user=request.user)

    return {
         'categories':categories
    }
       
    