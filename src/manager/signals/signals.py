from django.dispatch import Signal

# Define custom signals for the Post model
manager_pre_soft_delete = Signal()
manager_post_soft_delete = Signal()