from django.contrib import admin
from  . models import Question , Answer,Result,Quiz

# Register your models here.
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Result)
admin.site.register(Quiz)


