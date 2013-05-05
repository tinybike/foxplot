from django.conf.urls import patterns, url
from visual import views

urlpatterns = patterns('',
	# ex: /visual/
	url(r'^$', views.index, name='index'),
	# ex: /visual/results/
	#url(r'^results/$', views.results, name='results'),
)