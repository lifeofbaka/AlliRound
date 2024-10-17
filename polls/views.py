from django.db.models.query import QuerySet
from django.shortcuts import render, get_list_or_404
from django.http import HttpResponse, HttpResponseRedirect # Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.db.models import F
from django.template import loader
from .models import Question, Choice
from django.views import generic
from  django.utils import timezone

class IndexView(generic.ListView): 
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
       "Return the last 5 objects by date"
       return Question.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")[:5]
    

class DetailView(generic.DetailView):
    model = Question
    template_name = "polls/detail.html"

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())


class ResultsView(generic.DetailView):
    model = Question
    template_name = "polls/results.html"



def index(request):
    # return HttpResponse("Hello, world. You're at the polls index.")
    latest_question_list = Question.objects.order_by("-pub_date")[:5]
    # template = loader.get_template("polls/index.html")
    context = {
        "latest_question_list" : latest_question_list,
    }
    # return HttpResponse(template.render(context, request))
    return render(request,"polls/index.html", context)


def detail(request, question_id):
    #try:
    #    q = Question.objects.get(pk=question_id)
    #except Question.DoesNotExist:
    #   raise Http404("Question Does Not Exist")
    # return HttpResponse("You're looking at question %s." % question_id)
    q = get_object_or_404(Question, pk=question_id)
    return render(request, "polls/detail.html", {"question": q})


def results(request, question_id): 
    q = get_object_or_404(Question, pk=question_id)
    return render(request, "polls/results.html", {"question" : q})
    # return HttpResponse("You're looking at the results for question %s." % question_id)


def vote(request, question_id):
    # return HttpResponse("Youre voting on question %s." % question_id)
    q = get_object_or_404(Question, pk=question_id)
    try: 
        selected_choice = q.choice_set.get(pk=request.POST["choice"])
    except(KeyError, Choice.DoesNotExist):
        return render(
                      request, 
                      "polls/detail.html", 
                      {
                            "question": q,
                            "error_message": "No Choice selected.",
                       },
                       )
    else:
        selected_choice.votes = F("votes") + 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse("polls:results", args=(q.id,)))

