# context_processors.py - create this file in your app directory
def user_profile(request):
    """Add user profile data to all templates."""
    context = {'profile_picture_url': None}
    
    if request.session.get('token') and request.session.get('user_id'):
        # Try to get profile picture URL from session
        profile_picture_url = request.session.get('profile_picture_url')
        if profile_picture_url:
            context['profile_picture_url'] = profile_picture_url
    
    return context