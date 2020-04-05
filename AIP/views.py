import datetime
from datetime import timedelta
import os
import pprint
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from smtplib import SMTP
from django.db.models import Count
import pandas as pd
from django.conf import settings
from django.http import HttpResponse, request, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, get_list_or_404, redirect, resolve_url
from django.utils.datastructures import MultiValueDictKeyError
from django.core.files.storage import FileSystemStorage
from django.views import generic
from django.urls import reverse
from .models import Question, Answer, Result,Quiz,Attendance,Trainee_Attendance
from django.http import HttpResponse
import json
import random
import csv, io
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from .forms import QuestionForm
from django.contrib.auth.models import User
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,UpdateView)


def index(request):
    quizname = request.session.get('quizname',None)
    #quizattend = request.session['fromattend']
    #return HttpResponse(quizname)

    if quizname is None:
        #settings.LOGIN_REDIRECT_URL = '/pickskill'
        #return render(request, 'AIP/index.html')
        settings.LOGIN_REDIRECT_URL = '/'
        return render(request, 'AIP/success.html')
    else:
        return redirect('AIP:takequiz', pk=quizname)


def pickskill(request):
    request.session['user'] = request.user.get_full_name()
    request.session['email'] = request.user.email
    user = request.session['user']
    email = request.session['email']
    Result.objects.create(c_user=user,c_email=email)
    category_count = Question.objects.values('q_rank').order_by('q_rank').annotate(count=Count('q_rank'))
    cat_count = list(category_count)
    categories = []
    for item in cat_count:
        cnt = str(item['count'])
        line = item['q_rank'] + ' (' + cnt + ')'
        categories.append(line)

    context = {'user':user,'categories':categories}
    return render(request, 'AIP/pickskill.html',context)

def begin(request):
    if request.method == 'POST':
        subject = request.POST['skill']
        rank = request.POST['proficiency']
        context = {'subject': subject, 'rank': rank}
        request.session['skill'] = subject
        request.session['proficiency'] = rank
        request.session['curr_difficulty_score'] = 1
        request.session['total_q_asked'] = 1
        request.session['total_q_ans_correct'] = 0
        request.session['counter'] = 0
        cat_dict = {'Introduction': 0, 'Syntax': 0, 'OOPS': 0, 'NativeDataTypes': 0, 'FileAndExceptionHandling': 0,
                    'Function': 0, 'Advanced': 0,'All': 0}
        request.session['cat_dict'] = cat_dict
        request.session['score'] = 0

        if rank == 'Adaptive':
            return render(request, 'AIP/begin.html', context)
        else:
            return render(request, 'AIP/beginsimple.html', context)


def quizsimple(request):
    subject = request.session['skill']
    rank = request.session['proficiency']
    total_q_asked = request.session['total_q_asked']
    total_q_ans_correct = request.session['total_q_ans_correct']
    counter = request.session['counter']
    score = request.session['score']
    cat_dict = request.session['cat_dict']
    user = request.session['user']

    questions = Question.objects.filter(q_subject=subject, q_rank=rank)
    max = Question.objects.filter(q_subject=subject, q_rank=rank).count()
    ind = random.randint(1, max)
    #return  HttpResponse(ind)
    question = questions[ind]
    #question = questions[0]
    context = {'total_q_asked': total_q_asked, 'question': question}
    if request.method == 'POST':
        option = request.POST.get('options')
        q = Question(question.pk)
        ans = Answer()
        ans.question = q
        question.no_times_ques_served += 1

        total_q_asked += 1
        if question.q_answer == option:
            ans.ans_option = option
            ans.is_correct = True
            question.no_times_anwered_correctly += 1
            total_q_ans_correct += 1
            cat_dict[question.q_cat] += 1
            ans.save()
        else:
            ans.ans_option = option
            ans.is_correct = False
            question.no_times_anwered_incorrectly += 1
            ans.save()

        Question.objects.filter(pk=q.pk).update(no_times_ques_served=question.no_times_ques_served,
                                                no_times_anwered_correctly=question.no_times_anwered_correctly,
                                                no_times_anwered_incorrectly=question.no_times_anwered_incorrectly)
        if counter == (max-1) or request.POST.get('END') == 'STOP':
            score1 = (total_q_ans_correct / (total_q_asked - 1)) * 100
            score = round(score1)
            cat_scores = json.dumps(cat_dict)
            total_ans_incorrect = ((total_q_asked - 1) - total_q_ans_correct)
            Result.objects.filter(c_user=user).update(c_tot_score=score)
            Result.objects.filter(c_user=user).update(c_cat_scores=cat_scores,c_total_q_asked=(total_q_asked-1),c_total_ans_correct=total_q_ans_correct,c_total_ans_incorrect=total_ans_incorrect)
            score_context = {'score': score, 'cat_dict': cat_dict, 'total_q_asked': total_q_asked - 1,
                             'total_q_ans_correct': total_q_ans_correct}
            return render(request, 'AIP/report.html', score_context)

        counter += 1
        request.session['score'] = score
        request.session['counter'] = counter
        request.session['total_q_asked'] = total_q_asked
        request.session['total_q_ans_correct'] = total_q_ans_correct
        request.session['cat_dict'] = cat_dict

        questions = Question.objects.filter(q_subject=subject, q_rank=rank)
        max = Question.objects.filter(q_subject=subject, q_rank=rank).count()
        ind = random.randint(1, max)
        question = questions[ind]
        context = {'total_q_asked': total_q_asked, 'question': question}
        return render(request, 'AIP/quizsimple.html', context)
    else:
        # this is GET flow of 1st question
        return render(request, 'AIP/quizsimple.html', context)


def quiz(request):
    subject = request.session['skill']
    rank = request.session['proficiency']
    curr_difficulty_score = request.session['curr_difficulty_score']
    total_q_asked = request.session['total_q_asked']
    total_q_ans_correct = request.session['total_q_ans_correct']
    score = request.session['score']
    cat_dict = request.session['cat_dict']
    user = request.session['user']
    counter = request.session['counter']

    questions = Question.objects.filter(q_subject=subject, q_rank=rank).filter(difficulty_score__gt=curr_difficulty_score).order_by('difficulty_score')
    question = questions[0]
    context = {'total_q_asked': total_q_asked, 'question': question}

    if request.method == 'POST':
        option = request.POST.get('options')
        q = Question(question.pk)
        ans = Answer()
        ans.question = q
        question.no_times_ques_served += 1
        total_q_asked += 1
        if question.q_answer == option:
            ans.ans_option = option
            ans.is_correct = True
            question.no_times_anwered_correctly += 1
            total_q_ans_correct += 1
            cat_dict[question.q_cat] += 1
            ans.save()
        else:
            ans.ans_option = option
            ans.is_correct = False
            question.no_times_anwered_incorrectly += 1
            ans.save()

        Question.objects.filter(pk=q.pk).update(no_times_ques_served=question.no_times_ques_served,
                                                no_times_anwered_correctly=question.no_times_anwered_correctly,
                                                no_times_anwered_incorrectly=question.no_times_anwered_incorrectly,
                                                difficulty_score=curr_difficulty_score)

        if counter == 4 or request.POST.get('END') == 'STOP':
            score1 = (total_q_ans_correct / (total_q_asked - 1)) * 100
            score = round(score1)
            cat_scores = json.dumps(cat_dict)
            total_ans_incorrect = ((total_q_asked - 1) - total_q_ans_correct)

            Result.objects.filter(c_user=user).update(c_tot_score=score)
            Result.objects.filter(c_user=user).update(c_cat_scores=cat_scores, c_total_q_asked=(total_q_asked-1),
                                                      c_total_ans_correct=total_q_ans_correct,
                                                      c_total_ans_incorrect=total_ans_incorrect)
            score_context = {'score': score, 'cat_dict': cat_dict, 'total_q_asked': total_q_asked - 1,
                             'total_q_ans_correct': total_q_ans_correct}
            return render(request, 'AIP/report.html', score_context)

        counter += 1
        request.session['counter'] = counter
        request.session['score'] = score
        request.session['total_q_asked'] = total_q_asked
        request.session['total_q_ans_correct'] = total_q_ans_correct
        request.session['curr_difficulty_score'] = curr_difficulty_score
        request.session['cat_dict'] = cat_dict

        # curr_difficulty_score = question.no_times_anwered_incorrectly / question.no_times_anwered_incorrectly + question.no_times_anwered_correctly
        curr_difficulty_score = question.no_times_anwered_incorrectly / question.no_times_ques_served
        questions = Question.objects.filter(q_subject=subject, q_rank=rank).filter(
            difficulty_score__gt=curr_difficulty_score).order_by('difficulty_score')
        question = questions[0]
        context = {'total_q_asked': total_q_asked, 'question': question}
        return render(request, 'AIP/quiz.html', context)
    else:
        return render(request, 'AIP/quiz.html', context)


def comment(request):
    context = {}
    user = request.session['user']
    if request.method == 'POST':
        comment = request.POST.get('comment')
        Result.objects.filter(c_user=user).update(c_comment=comment)
        context['commsuccess'] = "Comment added . Thank You !"
        return render(request, 'AIP/report.html', context)


def question(request):
    context = {}
    user = request.session['user']
    if request.method == 'POST':
        question = request.POST.get('question')
        Result.objects.filter(c_user=user).update(c_new_quest=question)
        context['quessuccess'] = "Question added . Thank You !"
        return render(request, 'AIP/report.html', context)


def upload(request):
    context = {}
    if request.method == 'POST':
        try:
            uploaded_file = request.FILES['document']
        except MultiValueDictKeyError:
            return HttpResponse("Please upload a file")

        fs = FileSystemStorage()
        name = fs.save(uploaded_file.name, uploaded_file)
        context['url'] = fs.url(name)
    return render(request, 'AIP/report.html', context)


def logout(request):
    try:
        del request.session['user']
    except KeyError:
        pass

    return render(request, 'AIP/index.html')

@permission_required('admin.can_add_log_entry')
def export(request):
    response = HttpResponse(content_type='text/csv')
    writer = csv.writer(response)
    writer.writerow(
        ['q_subject', 'q_cat', 'q_rank', 'q_text', 'q_option1', 'q_option2', 'q_option3', 'q_option4', 'q_answer',
         'q_ask_time', 'no_times_ques_served', 'no_times_anwered_correctly', 'no_times_anwered_incorrectly',
         'difficulty_score'])
    for data in Question.objects.all().values_list('q_subject', 'q_cat', 'q_rank', 'q_text', 'q_option1', 'q_option2',
                                                   'q_option3', 'q_option4', 'q_answer', 'q_ask_time',
                                                   'no_times_ques_served', 'no_times_anwered_correctly',
                                                   'no_times_anwered_incorrectly', 'difficulty_score'):
        writer.writerow(data)

    response['Content-Disposition'] = 'attachment; filename="questions.csv"'
    return response

@permission_required('admin.can_add_log_entry')
def questionupload(request):
    # template = question_upload.html

    prompt = {
        'order': 'Order of CSV should be Question,Option1,Option2,Option3,Option4,answer option'
    }
    if request.method == "GET":
        return render(request, 'AIP/question_upload.html', prompt)

    csv_file = request.FILES['file']
    if not csv_file.name.endswith('.csv'):
        messages.error(request, 'This is not a cvs file')

    data_set = csv_file.read().decode('UTF-8')
    io_string = io.StringIO(data_set)
    next(io_string)
    for column in csv.reader(io_string, delimiter='|'):
        _, created = Question.objects.update_or_create(
            q_subject=column[0],
            q_cat=column[1],
            q_rank=column[2],
            q_text=column[3],
            q_option1=column[4],
            q_option2=column[5],
            q_option3=column[6],
            q_option4=column[7],
            q_answer=column[8]
        )
        context = {}
    return render(request, 'AIP/question_upload.html', context)


@permission_required('admin.can_add_log_entry')
def scores(request,pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    quiznm = quiz.quiz_OrgIdentifier

    results = Result.objects.filter(c_quiz_name=pk).order_by('-c_attempt_date')

    if not results:
        context = {'results': results, 'quiz': 'Quiz Not Found'}
    else:
        context = {'results':results,'quiznm':quiznm}
    return render(request, 'AIP/scores.html', context)

def searchquiz(request,pk):
    results = Result.objects.filter(c_quiz_name = pk).order_by('-c_attempt_date')
    if not results:
        context = {'results': results, 'quiz': 'Quiz Not Found'}
    else:
        context = {'results':results,'quiz':pk}
    return render(request, 'AIP/scores.html', context)

@permission_required('admin.can_add_log_entry')
def quizzes(request):
    quizzes = list(Quiz.objects.all())
    context = {'quizzes': quizzes}
    return render(request, 'AIP/quizzes.html',context)

def addquiz(request):
    return  render(request, 'AIP/quizadd.html')

def add(request):
    subject = request.session['subject']
    category = request.session['category']
    count = request.session['count']
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save()
            question.save()

            if count == 2:
                questions = list(Question.objects.all())
                context = {'subject': subject, 'category': category, 'questions': questions}
                return render(request, 'AIP/addquestion.html', context)

        count += 1
        request.session['count'] = count
        form = QuestionForm()
        return render(request, 'AIP/add.html',  {'form': form})
    else:
        form = QuestionForm()
        return render(request, 'AIP/add.html', {'form': form})

def  addquestion(request):
    subject = request.POST['Subject']
    quizname = request.POST['quizname']
    request.session['subject'] = subject
    request.session['quizname'] = quizname
    request.session['questionlist'] = []
    request.session['count'] = 1
    request.session['countdrop'] = 1
    questions = list(Question.objects.all())
    context = {'subject': subject, 'questions': questions}
    return render(request, 'AIP/addquestion.html', context)

def addquestion1(request):
    selectedquestion = []
    subject = request.session['subject']
    quizname = request.session['quizname']
    if request.method == 'POST':
        for question in request.POST.getlist('questionchecked'):
            selectedquestion.append(int(question))

        q = Quiz()
        q.quiz_name = subject
        q.quiz_OrgIdentifier = quizname
        q.quiz_questions = selectedquestion
        q.quiz_noofquest = len(selectedquestion)
        q.save()
        quizzes = Quiz.objects.all()
        context = {'quizzes': quizzes}
        return render(request, 'AIP/quizzes.html', context)

def quizbucket(request):
    if request.user.is_authenticated:
        quizzes = Quiz.objects.all()
        context = {'quizzes': quizzes}
        request.session['user'] = request.user.get_full_name()
        user = request.session['user']
        Result.objects.create(c_user=user)
        request.session['q_no'] = 0
        request.session['total_q_asked'] = 1
        request.session['total_q_ans_correct'] = 0
        request.session['counter'] = 0
        cat_dict = {'Introduction': 0, 'Syntax': 0, 'OOPS': 0, 'NativeDataTypes': 0, 'FileAndExceptionHandling': 0,'Function': 0, 'Advanced': 0,'All':0}
        request.session['cat_dict'] = cat_dict
        request.session['score'] = 0
        return  render(request, 'AIP/quizbucket.html',context)
    else:
        return render(request, 'AIP/index.html')

def check_expiry():
    datetimeFormat = '%Y-%m-%d %H:%M:%S'

    date1 = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    queryset  =  Attendance.objects.all()
    reg_time = [p.expire_time for p in queryset]

    date2 = reg_time[0].strftime("%Y-%m-%d %H:%M:%S")
    diff = datetime.datetime.strptime(date2, datetimeFormat) \
           - datetime.datetime.strptime(date1, datetimeFormat)
    print("expire_time :" , date2)
    print("login time" , date1)
    print("difference", diff)
    print(diff.total_seconds())
    if diff.total_seconds() < 5 :
        return  True
    else:
        return  False

def takequiz(request, pk):
    if request.user.is_authenticated:
        expired =  check_expiry()
        if expired == True:
            return render(request, 'AIP/notfound.html')

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        request.session['user'] = request.user.get_full_name()
        user = request.session['user']
        request.session['email'] = request.user.email
        email = request.session['email']
        Trainee_Attendance.objects.create(trainee_email=email,login_time=now)
        quiz = get_object_or_404(Quiz, pk=pk)
        quiz_str = json.loads(quiz.quiz_questions)
        total = len(quiz_str)
        if request.method == 'POST':
            q_no = request.session['q_no']
            total_q_asked = request.session['total_q_asked']
            total_q_ans_correct = request.session['total_q_ans_correct']
            counter = request.session['counter']
            score = request.session['score']
            cat_dict = request.session['cat_dict']
            user = request.session['user']
            question = get_object_or_404(Question, pk=quiz_str[q_no])
            context = {'total_q_asked': total_q_asked, 'question': question}

            option = request.POST.get('options')
            q = Question(question.pk)
            ans = Answer()
            ans.question = q
            question.no_times_ques_served += 1
            total_q_asked += 1
            if question.q_answer == option:
                ans.ans_option = option
                ans.is_correct = True
                question.no_times_anwered_correctly += 1
                total_q_ans_correct += 1
                cat_dict[question.q_cat] += 1
                ans.save()
            else:
                ans.ans_option = option
                ans.is_correct = False
                question.no_times_anwered_incorrectly += 1
                ans.save()

            Question.objects.filter(pk=q.pk).update(no_times_ques_served=question.no_times_ques_served,
                                                    no_times_anwered_correctly=question.no_times_anwered_correctly,
                                                    no_times_anwered_incorrectly=question.no_times_anwered_incorrectly)

            q_no += 1
            if q_no == total or request.POST.get('END') == 'STOP':
                score1 = (total_q_ans_correct / (total_q_asked - 1)) * 100
                total_ans_incorrect = ((total_q_asked-1) - total_q_ans_correct)
                score = round(score1)
                cat_scores = json.dumps(cat_dict)
                Result.objects.create(c_user=user,c_email=email, c_quiz_name=pk,c_tot_score=score,c_cat_scores=cat_scores,
                                      c_total_q_asked=(total_q_asked-1),c_total_ans_correct=total_q_ans_correct,
                                      c_total_ans_incorrect=total_ans_incorrect)

                score_context = {'score': score, 'cat_dict': cat_dict, 'total_q_asked': total_q_asked - 1,
                                 'total_q_ans_correct': total_q_ans_correct}

                send_mail(email,score,cat_dict)
                return render(request, 'AIP/report.html', score_context)

            request.session['q_no'] = q_no
            request.session['score'] = score
            request.session['total_q_asked'] = total_q_asked
            request.session['total_q_ans_correct'] = total_q_ans_correct
            request.session['cat_dict'] = cat_dict

            question = get_object_or_404(Question, pk=quiz_str[q_no])
            quizname = request.session['quizname']
            context = {'total_q_asked': total_q_asked, 'question': question,'quizname':quizname}
            return render(request, 'AIP/quizsimple.html', context)

        else:
            request.session['q_no'] = 0
            request.session['total_q_asked'] = 1
            request.session['total_q_ans_correct'] = 0
            request.session['counter'] = 0
            cat_dict = {'Introduction': 0, 'Syntax': 0, 'OOPS': 0, 'NativeDataTypes': 0, 'FileAndExceptionHandling': 0,
                        'Function': 0, 'Advanced': 0, 'All': 0}
            request.session['cat_dict'] = cat_dict
            request.session['score'] = 0
            q_no = request.session['q_no']
            total_q_asked = request.session['total_q_asked']
            question = get_object_or_404(Question, pk=quiz_str[q_no])
            quizname = request.session['quizname']
            context = {'total_q_asked': total_q_asked, 'question': question,'quizname':quizname}
            return render(request, 'AIP/quizsimple.html', context)
    else:
        request.session['quizname'] = '{}'.format(pk)
        quizname = request.session['quizname']
        context = {'quizname':quizname}
        settings.LOGIN_REDIRECT_URL = '/'
        return render(request, 'AIP/index.html',context)

def send_mail(email,score,cat_dict):
    print(email)
    score_data= pd.DataFrame(
        {
            'category score':cat_dict,
        }
    )
    #recipients = [email,'sukhpreetn@gmail.com','ravi92teja@gmail.com']
    recipients = [email, 'sukhpreetn@gmail.com']
    emaillist = [elem.strip().split(',') for elem in recipients]
    msg = MIMEMultipart()
    msg['Subject'] = "Quiz Hop Scores"
    msg['From'] = 'ravi92teja@gmail.com'

    html = """\
    <html>
      <head></head>
      <body>
        Total Score is : {0} 
        <p></p>
        Category wise split of Scores :
        {1}
      </body>
    </html>
    """.format(score,score_data.to_html())

    part1 = MIMEText(html, 'html')
    msg.attach(part1)

    server = smtplib.SMTP('smtp.gmail.com',587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login('pyvebdev@gmail.com', 'snwylifpbqtszbxe')
    server.sendmail(msg['From'], emaillist , msg.as_string())


@permission_required('admin.can_add_log_entry')
def review(request):
    questions = Question.objects.all()
    total = len(questions)
    context = {'questions': questions, 'total': total}
    return render(request, 'AIP/compare.html', context)


@permission_required('admin.can_add_log_entry')
def reviewquiz(request,pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    quiz_str = json.loads(quiz.quiz_questions)
    total = len(quiz_str)
    questions = []

    for qid in quiz_str:
        ques = get_object_or_404(Question,pk=qid)
        questions.append(ques)

    context = {'questions': questions,'total':total,'subject':questions[0].q_subject,'category':questions[0].q_cat}
    return render(request, 'AIP/compare.html',context)


def markattendance(request, pk):
    if request.method == 'POST':

        trainer = request.POST.get('trainer')
        trainees = request.POST.get('trainees')
        expires = request.POST.get('expires')

        Attendance.objects.create(trainer_name=trainer, trainee_emails=trainees, expire_time=expires)
        trainee_list = trainees.split("\r\n")
        send_mail_attendance(trainee_list,pk)

        #request.session['fromattend'] = 'attend'
        return redirect('AIP:showattendance', pk=pk)

    else:
        return render(request, 'AIP/markattendance.html')

def showattendance(request, pk):
    results = Trainee_Attendance.objects.all()
    context = {'results':results,'pk':pk}
    return render(request, 'AIP/showattendance.html',context)

def send_mail_attendance(trainee_list,pk):
    q_name  = str(pk)
    #url = "http://sukhpreetn.pythonanywhere.com/"
    url = "http://127.0.0.1:8000/"

    recipients = trainee_list
    emaillist = [elem.strip().split(',') for elem in recipients]
    msg = MIMEMultipart()
    msg['Subject'] = "Quiz Hop : Mark your attendance"
    msg['From'] = 'ravi92teja@gmail.com'

    html = """\
    <html>
      <head></head>
      <body>
       Login <a href= {0}> here </a>
        
      </body>
    </html>
    """.format(url)
    part1 = MIMEText(html, 'html')
    msg.attach(part1)

    server = smtplib.SMTP('smtp.gmail.com',587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login('pyvebdev@gmail.com', 'snwylifpbqtszbxe')
    server.sendmail(msg['From'], emaillist , msg.as_string())
