from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
	# Examples:
	# url(r'^$', 'dataronin.views.home', name='home'),
	# url(r'^dataronin/', include('dataronin.foo.urls')),

	url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
	url(r'^admin/', include(admin.site.urls)),
	url(r'^visual/', include('visual.urls', namespace='visual')),
)
