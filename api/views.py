from app.bases.rest.views import *
from api.models import User

__all__ = ['EchoView', 'AccountsViewSet']


class EchoView(GenericView):

    def get(self, *args, **kwargs):
        return {"resp": "Hi!"}, 200


class AccountsViewSet(GenericView, ViewSetMixin, CreateMixin):
    model = User


