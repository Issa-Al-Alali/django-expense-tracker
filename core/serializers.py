from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import Expense, Income, Video, Category, VideoComment, VideoLike, VideoReview
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
        
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            password=hashed_password
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
        
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            user = User.objects.get(email=email, password=hashed_password)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password")
        
        data['user'] = user
        return data

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile_picture']

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
        receipt = self.context['request'].FILES.get('receipt')
        if receipt:
            validated_data['receipt'] = receipt
            
        user = self.context.get('user')
        if not user:
            raise serializers.ValidationError("User is required.")
            
        validated_data['user'] = user
        return super().create(validated_data)
    
    def to_internal_value(self, data):
        if isinstance(data.get('receipt'), str) and data['receipt'] == '':
            data.pop('receipt')
        return super().to_internal_value(data)

class VideoCommentSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_profile_picture = serializers.ImageField(source='user.profile_picture', read_only=True)
    
    class Meta:
        model = VideoComment
        fields = ['id', 'user', 'video', 'content', 'created_at', 'updated_at', 
                  'user_username', 'user_profile_picture']
        extra_kwargs = {
            'user': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True}
        }
    
    def create(self, validated_data):
        user = self.context.get('request').user
        validated_data['user'] = user
        return super().create(validated_data)

class VideoLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoLike
        fields = ['id', 'user', 'video', 'created_at']
        extra_kwargs = {
            'user': {'read_only': True},
            'created_at': {'read_only': True}
        }

    def create(self, validated_data):
        user = self.context.get('request').user
        video = validated_data['video'] # Get the video instance

        # Check if the user already liked this video
        existing_like = VideoLike.objects.filter(
            user=user,
            video=video
        ).first()

        if existing_like:
            # If like exists, this is a toggle operation, so remove it
            existing_like.delete()

            # Update the likes count on the video - Decrement when unliking
            video.likes_count = max(0, video.likes_count - 1)
            video.save()

            # Return the deleted like instance (or None, depending on desired behavior)
            # Returning the instance that was just deleted might be confusing.
            # It might be better to return None or raise a specific exception
            # indicating deletion for clarity in the view, but for consistency
            # with the original structure returning the deleted instance.
            return existing_like
        else:
            # Create new like
            validated_data['user'] = user # Assign the current user
            like = super().create(validated_data)

            # Update the likes count on the video - Increment when liking
            video.likes_count = video.likes_count + 1
            video.save()

            return like

class VideoReviewSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = VideoReview
        fields = ['id', 'user', 'video', 'rating', 'review_text', 
                  'created_at', 'updated_at', 'user_username']
        extra_kwargs = {
            'user': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True}
        }
    
    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value
    
    def create(self, validated_data):
        user = self.context.get('request').user
        validated_data['user'] = user
        
        # Check if user already reviewed this video
        existing_review = VideoReview.objects.filter(
            user=user, 
            video=validated_data['video']
        ).first()
        
        if existing_review:
            # Update the existing review
            existing_review.rating = validated_data['rating']
            existing_review.review_text = validated_data['review_text']
            existing_review.save()
            return existing_review
        
        return super().create(validated_data)

class VideoSerializer(serializers.ModelSerializer):
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    user_has_liked = serializers.SerializerMethodField(read_only=True)
    user_review = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Video
        fields = ['id', 'title', 'url', 'thumbnail', 'description', 'created_at',
                  'likes_count', 'comments_count', 'user_has_liked', 'user_review']
    
    def get_user_has_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return VideoLike.objects.filter(user=request.user, video=obj).exists()
        return False
    
    def get_user_review(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            review = VideoReview.objects.filter(user=request.user, video=obj).first()
            if review:
                return VideoReviewSerializer(review).data
        return None

class VideoDetailSerializer(VideoSerializer):
    comments = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()
    
    class Meta(VideoSerializer.Meta):
        fields = VideoSerializer.Meta.fields + ['comments', 'reviews']
    
    def get_comments(self, obj):
        comments = obj.comments.all().order_by('-created_at')
        return VideoCommentSerializer(comments, many=True).data
    
    def get_reviews(self, obj):
        reviews = obj.reviews.all().order_by('-created_at')
        return VideoReviewSerializer(reviews, many=True).data

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'