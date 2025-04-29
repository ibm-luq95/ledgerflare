from django.dispatch import Signal

# Define custom signals for the Post model
assistant_pre_soft_delete = Signal()
assistant_post_soft_delete = Signal()