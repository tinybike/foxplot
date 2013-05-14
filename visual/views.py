from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.utils import timezone
from plotter import Plotter
try:
	import json
except ImportError:
	import simplejson as json
from math import log, sqrt
from numpy import isnan

def results(request):
	
	get_histogram = True if 'get_histogram' in request.POST.keys() else False
	get_time_series = True if 'get_time_series' in request.POST.keys() else False
	log_y = True if 'log_y' in request.POST.keys() else False
	hist_log_y = True if 'hist_log_y' in request.POST.keys() else False
	hist_log_x = True if 'hist_log_x' in request.POST.keys() else False
	show_errors = True if 'show_errors' in request.POST.keys() else False
	hist_show_errors = True if 'hist_show_errors' in request.POST.keys() else False
	select_stat = request.POST['select_stat']
	select_span = request.POST['select_span']
	num_bins = int(request.POST['num_bins'])
	align_start = True if 'align_start' in request.POST.keys() else False
	bio_or_npp = request.POST['bio_or_npp']
	
	table_dict = {
		'bio': 'piedata',
		'gro': 'piedata',
		'npp_wet': 'kelp_grow_npp',
		'bio_all': 'hja_ws1_test',
		'anpp': 'hja_ws1_test',
	}
	#if dataset == 'bio' or dataset == 'gro':
	#	data_label = 'PIE' # Plum Island Ecosystem: estuary (Spartina spp.)
	#elif dataset == 'bio_all':
	#	data_label = 'HJA' # HJ Andrews: old-growth forest (Psuedotsuga menziesii)
	#else:
	#	data_label = 'SBC' # Santa Barbara Coastal: sea vegetation (Macrocystis spp.)
	
	P = Plotter(bins=num_bins, align=align_start)
	P.summary_stats()
	P.fetch_data()
	P.make_plots()

	if select_span == 'year':
		time_series = P.time_series
		field_list = ['bio', 'gro', 'bio_all', 'npp_wet', 'anpp']
	else:
		time_series = P.monthly_time_series
		field_list = ['bio', 'gro', 'npp_wet']
	
	keep_fields = ['gro', 'npp_wet', 'anpp'] if bio_or_npp == 'npp' \
		else ['bio', 'bio_all']
	field_list = filter(
		None, [f if f in keep_fields else None for f in field_list]
	)

	# Create prettier labels for the plots...
	field_labels = {
		'bio': 'PIE',
		'gro': 'PIE',
		'bio_all': 'HJA',
		'npp_wet': 'SBC',
		'anpp': 'HJA',
	}
	stat_labels = {
		'max': 'Maximum',
		'mean': 'Mean',
		'median': 'Median',
		'min': 'Minimum',
		'quartile_1': '1st quartile',
		'quartile_3': '3rd quartile',
	}

	json_time_series = {}
	json_histogram = {}
	total_summary, total_labels = [], []
	for field in field_list:
		# Get standard errors and zip time-series data into JSON-like dict 
		# (for Flot)
		time_key = 'yearly' if select_span == 'year' else 'aggregate'
		this_summary = P.summary[time_key][table_dict[field]][field]
		values = time_series[field][select_stat]
		if show_errors:
			N = [this_summary[j]['N'] for j in this_summary.keys()]
			error_bars = [j/sqrt(N[i]-1) \
				for i, j in enumerate(time_series[field]['std'])]
			period = time_series[field][select_span]
			data = zip(period, values, error_bars)
		else:
			period = time_series[field][select_span]
			data = zip(period, values)
		data = [list(j) for j in data]
		json_time_series[field] = {
			'label': field_labels[field], 
			'data': data,
		}
		
		# Zip histogram data into JSON-like dict (for Flot)
		hist_x = P.hist['bin'][field]
		bar_width = P.hist['bin'][field][1] - P.hist['bin'][field][0]
		hist_bar_width = [bar_width for j in hist_x]
		if hist_log_y:
			hist_y = [None if j == 0 else j for j in P.hist['percent'][field]]
		else:
			hist_y = P.hist['percent'][field]
		if hist_show_errors:
			hist_errors = [0 if isnan(j) else j for j in P.hist['std'][field]]
			hist_data = zip(hist_x, hist_y, hist_errors)
		else:
			hist_errors = [0 for j in hist_y]
			hist_data = zip(hist_x, hist_y, hist_errors, hist_bar_width)
		hist_data = [list(j) for j in hist_data]
		json_histogram[field] = {
			'label': field_labels[field],
			'data': hist_data,
		}
		
		this_total = P.summary['total'][time_key][table_dict[field]][field]
		total_labels.append(field_labels[field])
		total_summary.append([
			[
				#field_labels[field], 
				stat_labels[key], 
				repr(round(this_total[key]['mean']*1000.0)/1000.0), 
				repr(round(this_total[key]['std']*1000.0)/1000.0)
			] 
			for key in this_total.keys()
		])
	summary = zip(total_labels, total_summary)
	
	bar_width = P.hist['bin']['npp_wet'][1] - P.hist['bin']['npp_wet'][0]
	
	bio_or_npp_dict = {
		'biomass': '<strong>Biomass</strong> (g/m<sup>2</sup>)',
		'npp': '<strong>NPP</strong> (g/m<sup>2</sup>/year)',
	}
	bio_or_npp_label = bio_or_npp_dict[bio_or_npp]
	
	if bio_or_npp == 'biomass':
		json_histogram_1 = json_histogram['bio']
		json_histogram_2 = json_histogram['bio_all']
		json_histogram_3 = None
	else:
		json_histogram_1 = json_histogram['gro']
		json_histogram_2 = json_histogram['npp_wet']
		json_histogram_3 = json_histogram['anpp']
		
	return render(request, 'visual/results.html', {
		#'dataset': dataset,
		#'table': table,
		#'get_summary': get_summary,
		#'get_histogram': get_histogram,
		#'get_time_series': get_time_series,
		'select_stat': select_stat,
		'select_span': select_span,
		'show_errors': show_errors,
		'hist_show_errors': hist_show_errors,
		'log_y': log_y,
		'bar_width': bar_width,
		'hist_log_y': hist_log_y,
		'hist_log_x': hist_log_x,
		#'bin_sizes': bin_sizes,
		'summary': summary,
		'num_bins': P.num_bins,
		'bio_or_npp': bio_or_npp,
		'bio_or_npp_label': bio_or_npp_label,
		#'histogram': histogram,
		#'time_series': time_series,
		'json_time_series': json.dumps(json_time_series),
		'json_histogram': json.dumps(json_histogram),
		'json_histogram_1': json.dumps(json_histogram_1),
		'json_histogram_2': json.dumps(json_histogram_2),
		'json_histogram_3': json.dumps(json_histogram_3),
	})

def fetch(request):
	return render(request, 'visual/fetch.html')