from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.utils import timezone
from plotter import Plotter

def results(request):
	return render(request, 'visual/results.html')

def index(request):
	return render(request, 'visual/index.html')