from django.db import models

class Scrape(models.Model):
	
	scrape_url = models.TextField()
	scrape_date = models.DateTimeField('date scraped')
	scrape_keep_markup = models.BooleanField()