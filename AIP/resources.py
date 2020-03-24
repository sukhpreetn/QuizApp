from .models import Question

class PersonResource(resources.ModelResource):
    class Meta:
        model = Question