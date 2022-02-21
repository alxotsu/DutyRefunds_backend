from app.bases import *
from api.serializers import *

__all__ = ['EchoView', 'AccountsViewSet']


class EchoView(GenericView):

    def get(self, *args, **kwargs):
        return {"resp": "Hi!"}, 200


class AccountsViewSet(GenericView, ViewSetMixin, CreateMixin):
    serializer_class = UserSerializer


