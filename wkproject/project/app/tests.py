from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Product, Category, Variants, Stock
import json

# Create your tests here.

class SizeSelectionTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test category
        self.category = Category.objects.create(
            title="Test Category",
            cid="test123"
        )
        
        # Create test product
        self.product = Product.objects.create(
            title="Test Product",
            pid="testprod123",
            category=self.category,
            price=100.00,
            old_price=120.00
        )
        
        # Create test variants with different stock levels
        self.variant_in_stock = Variants.objects.create(
            product=self.product,
            size="M",
            is_active=True
        )
        
        self.variant_out_of_stock = Variants.objects.create(
            product=self.product,
            size="L",
            is_active=True
        )
        
        # Create stock records
        Stock.objects.create(
            variant=self.variant_in_stock,
            stock=5
        )
        
        Stock.objects.create(
            variant=self.variant_out_of_stock,
            stock=0
        )
    
    def test_get_sizes_includes_stock_info(self):
        """Test that get_sizes view returns stock information"""
        url = reverse('get_sizes', kwargs={'pid': self.product.pid})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Check that we get both sizes
        self.assertEqual(len(data['sizes']), 2)
        
        # Find the in-stock and out-of-stock sizes
        in_stock_size = next(s for s in data['sizes'] if s['size'] == 'M')
        out_of_stock_size = next(s for s in data['sizes'] if s['size'] == 'L')
        
        # Verify stock information
        self.assertTrue(in_stock_size['in_stock'])
        self.assertEqual(in_stock_size['stock'], 5)
        
        self.assertFalse(out_of_stock_size['in_stock'])
        self.assertEqual(out_of_stock_size['stock'], 0)
