from app.bases import GenericView

__all__ = ['EchoView']


class EchoView(GenericView):

    def get(*args, **kwargs):
        return {"resp": "Hi!"}, 200
