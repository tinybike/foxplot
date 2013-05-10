#!usr/bin/env python
"""
Statistics and plotting tools for dataRonin ecological time-series data.

(c) Jack Peterson (jack@tinybike.net), 5/7/2013
"""
from __future__ import division
from django.db import connection
from numpy import percentile, mean, median, std, histogram
from collections import OrderedDict
#from matplotlib import pyplot

class Plotter:

	def __init__(self, num_bins=25):
		self.cursor = connection.cursor()
		self.num_bins = num_bins
		self.summary, self.data, self.hist, self.time_series = {}, {}, {}, {}
		self.monthly_time_series = {}

	def summary_stats(self):
		"""
		Get yearly and aggregated summary statistics for numerical fields, 
		then place into dictionary.
		"""
		self.summary['yearly'] = {
			'hja_ws1_test': self.yearly_stats('hja_ws1_test', ['bio_all', 'anpp']),
			'kelp_grow_npp': self.yearly_stats('kelp_grow_npp', ['npp_wet']),
			'piedata': self.yearly_stats('piedata', ['gro', 'bio']),
		}
		self.summary['aggregate'] = {
			'kelp_grow_npp': self.aggregated_stats('kelp_grow_npp', ['npp_wet']),
			'piedata': self.aggregated_stats('piedata', ['gro', 'bio']),
		}

	def aggregated_stats(self, dataset, fields):
		"""
		Calculates statistics aggregated across years for npp_wet, gro, and
		bio: gro and bio are monthly data, npp_wet is seasonal data.
		"""
		summary = {}
		period_label = 'mm' if dataset == 'piedata' else 'season'
		
		# Find all unique months
		self.cursor.execute("SELECT DISTINCT `%s` FROM %s" % (period_label, dataset))
		periods = [row[0] for row in self.cursor.fetchall()]
		
		for field in fields:
			summary[field] = OrderedDict()
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
				self.cursor.execute(sql)
				
				# Adjust units for the npp_wet field, otherwise no adjustment is
				# needed
				adjustment = 3650 if field == 'npp_wet' else 1
				results = [row[0]*adjustment for row in self.cursor.fetchall()]
				
				# Calculate summary statistics
				summary[field][period] = {
					'min': min(results),
					'quartile_1': percentile(results, 25),
					'mean': mean(results),
					'median': median(results),
					'quartile_3': percentile(results, 75),
					'max': max(results),
					'std': std(results),
				}
		
		return summary
				
	def yearly_stats(self, dataset, fields):
		"""
		Calculates yearly statistics (min, 1st quartile, mean, median, 3rd quartile,
		max) for numerical data retrieved from the dataRonin database.
		"""
		summary = {}
		year_label = 'yy' if dataset == 'piedata' else 'year'
		
		# Find all unique years
		self.cursor.execute("SELECT DISTINCT `%s` FROM %s" % (year_label, dataset))
		years = [row[0] for row in self.cursor.fetchall()]

		for field in fields:
			summary[field] = OrderedDict()
			for year in years:
				self.cursor.execute(
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
				results = [row[0]*adjustment for row in self.cursor.fetchall()]

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
				
	def fetch_data(self):
		"""
		Fetch raw time series data from the dataRonin database.
		"""
		# Get full datasets from dataRonin database
		# 1. piedata table "PIE SPARTINA"
		self.cursor.execute(
			"SELECT `yy`, `mm`, `gro`, `bio` FROM piedata"
		)
		results = self.cursor.fetchall()
		self.data['piedata'] = {
			'yy': [row[0] for row in results],
			'mm': [row[1] for row in results],
			'gro': [row[2] for row in results],
			'bio': [row[3] for row in results],
		}
		# 2. kelp_grow_npp table "SBC MACROCYSTIS"
		self.cursor.execute(
			"SELECT `year`, `season`, `npp_wet` FROM kelp_grow_npp"
		)
		results = self.cursor.fetchall()
		self.data['kelp_grow_npp'] = {
			'year': [row[0] for row in results],
			'season': [row[1] for row in results],
			'npp_wet': [row[2]*3650 for row in results],
		}
		# 3. hja_ws1_test table "HJA PSUEDOTSUGA"
		self.cursor.execute(
			"SELECT `year`, `bio_all`, `anpp` FROM hja_ws1_test"
		)
		results = self.cursor.fetchall()
		self.data['hja_ws1_test'] = {
			'year': [row[0] for row in results],
			'bio_all': [row[1]*0.01 for row in results],
			'anpp': [row[2]*0.01 for row in results],
		}

	def make_plots(self):
		"""
		Calculate histograms and time series.
		"""	
		self.hist['percent'], self.hist['bin'] = {}, {}
		dataset_field = zip(
			[
				'hja_ws1_test', 'piedata', 'kelp_grow_npp', 
				'hja_ws1_test', 'piedata'
			],
			['bio_all', 'bio', 'npp_wet', 'anpp', 'gro']
		)
		for dataset, field in dataset_field:
			self.hist['percent'][field], self.hist['bin'][field] = \
				self.get_histogram(dataset, field)
			self.time_series[field] = self.get_time_series(dataset, field)
			if field in ['bio', 'gro', 'npp_wet']:
				self.monthly_time_series[field] = \
					self.get_time_series(dataset, field, 'aggregate')
		
	def get_histogram(self, dataset, field):
		"""
		Create and return histogram for specified dataset and field.
		"""
		counts, bin_edges = histogram(
			self.data[dataset][field], bins=self.num_bins
		)
		total_count = sum(counts)
		percentages = [100*count/total_count for count in counts]
		bin_centers = [0.5*(bin_edges[j]+bin_edges[j+1]) \
			for j in xrange(self.num_bins)]
		return percentages, bin_centers

	def get_time_series(self, dataset, field, aggregate='yearly'):
		"""
		Return time series, per year aggregated over months.
		"""
		time_series = {}
		time_key = 'year' if aggregate == 'yearly' else 'month'
		time_series[time_key] = \
			[span for span in self.summary[aggregate][dataset][field]]
		stat_list = ['mean', 'std', 'median', 'quartile_1', 'quartile_3', 'max', 'min']
		for stat in stat_list:
			time_series[stat] = [
				self.summary[aggregate][dataset][field][span][stat] for span in \
					self.summary[aggregate][dataset][field]
			]
		return time_series
			
#pyplot.hist(data['hja_ws1_test']['bio_all'], bins=num_bins)
#pyplot.show()

if __name__ == '__main__':
	"""
	The user should be able to select which datasets he/she wants to include so that he can put in just one data set or two data sets for the first two (bio or bio_all or BOTH bio and bio_all) and up to all three data sets for the third (ANPP orNPP_wet or gro or ANPP AND NPP_wet or ANPP AND gro or gro and NPP_wet or all three)
	"""
	P = Plotter()
	P.summary_stats()
	P.fetch_data()
	P.make_plots()