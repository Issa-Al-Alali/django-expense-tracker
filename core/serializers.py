from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import Expense, Income, Video, Category
import hashlib

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, source='pass')
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password')
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True}
        }
    
    def validate_email(self, value):
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError("Please enter a valid email address.")
        
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered. Please use a different email.")
        
        return value
    
    def validate(self, data):
        if not data.get('username') or not data.get('email') or not data.get('pass'):
            raise serializers.ValidationError("Please fill in all fields.")
        return data
    
    def create(self, validated_data):
        hashed_password = hashlib.sha256(validated_data['pass'].encode()).hexdigest()
        
        # Create user WITHOUT using create_user (which hashes again)
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            password=hashed_password  # Store exactly what we hashed
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            raise serializers.ValidationError("Both email and password are required.")
        
        # Hash the password to match registration
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            user = User.objects.get(email=email, password=hashed_password)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password")
        
        data['user'] = user
        return data
    
    # NEW Income Serializer
class IncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Income
        fields = '__all__'
        extra_kwargs = {'user': {'read_only': True}}
    
    def validate_budget_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("Budget amount cannot be negative")
        return value
    
class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Expense
        fields = ['id', 'expense_date', 'category', 'category_name', 
                 'description', 'amount', 'location', 'receipt']
        extra_kwargs = {
            'receipt': {'required': False, 'allow_null': True}
        }
    
    def create(self, validated_data):
        # Get the uploaded file from the request if it exists
        receipt = self.context['request'].FILES.get('receipt')
        if receipt:
            validated_data['receipt'] = receipt
            
        user = self.context.get('user')
        if not user:
            raise serializers.ValidationError("User is required.")
            
        validated_data['user'] = user
        return super().create(validated_data)
    
    def to_internal_value(self, data):
        # Handle case where receipt comes as a string (from JSON)
        if isinstance(data.get('receipt'), str) and data['receipt'] == '':
            data.pop('receipt')
        return super().to_internal_value(data)
    
class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ['id', 'title', 'url', 'thumbnail', 'description', 'created_at']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'  # or list specific fields like ['id', 'name', ...]