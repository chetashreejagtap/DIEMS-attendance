def is_coordinator(user):
    return user.is_authenticated and user.is_coordinator

