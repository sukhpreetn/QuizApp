from django.db import models
from datetime import datetime

# Create your models here.
class Quiz(models.Model):
    quiz_name                        = models.CharField(max_length=100,default='')
    quiz_OrgIdentifier               = models.CharField(max_length=40,default='')
    quiz_questions                   = models.TextField(null=True)
    quiz_noofquest                   = models.IntegerField(default=0)

    def __str__(self):
        return self.quiz_name + "_" + self.quiz_OrgIdentifier

class Question(models.Model):
    q_subject                    = models.CharField(max_length=40)
    q_cat                        = models.CharField(max_length=40)
    q_rank                       = models.CharField(max_length=20)
    q_text                       = models.TextField(null=True,default='')
    q_option1                    = models.CharField(max_length=200,default='')
    q_option2                    = models.CharField(max_length=200,default='')
    q_option3                    = models.CharField(max_length=200,default='')
    q_option4                    = models.CharField(max_length=200,default='')
    q_answer                     = models.CharField(max_length=20)
    q_ask_time                   = models.DateTimeField(default=datetime.now, blank=True)
    no_times_ques_served         = models.IntegerField(default=0)
    no_times_anwered_correctly   = models.IntegerField(default=0)
    no_times_anwered_incorrectly = models.IntegerField(default=0)
    difficulty_score             = models.DecimalField(default=0,max_digits = 5, decimal_places = 2)

    def __str__(self):
        return self.q_text

class Answer(models.Model):
    question                     = models.ForeignKey(Question, on_delete=models.CASCADE)
    ans_option                   = models.CharField(max_length=20)
    is_correct                   = models.BooleanField(default=False)
    ans_time                     = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.ans_option

class Result(models.Model):
    c_user                      = models.CharField(max_length=100)
    c_quiz_name                 = models.CharField(max_length=100,default='')
    c_tot_score                 = models.IntegerField(default=0)
    c_cat_scores                = models.TextField(null=True,default=0)
    c_comment                   = models.TextField(null=True,default='')
    c_new_quest                 = models.TextField(null=True,default='')
    c_attempt_date              = models.DateTimeField(default=datetime.now, blank=True)

    def __str__(self):
        return self.c_user



