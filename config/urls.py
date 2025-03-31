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
from core.views import (
    UpdateExpenseView,
    UserRegistrationView, 
    UserLoginView,
    UserIncomeView,
    IncomeDetailView,
    RegistrationView,
    LoginView,
    LandingPageView,
    LogoutView,
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
    # Frontend views
    path('register/', RegistrationView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('landing/', LandingPageView.as_view(), name='landing_page'),
    path('base/', BaseView.as_view(), name='base'),
    path('', LoginView.as_view(), name='home'),  # Default to login
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('incomes-list/', income_list, name='frontend-income-list'),  # Add this line  # Add this line
    path('logout/', LogoutView.as_view(), name='logout'),
    path('expenses/view', ExpensesPageView.as_view(), name='frontend-expense-list'),  # Add this line
    path('expenses/add/', AddExpenseViewFront.as_view(), name='add_expense'),
    path('expenses/update/<uuid:expense_id>/', UpdateExpenseViewFront.as_view(), name='update_expense'),
]