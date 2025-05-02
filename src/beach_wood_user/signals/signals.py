from django.dispatch import Signal

# Define custom signals for the Post model
bwuser_pre_soft_delete = Signal()
bwuser_post_soft_delete = Signal()