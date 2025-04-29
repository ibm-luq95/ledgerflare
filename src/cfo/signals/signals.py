from django.dispatch import Signal

# Define custom signals for the Post model
cfo_pre_soft_delete = Signal()
cfo_post_soft_delete = Signal()