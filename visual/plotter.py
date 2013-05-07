#!usr/bin/env python
"""
For “NPP_wet” and “gro” and “bio” those same statistics, but calculated both on the scale of 1 year (so for each year, those measurements, for example: gro in 1999 1st quartile, mean, median etc., gro in 2000 1st quartile, mean, median, etc. as well as for “gro” for each month, but aggregated across years, for example, gro in all Januaries mean, median, etc., gro in all Julys, etc. For the “NPP_wet” the same idea, but for each season, so “NPP_wet in autumns” etc.

The units of these should be based on the units defined above. And hopefully the tables look kind of nice too.

(c) Jack Peterson (jack@tinybike.net), 5/5/2013
"""
from django.db import connection
from numpy import percentile, mean, median

def aggregated_stats(dataset, fields):
	"""
	Calculates statistics aggregated across years for npp_wet, gro, and
	bio: gro and bio are monthly data, npp_wet is seasonal data.
	"""
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
			}
	return summary

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

# Get yearly and aggregated summary statistics for numerical datasets
summary_stats = {}
summary_stats['yearly'] = {
	'hja': yearly_stats('hja_ws1_test', ['bio_all', 'anpp']),
	'kelp': yearly_stats('kelp_grow_npp', ['npp_wet']),
	'pie': yearly_stats('piedata', ['gro', 'bio']),
}
summary_stats['aggregate'] = {
	'kelp': aggregated_stats('kelp_grow_npp', ['npp_wet']),
	'pie': aggregated_stats('piedata', ['gro', 'bio']),
}

"""
Okay the second thing, I need the application to be able to plot some graphs.

BIOMASS

1.       Histograms of “bio” and “bio_all” with % on the Y and “g/m2” on the X. It also needs to be able to over lay these two on top of one another, which means that it will probably be log g/m2 on the X to be meaningful. There will be more measurements of the “bio_all” than the “bio” but that is okay, there would just be “skinnier bars”. On these bars should also be error bars the size of the standard deviation.

2.       Time trajectories of “bio” and “bio_all,” also possible to be overlaid, and in 2 ways. (1) so that the “years” line up (so in this case there would not be much overlap) and (2) so that they both “start” at the same time, but the years do not line up, rather just the time since the “start” lines up. There will be more measurements of the “bio all” than the “bio” in both cases but that is okay,  and the time trajectories should be essentially “errorbars” of height “standard deviation” connected by solid lines.

So that would be like month/year on the X and raw values (or log transformed values) of bio and bio_all on the y

NPP

3.       The same as the above but for “NPP_wet”, “ANPP”, and “gro.” In this case, the units will be g/m2/year, and this is where the assumption that “season is 3 months long” is valid. So histograms of the three with % on the y and “g/m2” on the X (possibly log g/m2) and time trajectories (month/year on the X and raw values or log-transformed values on the Y).

For all of the above, the user should be able to select which datasets he/she wants to include so that he can put in just one data set or two data sets for the first two (bio or bio_all or BOTH bio and bio_all) and up to all three data sets for the third (ANPP orNPP_wet or gro or ANPP AND NPP_wet or ANPP AND gro or gro and NPP_wet or all three)
"""