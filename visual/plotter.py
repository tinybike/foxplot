#!usr/bin/env python
"""
Statistics and plotting tools for dataRonin ecological time-series data.

(c) Jack Peterson (jack@tinybike.net), 5/7/2013
"""
from __future__ import division
from django.db import connection
from numpy import percentile, mean, median, std, histogram
#from matplotlib import pyplot

def aggregated_stats(dataset, fields):
	"""
	Calculates statistics aggregated across years for npp_wet, gro, and
	bio: gro and bio are monthly data, npp_wet is seasonal data.
	"""
	cursor = connection.cursor()
	
	summary = {}
	period_label = 'mm' if dataset == 'piedata' else 'season'
	
	# Find all unique months
	cursor.execute("SELECT DISTINCT `%s` FROM %s" % (period_label, dataset))
	periods = [row[0] for row in cursor.fetchall()]
	
	for field in fields:
		summary[field] = {}
		for period in periods:
			if period_label == 'mm':
				sql = (
					"SELECT `%s` FROM %s WHERE `%s` = %i" 
					% (field, dataset, period_label, int(period))
				)
			else:
				sql = (
					"SELECT `%s` FROM %s WHERE `%s` = '%s'" 
					% (field, dataset, period_label, period)
				)
			cursor.execute(sql)
			
			# Adjust units for the npp_wet field, otherwise no adjustment is
			# needed
			adjustment = 3650 if field == 'npp_wet' else 1
			results = [row[0]*adjustment for row in cursor.fetchall()]
			
			# Calculate summary statistics
			summary[field][period] = {
				'min': min(results),
				'quartile_1': percentile(results, 25),
				'mean': mean(results),
				'median': median(results),
				'quartile_3': percentile(results, 75),
				'max': max(results),
			}
	return summary

def yearly_stats(dataset, fields):
	"""
	Calculates yearly statistics (min, 1st quartile, mean, median, 3rd quartile,
	max) for numerical data retrieved from the dataRonin database.
	"""
	cursor = connection.cursor()
	
	summary = {}
	year_label = 'yy' if dataset == 'piedata' else 'year'

	# Find all unique years
	cursor.execute("SELECT DISTINCT `%s` FROM %s" % (year_label, dataset))
	years = [row[0] for row in cursor.fetchall()]

	for field in fields:
		summary[field] = {}
		for year in years:			
			cursor.execute(
				"SELECT `%s` FROM %s WHERE `%s` = %i" 
				% (field, dataset, year_label, int(year))
			)

			# Adjust units for for the npp_wet, bio_all, or anpp fields.
			# Otherwise, no adjustment is needed.
			if field == 'npp_wet':
				adjustment = 3650
			elif field == 'bio_all' or field == 'anpp':
				adjustment = 0.01
			else:
				adjustment = 1
			results = [row[0]*adjustment for row in cursor.fetchall()]

			# Calculate summary statistics
			summary[field][year] = {
				'min': min(results),
				'quartile_1': percentile(results, 25),
				'mean': mean(results),
				'median': median(results),
				'quartile_3': percentile(results, 75),
				'max': max(results),
				'std': std(results),
			}
	return summary

def get_histogram(dataset, field, num_bins=10):
	"""
	Histograms of “bio” and “bio_all” with % on the Y and “g/m2” on the X. It also needs to be able to over lay these two on top of one another, which means that it will probably be log g/m2 on the X to be meaningful. There will be more measurements of the “bio_all” than the “bio” but that is okay, there would just be “skinnier bars”. On these bars should also be error bars the size of the standard deviation.  (NOTE: What is std dev here??)
	"""
	counts, bin_edges = histogram(data[dataset][field], bins=num_bins)
	total_count = sum(counts)
	percentages = [100*count/total_count for count in counts]
	bin_centers = [0.5*(bin_edges[j]+bin_edges[j+1]) for j in xrange(num_bins)]
	return percentages, bin_centers

def get_time_series(dataset, field, align=True):
	"""
	Time trajectories of “bio” and “bio_all,” also possible to be overlaid, and in 2 ways. (1) so that the “years” line up (so in this case there would not be much overlap) and (2) so that they both “start” at the same time, but the years do not line up, rather just the time since the “start” lines up. There will be more measurements of the “bio all” than the “bio” in both cases but that is okay,  and the time trajectories should be essentially “errorbars” of height “standard deviation” connected by solid lines.
	
	So that would be like month/year on the X and raw values (or log transformed values) of bio and bio_all on the y
	"""
	# Verify the ordering in the dict is correct!
	time_series = {}
	time_series['year'] = [year for year in summary_stats['yearly'][dataset][field]]
	for stat in ['mean', 'std']:
		time_series[stat] = [
			summary_stats['yearly'][dataset][field][year][stat] for year in \
			summary_stats['yearly'][dataset][field]
		]
	return time_series

def get_summary_stats():
	"""
	Calculate and return summary statistics dict.
	"""
	# Get yearly and aggregated summary statistics for numerical datasets
	summary_stats = {}
	summary_stats['yearly'] = {
		'hja_ws1_test': yearly_stats('hja_ws1_test', ['bio_all', 'anpp']),
		'kelp_grow_npp': yearly_stats('kelp_grow_npp', ['npp_wet']),
		'piedata': yearly_stats('piedata', ['gro', 'bio']),
	}
	summary_stats['aggregate'] = {
		'kelp_grow_npp': aggregated_stats('kelp_grow_npp', ['npp_wet']),
		'piedata': aggregated_stats('piedata', ['gro', 'bio']),
	}
	return summary_stats

def get_data():
	"""
	Fetch raw data from the database and place into a dict.
	"""
	cursor = connection.cursor()
	
	# Get full datasets from dataRonin database
	# 1. piedata table "PIE SPARTINA"
	data = {}
	cursor.execute("SELECT `yy`, `mm`, `gro`, `bio` FROM piedata")
	results = cursor.fetchall()
	data['piedata'] = {
		'yy': [row[0] for row in results],
		'mm': [row[1] for row in results],
		'gro': [row[2] for row in results],
		'bio': [row[3] for row in results],
	}
	# 2. kelp_grow_npp table "SBC MACROCYSTIS"
	cursor.execute("SELECT `year`, `season`, `npp_wet` FROM kelp_grow_npp")
	results = cursor.fetchall()
	data['kelp_grow_npp'] = {
		'year': [row[0] for row in results],
		'season': [row[1] for row in results],
		'npp_wet': [row[2]*3650 for row in results],
	}
	# 3. hja_ws1_test table "HJA PSUEDOTSUGA"
	cursor.execute("SELECT `year`, `bio_all`, `anpp` FROM hja_ws1_test")
	results = cursor.fetchall()
	data['hja_ws1_test'] = {
		'year': [row[0] for row in results],
		'bio_all': [row[1]*0.01 for row in results],
		'anpp': [row[2]*0.01 for row in results],
	}
	
	return data

def get_plots():
	"""
	Calculate and return histograms and time series.
	"""
	cursor = connection.cursor()
	
	# Calculate histograms and time series
	hist = {}
	hist['percent'] = {}
	hist['bin'] = {}
	time_series = {}
	num_bins = 25
	dataset_field = zip(
		['hja_ws1_test', 'piedata', 'kelp_grow_npp', 'hja_ws1_test', 'piedata'],
		['bio_all', 'bio', 'npp_wet', 'anpp', 'gro']
	)
	for dataset, field in dataset_field:
		hist['percent'][field], hist['bin'][field] = get_histogram(
			dataset, field, num_bins
		)
		time_series[field] = get_time_series(dataset, field)
	
	return hist, time_series

#pyplot.hist(data['hja_ws1_test']['bio_all'], bins=num_bins)
#pyplot.show()

if __name__ == '__main__':
	"""
	The user should be able to select which datasets he/she wants to include so that he can put in just one data set or two data sets for the first two (bio or bio_all or BOTH bio and bio_all) and up to all three data sets for the third (ANPP orNPP_wet or gro or ANPP AND NPP_wet or ANPP AND gro or gro and NPP_wet or all three)
	"""
	summary_stats = get_summary_stats()
	data = get_data()
	hist, time_series = get_plots()