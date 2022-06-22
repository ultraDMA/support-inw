from rest_framework import routers

from support.views import TicketCommentView, TicketView

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'ticket', TicketView, basename='ticket')
router.register(r'comment', TicketCommentView, basename='comment')

urlpatterns = router.urls
