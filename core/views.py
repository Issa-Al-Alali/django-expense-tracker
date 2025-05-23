from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import UserRegistrationSerializer, UserLoginSerializer, ExpenseSerializer, VideoCommentSerializer, VideoDetailSerializer, VideoLikeSerializer, VideoReviewSerializer, VideoSerializer, CategorySerializer
from .models import Income, Category, Expense, Video, VideoComment, VideoLike
from django.db import IntegrityError
from django.db.models.functions import ExtractMonth
from django.db.models import Sum, Q
from .serializers import IncomeSerializer
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.views import View
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth import login as auth_login, logout
from django.conf import settings
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
import requests
from .forms import RegistrationForm, LoginForm
import logging
logger = logging.getLogger(__name__)

from django.core.paginator import Paginator  # Import Paginator
from rest_framework.pagination import PageNumberPagination  # Import PageNumberPagination
from rest_framework import generics  # Import generics

from .forms import ProfilePictureForm  # Import the missing form

User = get_user_model()

class UserRegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)

            # Create an Income object with a budget_amount of 0 for the new user
            Income.objects.create(user=user, budget_amount=0)

            return Response({
                'user_id': str(user.id),
                'token': token.key
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'user_id': str(user.id),
                'token': token.key
            }, status=status.HTTP_200_OK)
        
        return Response({
            'error': serializer.errors.get('non_field_errors', ['Invalid credentials'])[0]
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    # NEW Income Views
class UserIncomeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Fetch the income for the authenticated user
        try:
            income = Income.objects.get(user=request.user)
            serializer = IncomeSerializer(income)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Income.DoesNotExist:
            return Response({"error": "Income not found for this user."}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        serializer = IncomeSerializer(data=request.data)

        if serializer.is_valid():
            try:
                # Pass the authenticated user instance to the save method
                serializer.save(user=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                return Response(
                    {"error": "A database integrity error occurred.", "details": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class IncomeDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def put(self, request, user_id):
        # Get the income object for the authenticated user and the provided user_id
        income = get_object_or_404(Income, user__id=user_id, user=request.user)
        
        # Update the income object with the provided data
        serializer = IncomeSerializer(income, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class AddExpenseView(APIView):
    parser_classes = (MultiPartParser, FormParser, JSONParser)  # Add all three parsers
    
    def post(self, request, user_id, category_name):
        user = get_object_or_404(User, id=user_id)
        category = get_object_or_404(Category, name=category_name)

        # Handle both form data and JSON
        data = request.data.dict() if hasattr(request.data, 'dict') else request.data.copy()
        data['category'] = category.id

        serializer = ExpenseSerializer(data=data, context={
            'user': user,
            'request': request
        })

        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                return Response(
                    {"error": "Database error", "details": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ExpenseListView(APIView):
    def get(self, request, user_id):
        # Get the user
        user = get_object_or_404(User, id=user_id)

        # Filter expenses for the specific user
        queryset = Expense.objects.filter(user=user)

        # Filtering by year
        year = request.query_params.get('year')
        if year:
            queryset = queryset.filter(expense_date__year=year)

        # Filtering by month
        month = request.query_params.get('month')
        if month:
            queryset = queryset.filter(expense_date__month=month)

        # Filtering by category name
        category_name = request.query_params.get('category_name')
        if category_name:
            queryset = queryset.filter(category__name__iexact=category_name)

        # Sorting by amount
        sort = request.query_params.get('sort')
        if sort == 'asc':
            queryset = queryset.order_by('amount')
        elif sort == 'desc':
            queryset = queryset.order_by('-amount')

        # Serialize the data
        serializer = ExpenseSerializer(queryset, many=True)
        return Response(serializer.data)
    

class UpdateExpenseView(APIView):
    def put(self, request, expense_id):
        # Get the expense object
        expense = get_object_or_404(Expense, id=expense_id)

        # Update the expense with the provided data
        serializer = ExpenseSerializer(expense, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class DeleteExpenseView(APIView):
    def delete(self, request, expense_id):
        try:
            expense = Expense.objects.get(id=expense_id)
            expense.delete()
            return Response({'success': True}, status=status.HTTP_204_NO_CONTENT)
        except Expense.DoesNotExist:
            return Response({'success': False, 'error': 'Expense not found'}, status=status.HTTP_404_NOT_FOUND)
        

class MonthlyExpenseSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        year = request.query_params.get('year')
        if not year:
            return Response({'error': 'Year parameter is required'}, status=400)
        
        try:
            year = int(year)
        except ValueError:
            return Response({'error': 'Invalid year format'}, status=400)
        
        # Get monthly expenses for the user
        monthly_totals = Expense.objects.filter(
            user_id=user_id,
            expense_date__year=year
        ).annotate(
            month=ExtractMonth('expense_date')
        ).values('month').annotate(
            total=Sum('amount')
        ).order_by('month')
        
        # Create a dictionary with all months initialized to 0
        monthly_data = {month: 0 for month in range(1, 13)}
        
        # Update with actual data
        for entry in monthly_totals:
            monthly_data[entry['month']] = float(entry['total'])
        
        # Prepare response
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        return Response({
            'labels': month_names,
            'data': [monthly_data[month] for month in range(1, 13)]
        })

class CategoryExpenseSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        # Get expenses grouped by category
        category_totals = Expense.objects.filter(
            user_id=user_id
        ).values(
            'category__name'
        ).annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        # Prepare response
        labels = []
        data = []
        
        for entry in category_totals:
            labels.append(entry['category__name'])
            data.append(float(entry['total']))
        
        return Response({
            'labels': labels,
            'data': data
        })           

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    
    def get(self, request):
        user = request.user
        return Response({
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'profile_picture': request.build_absolute_uri(user.profile_picture.url) if user.profile_picture else None
        })
    
    def put(self, request):
        user = request.user
        
        if 'profile_picture' in request.FILES:
            # Delete old profile picture if exists
            if user.profile_picture:
                try:
                    user.profile_picture.delete(save=False)
                except:
                    pass  # Handle potential file deletion errors
            
            user.profile_picture = request.FILES['profile_picture']
            user.save()
            
            # Return the updated profile with the new picture URL
            profile_picture_url = request.build_absolute_uri(user.profile_picture.url) if user.profile_picture else None
            
            # The frontend should update the session with this new URL
            return Response({
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'profile_picture': profile_picture_url
            })
        
        return Response({"error": "No profile picture provided"}, status=400)

# Video list view with search and pagination
class VideoListAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        query = request.GET.get('search', '')
        videos_list = Video.objects.all().order_by('-created_at')
        
        # Search functionality
        if query:
            videos_list = videos_list.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query)
            )
            
        # Pagination
        paginator = PageNumberPagination()
        paginator.page_size = 6
        result_page = paginator.paginate_queryset(videos_list, request)
        serializer = VideoSerializer(result_page, many=True, context={'request': request})
        
        return paginator.get_paginated_response(serializer.data)

# Video detail API view
class VideoDetailAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, video_id):
        video = get_object_or_404(Video, id=video_id)
        
        # Optionally increment view count
        video.view_count += 1
        video.save()
        
        serializer = VideoDetailSerializer(video, context={'request': request})
        return Response(serializer.data)

# Video comment API endpoints
class VideoCommentListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Only logged in users can comment
    
    def get(self, request, video_id):
        video = get_object_or_404(Video, id=video_id)
        comments = video.comments.all().order_by('-created_at')
        serializer = VideoCommentSerializer(comments, many=True)
        return Response(serializer.data)
    
    def post(self, request, video_id):
        video = get_object_or_404(Video, id=video_id)
        
        serializer = VideoCommentSerializer(
            data={'video': video.id, 'content': request.data.get('content')},
            context={'request': request}
        )
        
        if serializer.is_valid():
            comment = serializer.save()
            
            # Update comment count on video
            video.comments_count = video.comments.count()
            video.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Video comment detail API endpoints (update, delete)
class VideoCommentDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_object(self, comment_id, user):
        comment = get_object_or_404(VideoComment, id=comment_id)
        
        # Check if the user is the comment owner
        if comment.user != user:
            return None
        return comment
    
    def put(self, request, comment_id):
        comment = self.get_object(comment_id, request.user)
        if not comment:
            return Response(
                {"detail": "You don't have permission to edit this comment."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = VideoCommentSerializer(
            comment,
            data={'video': comment.video.id, 'content': request.data.get('content')},
            context={'request': request},
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, comment_id):
        comment = self.get_object(comment_id, request.user)
        if not comment:
            return Response(
                {"detail": "You don't have permission to delete this comment."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        video = comment.video
        comment.delete()
        
        # Update comment count on video
        video.comments_count = video.comments.count()
        video.save()
        
        return Response(status=status.HTTP_204_NO_CONTENT)

# Video like toggle API endpoint
class VideoLikeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, video_id):
        video = get_object_or_404(Video, id=video_id)

        # Pass the video instance to the serializer data
        serializer = VideoLikeSerializer(
            data={'video': video.id}, # Pass video ID for validation
            context={'request': request}
        )

        if serializer.is_valid():
            # The save() method in the serializer handles the creation/deletion and count update
            serializer.save()

            # Re-fetch the video to get the updated likes_count
            video.refresh_from_db()

            # Return updated like status
            return Response({
                'liked': VideoLike.objects.filter(user=request.user, video=video).exists(),
                'likes_count': video.likes_count
            }, status=status.HTTP_200_OK) # Use 200 OK for success

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Video review API endpoints
class VideoReviewCreateUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, video_id):
        video = get_object_or_404(Video, id=video_id)
        
        serializer = VideoReviewSerializer(
            data={
                'video': video.id,
                'rating': request.data.get('rating'),
                'review_text': request.data.get('review_text', '')
            },
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Template view for videos page
class VideoListView(View):
    def get(self, request):
        query = request.GET.get('search', '')
        videos_list = Video.objects.all().order_by('-created_at')
        
        # Search functionality
        if query:
            videos_list = videos_list.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query)
            )
        
        # Pagination
        paginator = Paginator(videos_list, 6)  # Show 6 videos per page
        page_number = request.GET.get('page', 1)
        videos = paginator.get_page(page_number)
        
        return render(request, 'core/videos.html', {
            'videos': videos,
            'search_query': query
        })

    # Frontend views

class RegistrationView(View):
    def get(self, request):
        form = RegistrationForm()
        return render(request, 'core/register.html', {'form': form})

    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            response = requests.post(
                f'{settings.API_BASE_URL}/users/',
                json={
                    'username': form.cleaned_data['username'],
                    'email': form.cleaned_data['email'],
                    'password': form.cleaned_data['password']
                }
            )
            if response.status_code == 201:  # User successfully registered
                return redirect('login')
            elif response.status_code == 400:  # Handle API errors (e.g., user already exists)
                errors = response.json()
                for field, error_messages in errors.items():
                    for error in error_messages:
                        form.add_error(field, error)
        return render(request, 'core/register.html', {'form': form})

class LoginView(View):
    def get(self, request):
        form = LoginForm()
        return render(request, 'core/login.html', {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            response = requests.post(
                f'{settings.API_BASE_URL}/users/login/',
                json={
                    'email': form.cleaned_data['email'],
                    'password': form.cleaned_data['password']
                }
            )
            if response.status_code == 200:  # Login successful
                response_data = response.json()
                try:
                    request.session['token'] = response_data['token']
                    request.session['user_id'] = response_data['user_id']
                    
                    # Fetch user profile to get profile picture URL
                    profile_response = requests.get(
                        f"{settings.API_BASE_URL}/users/profile/",
                        headers={'Authorization': f"Token {response_data['token']}"}
                    )
                    
                    if profile_response.status_code == 200:
                        profile_data = profile_response.json()
                        if profile_data.get('profile_picture'):
                            request.session['profile_picture_url'] = profile_data['profile_picture']
                    
                    return redirect('dashboard')
                except KeyError:
                    form.add_error(None, "Invalid response from the server.")
            elif response.status_code in [400, 401]:  # Invalid credentials or unauthorized
                try:
                    error_message = response.json().get('error', "Invalid email or password.")
                except ValueError:
                    error_message = "Invalid email or password."
                form.add_error(None, error_message)
            else:  # Handle unexpected errors
                form.add_error(None, "An unexpected error occurred. Please try again.")
        return render(request, 'core/login.html', {'form': form})

class LandingPageView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        return render(request, 'core/landing_page.html')
    

class LogoutView(View):
    def get(self, request):
        # Clear the session data
        if 'token' in request.session:
            del request.session['token']
        if 'user_id' in request.session:
            del request.session['user_id']
        if 'profile_picture_url' in request.session:
            del request.session['profile_picture_url']
        
        # Perform Django logout
        logout(request)
        
        # Redirect to login page
        return redirect('login')
  
    
class BaseView(View):
    def get(self, request):
        return render(request, 'core/base.html')
    
class HomeView(View):
    def get(self, request):
        return render(request, 'core/home.html')
    
method_decorator(login_required, name='dispatch')
class DashboardView(View):
    def get(self, request):
        return render(request, "core/dashboard.html")
    
def income_list(request):
    token = request.session.get("token")  # Retrieve the token from the session
    user_id = request.session.get("user_id")  # Retrieve the user_id from the session

    if not token:
        messages.error(request, "You are not authenticated. Please log in again.")
        return redirect("login")

    headers = {"Authorization": f"Token {token}"}

    if request.method == "POST":
        # Handle income update
        budget_amount = request.POST.get("budget_amount")
        data = {"budget_amount": budget_amount}

        # Send the updated income to the API
        response = requests.put(f"{settings.API_BASE_URL}/incomes/{user_id}/", headers=headers, json=data)

        if response.status_code == 200:  # Income updated successfully
            messages.success(request, "Income updated successfully!")
        else:  # Handle errors
            messages.error(request, "Failed to update income. Please try again.")
        return redirect("frontend-income-list")

    # Handle GET request to fetch the user's current income
    response = requests.get(f"{settings.API_BASE_URL}/incomes/", headers=headers)
    if response.status_code == 200:
        income = response.json()  # Fetch the current income details
    else:
        income = None
        messages.error(request, "Failed to fetch income details. Please try again.")

    return render(request, "core/income_list.html", {"income": income})

class ExpensesPageView(View):
    template_name = "core/expenses.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        if isinstance(context, HttpResponseRedirect):
            return context
        return render(request, self.template_name, context)

    def get_context_data(self):
        # Debug: Print session data
        print(f"Session data: {dict(self.request.session)}")
        
        # Get authentication data
        token = self.request.session.get('token')
        user_id = self.request.session.get('user_id')
        
        print(f"Token: {token}, User ID: {user_id}")  # Debug
        
        if not token or not user_id:
            messages.error(self.request, "You are not authenticated. Please log in again.")
            return redirect("login")
        
        # Set headers with authentication token
        headers = {'Authorization': f'Token {token}'}
        
        # Get filter parameters
        year = self.request.GET.get('year')
        month = self.request.GET.get('month')
        category_name = self.request.GET.get('category_name')
        sort = self.request.GET.get('sort')  # Get the sort parameter
        
        # Build API URL (MUST include user_id)
        api_url = f"{settings.API_BASE_URL}/expenses/{user_id}/"
        params = {}
        if year: params['year'] = year
        if month: params['month'] = month
        if category_name: params['category_name'] = category_name
        if sort: params['sort'] = sort  # Add sort parameter to the API request
        
        print(f"Making request to: {api_url} with params: {params}")  # Debug
        
        # Initialize default context values
        expenses = []
        api_categories = []
        income = 0  # Default income value
        
        # Fetch expenses from API
        try:
            response = requests.get(api_url, params=params, headers=headers)
            print(f"API response: {response.status_code}")  # Debug
            
            if response.status_code == 200:
                expenses = response.json()
            else:
                messages.error(self.request, "Failed to fetch expenses. Please try again.")
            
            # Fetch categories from API for dropdown
            categories_response = requests.get(f"{settings.API_BASE_URL}/categories/")
            api_categories = categories_response.json() if categories_response.status_code == 200 else []
            
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")  # Debug
            messages.error(self.request, "Error connecting to the server. Please try again.")
        
        # Fetch income for the user
        try:
            income_response = requests.get(f"{settings.API_BASE_URL}/incomes/", headers=headers)
            if income_response.status_code == 200:
                income_data = income_response.json()
                income = float(income_data.get('budget_amount', 0))  # Convert to float for comparison
            else:
                messages.error(self.request, "Failed to fetch income details.")
        except requests.exceptions.RequestException as e:
            print(f"Income request error: {e}")  # Debug
            messages.error(self.request, "Error connecting to the server while fetching income.")
        
        # Get categories directly from database (original functionality)
        orm_categories = Category.objects.all()
        
        # Return context dictionary
        return {
            'expenses': expenses,
            'categories': orm_categories,  # Maintain original ORM categories
            'api_categories': api_categories,  # Also include API categories if needed
            'income': income,  # Add income to the context
            'filters': {
                'year': year,
                'month': month,
                'category_name': category_name,
                'sort': sort  # Include sort in filters
            }
        }

class AddExpenseViewFront(View):
    def post(self, request):
        # Get authentication token and user_id from session
        token = request.session.get('token')
        user_id = request.session.get('user_id')  # Get the user_id from session
        
        if not token or not user_id:
            return JsonResponse({'success': False, 'errors': 'Authentication required. Please log in again.'}, status=401)
            
        # Parse JSON data from request body
        import json
        try:
            data = json.loads(request.body)
            category_id = data.get('category')
            
            # Get the category name for the API call
            category = get_object_or_404(Category, id=category_id)
            category_name = category.name
            
            # Prepare data for the API call
            api_data = {
                'amount': data.get('amount'),
                'description': data.get('description'),
                'expense_date': data.get('expense_date'),
                'location': data.get('location')
            }
            
            # Set up headers with authentication token
            headers = {
                'Authorization': f'Token {token}',
                'Content-Type': 'application/json'
            }
            
            # Make API request with the user_id from session
            response = requests.post(
                f"{settings.API_BASE_URL}/expenses/add/{user_id}/{category_name}/",
                json=api_data,
                headers=headers
            )
            
            if response.status_code == 201:
                return JsonResponse({'success': True})
            
            # Return detailed error information
            return JsonResponse({
                'success': False, 
                'errors': response.json() if response.content else "Error communicating with the API"
            }, status=response.status_code)
        
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'errors': "Invalid JSON data"}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'errors': str(e)}, status=500)

class UpdateExpenseViewFront(View):
    def post(self, request, expense_id):
        # Get authentication token and user_id from session
        token = request.session.get('token')
        user_id = request.session.get('user_id')  # Add this line
        
        if not token or not user_id:  # Check for user_id too
            return JsonResponse({'success': False, 'errors': 'Authentication required. Please log in again.'}, status=401)
            
        # Rest of your code...
            
        # Parse JSON data from request body
        import json
        try:
            data = json.loads(request.body)
            
            # Prepare data for the API call
            api_data = {
                'amount': data.get('amount'),
                'description': data.get('description'),
                'expense_date': data.get('expense_date'),
                'location': data.get('location'),
                'category': data.get('category')
            }
            
            # Set up headers with authentication token
            headers = {
                'Authorization': f'Token {token}',
                'Content-Type': 'application/json'
            }
            
            # Make API request with authentication
            response = requests.put(
                f"{settings.API_BASE_URL}/expenses/update/{expense_id}/",
                json=api_data,
                headers=headers
            )
            
            if response.status_code == 200:
                return JsonResponse({'success': True})
            
            # Return detailed error information
            return JsonResponse({
                'success': False, 
                'errors': response.json() if response.content else "Error communicating with the API"
            }, status=response.status_code)
        
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'errors': "Invalid JSON data"}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'errors': str(e)}, status=500)
        
class ProfileView(View):
    def get(self, request):
        # Check if user is authenticated
        token = request.session.get('token')
        user_id = request.session.get('user_id')
        
        if not token or not user_id:
            messages.error(request, "Authentication required. Please log in again.")
            return redirect('login')
            
        headers = {'Authorization': f'Token {token}'}
        
        try:
            # Get user profile data
            response = requests.get(f"{settings.API_BASE_URL}/users/profile/", headers=headers)
            if response.status_code == 200:
                user_data = response.json()
                form = ProfilePictureForm()
                return render(request, 'core/profile.html', {'user_data': user_data, 'form': form})
            else:
                messages.error(request, "Failed to fetch user profile.")
                return redirect('dashboard')
        except requests.exceptions.RequestException:
            messages.error(request, "Error connecting to the server.")
            return redirect('dashboard')
    
    def post(self, request):
        token = request.session.get('token')
        user_id = request.session.get('user_id')
        
        if not token or not user_id:
            messages.error(request, "Authentication required. Please log in again.")
            return redirect('login')
            
        form = ProfilePictureForm(request.POST, request.FILES)
        if form.is_valid():
            # Create a multipart form data request
            headers = {'Authorization': f'Token {token}'}
            files = {'profile_picture': request.FILES['profile_picture']}
            
            try:
                response = requests.put(
                    f"{settings.API_BASE_URL}/users/profile/",
                    headers=headers,
                    files=files
                )
                
                if response.status_code == 200:
                    # Update the profile picture URL in the session
                    response_data = response.json()
                    if response_data.get('profile_picture'):
                        request.session['profile_picture_url'] = response_data['profile_picture']
                    
                    messages.success(request, "Profile picture updated successfully!")
                else:
                    messages.error(request, "Failed to update profile picture.")
            except requests.exceptions.RequestException:
                messages.error(request, "Error connecting to the server.")
                
        return redirect('profile')

class VideoListView(View):
    def get(self, request):
        query = request.GET.get('search', '')
        videos_list = Video.objects.all().order_by('-created_at')
        
        # Search functionality
        if query:
            videos_list = videos_list.filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query)
            )
        
        # Pagination
        paginator = Paginator(videos_list, 6)  # Show 6 videos per page
        page_number = request.GET.get('page', 1)
        videos = paginator.get_page(page_number)
        
        return render(request, 'core/videos.html', {
            'videos': videos,
            'search_query': query
        })
    
class CategoryList(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer