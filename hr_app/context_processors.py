from .models import Profile, Message

def user_profile(request):
    """
    Ensure `request.user.profile` is available in templates without raising
    RelatedObjectDoesNotExist. If the user is authenticated and doesn't have
    a Profile yet, create a default Employee profile (so templates that use
    `user.profile` won't crash).
    """
    context = {}
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        try:
            # Try to access related profile; create if missing
            profile = Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            profile = Profile.objects.create(user=user, user_type='Employee')
        # Attach to user object for template convenience (lives only for this request)
        setattr(user, 'profile', profile)
        context['profile'] = profile
        # عدد الرسائل غير المقروءة للمستخدم الحالي
        try:
            unread = Message.objects.filter(recipient=user, is_read=False).count()
        except Exception:
            unread = 0
        context['unread_messages_count'] = unread
    return context
