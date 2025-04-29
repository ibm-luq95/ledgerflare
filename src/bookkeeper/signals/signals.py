from django.dispatch import Signal

# Define custom signals for the Post model
bookkeeper_pre_soft_delete = Signal()
bookkeeper_post_soft_delete = Signal()