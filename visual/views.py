from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.utils import timezone
from plotter import Plotter
try:
	import json
except ImportError:
	import simplejson as json
from math import log

def results(request):
	
	#dataset = request.POST['dataset']
	#get_summary = True if 'get_summary' in request.POST.keys() else False
	get_histogram = True if 'get_histogram' in request.POST.keys() else False
	get_time_series = True if 'get_time_series' in request.POST.keys() else False
	log_y = True if 'log_y' in request.POST.keys() else False
	show_errors = True if 'show_errors' in request.POST.keys() else False
	select_stat = request.POST['select_stat']
	#select_span = request.POST['select_span']
	select_span = 'month'
	
	#if dataset == 'bio' or dataset == 'gro':
	#	table = 'piedata'
	#elif dataset == 'bio_all':
	#	table = 'hja_ws1_test'
	#else:
	#	table = 'kelp_grow_npp'
	
	P = Plotter()
	P.summary_stats()
	P.fetch_data()
	P.make_plots()
	
	#summary = zip(
	#	P.summary['yearly'][table][dataset][2007].keys(), 
	#	P.summary['yearly'][table][dataset][2007].values()
	#)
	histogram = zip(P.hist['bin']['bio'], P.hist['percent']['bio'])
	
	#time_series = zip(
	#	P.time_series[dataset]['year'],
	#	P.time_series[dataset]['mean'],
	#	P.time_series[dataset]['std']
	#)
	
	if select_span == 'year':
		time_series = P.time_series
		field_list = ['bio', 'gro', 'bio_all', 'npp_wet', 'anpp']
	else:
		time_series = P.monthly_time_series
		field_list = ['bio', 'gro', 'npp_wet']
	
	json_time_series = {}
	json_histogram = {}
	for field in field_list:
		if log_y:
			values = [None if j == 0 else log(j) \
				for j in time_series[field][select_stat]]
			data = zip(time_series[field][select_span], values)
		else:
			values = time_series[field][select_stat]
			if show_errors:
				error_bars = time_series[field]['std']
				data = zip(time_series[field][select_span], values, error_bars)
			else:
				data = zip(time_series[field][select_span], values)
		data = [list(j) for j in data]
		json_time_series[field] = {'label': field, 'data': data}
		
		hist_data = zip(P.hist['bin'][field], P.hist['percent'][field])
		hist_data = [list(j) for j in hist_data]
		json_histogram[field] = {'label': field, 'data': hist_data}
	
	return render(request, 'visual/results.html', {
		#'dataset': dataset,
		#'table': table,
		#'get_summary': get_summary,
		#'get_histogram': get_histogram,
		#'get_time_series': get_time_series,
		'select_span': select_span,
		'show_errors': show_errors,
		'log_y': log_y,
		#'summary': summary,
		'num_bins': P.num_bins,
		#'histogram': histogram,
		#'time_series': time_series,
		'json_time_series': json.dumps(json_time_series),
		'json_histogram': json.dumps(json_histogram),
	})

def index(request):
	return render(request, 'visual/index.html')