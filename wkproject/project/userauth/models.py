from django.db import models
from django.contrib.auth.models import AbstractBaseUser,BaseUserManager,PermissionsMixin
from django.db.models import Q 
from django.core.validators import MaxValueValidator


class Usermanager(BaseUserManager):
    def create_user(self,first_name,last_name,email,username,password=None):
        if not email:
            raise ValueError('doesnt have an email')
        if not username:
            raise ValueError('doesnt have an username')
        
        user = self.model(
            email = self.normalize_email(email),
            username = username,
            first_name = first_name,
            last_name = last_name
        )
        user.set_password(password)
        user.save(using=self.db)
        return user
    


    def create_superuser(self,first_name,last_name,username,email,password=None):
        user = self.create_user(
            email = self.normalize_email(email),
            username = username,
            first_name = first_name,
            last_name = last_name,
            password = password
            
        )

        user.is_admin=True
        user.is_active = True
        user.is_staff=True
        user.is_superadmin=True 
        user.save(using=self.db)
        return user


class User(AbstractBaseUser,PermissionsMixin):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    username=models.CharField(max_length=50,unique=True)
    phone_number = models.CharField(max_length=12,null=True,blank=True)
    email =models.EmailField(max_length= 100,unique=True)

    is_admin = models.BooleanField(default = False)
    is_active=models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superadmin = models.BooleanField(default=False)


    date_joined = models.DateTimeField(auto_now_add = True)
    last_login = models.DateTimeField(auto_now_add = True)
    

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username','first_name','last_name']
    objects = Usermanager()

    


    def __str__(self):
     return self.email
  
    def has_perm(self, perm, obj=None):
        return self.is_admin

  
    def has_module_perms(self,app_label):
     return True



class Address(models.Model):
    user = models.ForeignKey(User,on_delete=models.SET_NULL,null=True)
    house = models.CharField(max_length = 100,null = True)
    street = models.CharField(max_length = 100,null = True)
    landmark = models.CharField(max_length = 100,null = True)
    pincode = models.IntegerField(validators=[MaxValueValidator(999999)],null = True)
    town = models.CharField(max_length = 100,null = True)
    state = models.CharField(max_length = 100,null = True)
    status = models.BooleanField(default=False)


    class Meta:
        verbose_name_plural ="Address"

    def __str__(self):
        return f"{self.street},{self.state} {self.pincode}"
     