"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core.views import (
    CategoryList,
    UpdateExpenseView,
    UserRegistrationView, 
    UserLoginView,
    UserIncomeView,
    IncomeDetailView,
    RegistrationView,
    LoginView,
    LandingPageView,
    BaseView,
    DashboardView,
    income_list,
    AddExpenseView,
    ExpenseListView,
    ExpensesPageView,
    AddExpenseViewFront,
    UpdateExpenseViewFront,
    DeleteExpenseView,
    MonthlyExpenseSummaryView,
    CategoryExpenseSummaryView,
    UserProfileView,
    ProfileView,
    LogoutView,
    VideoListView,
    VideoListAPIView,
    VideoDetailAPIView,
    VideoCommentListCreateAPIView,
    VideoCommentDetailAPIView,
    VideoLikeAPIView,
    VideoReviewCreateUpdateAPIView,
)

urlpatterns = [
    # Admin and API endpoints
    path('admin/', admin.site.urls),
    path('users/', UserRegistrationView.as_view(), name='user-registration'),
    path('users/login/', UserLoginView.as_view(), name='user-login'),
    path('incomes/', UserIncomeView.as_view(), name='user-incomes'),
    path('incomes/<uuid:user_id>/', IncomeDetailView.as_view(), name='income-detail'),
    path('expenses/add/<uuid:user_id>/<str:category_name>/', AddExpenseView.as_view(), name='add-expense'),
    path('expenses/<uuid:user_id>/', ExpenseListView.as_view(), name='list-expenses'),  # Updated to include user_id
    path('expenses/update/<uuid:expense_id>/', UpdateExpenseView.as_view(), name='update-expense'),
    path('expenses/delete/<uuid:expense_id>/', DeleteExpenseView.as_view(), name='delete_expense'),
    path('expenses/<uuid:user_id>/monthly-summary/', MonthlyExpenseSummaryView.as_view(), name='monthly-summary'),
    path('expenses/<uuid:user_id>/category-summary/', CategoryExpenseSummaryView.as_view(), name='category-summary'),
    path('users/profile/', UserProfileView.as_view(), name='api-profile'),
    # Video-related API endpoints
    path('api/videos/', VideoListAPIView.as_view(), name='video-list-api'),
    path('api/videos/<uuid:video_id>/', VideoDetailAPIView.as_view(), name='video-detail-api'),
    
    # Video comments endpoints
    path('api/videos/<uuid:video_id>/comments/', VideoCommentListCreateAPIView.as_view(), name='video-comments'),
    path('api/comments/<uuid:comment_id>/', VideoCommentDetailAPIView.as_view(), name='comment-detail'),
    
    # Video likes endpoint
    path('api/videos/<uuid:video_id>/like/', VideoLikeAPIView.as_view(), name='video-like'),
    
    # Video reviews endpoint
    path('api/videos/<uuid:video_id>/review/', VideoReviewCreateUpdateAPIView.as_view(), name='video-review'),
    
    # Template view for videos page
    path('videos/', VideoListView.as_view(), name='video-list'),
    path('categories/', CategoryList.as_view(), name='category-list'),
    # Frontend views
    path('register/', RegistrationView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('landing/', LandingPageView.as_view(), name='landing_page'),
    path('base/', BaseView.as_view(), name='base'),
    path('', LoginView.as_view(), name='home'),  # Default to login
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('incomes-list/', income_list, name='frontend-income-list'),  # Add this line  # Add this line
    path('expenses/view', ExpensesPageView.as_view(), name='frontend-expense-list'),  # Add this line
    path('expenses/add/', AddExpenseViewFront.as_view(), name='add_expense'),
    path('expenses/update/<uuid:expense_id>/', UpdateExpenseViewFront.as_view(), name='update_expense'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('videos/', VideoListView.as_view(), name='video-list'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)