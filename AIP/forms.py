from django.db import models

from django import forms
from .models import Question

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        labels = {
            'q_subject'                     : 'Subject',
            'q_cat'                         : 'Category',
            'q_rank'                        : 'Rank',
            'q_text'                        : 'Question',
            'q_option1'                     : 'Answer Option1',
            'q_option2'                     : 'Answer Option2',
            'q_option3'                     : 'Answer Option3',
            'q_option4'                     : 'Answer Option4',
            'q_answer'                      : 'Answer',
        }

        fields = ('q_subject','q_cat','q_rank','q_text','q_option1','q_option2','q_option3','q_option4','q_answer')
        #fields = '__all__'