from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.utils import timezone
from plotter import Plotter
try:
	import json
except ImportError:
	import simplejson as json

def results(request):
	
	dataset = request.POST['dataset']
	get_summary = True if 'get_summary' in request.POST.keys() else False
	get_histogram = True if 'get_histogram' in request.POST.keys() else False
	get_time_series = True if 'get_time_series' in request.POST.keys() else False

	if dataset == 'bio' or dataset == 'gro':
		table = 'piedata'
	elif dataset == 'bio_all':
		table = 'hja_ws1_test'
	else:
		table = 'kelp_grow_npp'
	
	P = Plotter()
	P.summary_stats()
	P.fetch_data()
	P.make_plots()
	
	summary = zip(
		P.summary['yearly'][table][dataset][2007].keys(), 
		P.summary['yearly'][table][dataset][2007].values()
	)
	histogram = zip(P.hist['bin'][dataset], P.hist['percent'][dataset])
	
	time_series = zip(
		P.time_series[dataset]['year'],
		P.time_series[dataset]['mean'],
		P.time_series[dataset]['std']
	)
	
	return render(request, 'visual/results.html', {
		'dataset': dataset,
		'table': table,
		'get_summary': get_summary,
		'get_histogram': get_histogram,
		'get_time_series': get_time_series,
		'summary': summary,
		'num_bins': P.num_bins,
		'histogram': histogram,
		'time_series': time_series,
		'json_time_series': json.dumps(P.time_series),
		'data': P.data,
	})

def index(request):
	return render(request, 'visual/index.html')