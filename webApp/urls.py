from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin

admin.autodiscover()

import views

urlpatterns = patterns('',
    url(r'^pis', views.pis),
    url(r'^words', views.words, { 'titles': False }),
    url(r'^projects', views.projects),
    url(r'^posters', views.posters),
    url(r'^posterpresenters', views.posterpresenters),
    url(r'^pigraph', views.pigraph),
    url(r'^institutions', views.institutions),                    
    url(r'^institution/(?P<institutionid>\d+)', views.institution),                    
    url(r'^profile/$', views.profile),
    url(r'^schedule/(?P<email>\S+)', views.schedule),
    url(r'^ratemeeting/(?P<rmid>\d+)/(?P<email>\S+)', views.ratemeeting),
    url(r'^submitrating/(?P<rmid>\d+)/(?P<email>\S+)', views.submitrating),
    url(r'^feedback/(?P<email>\S+)', views.after),
    url(r'^breakouts', views.breakouts),
    url(r'^breakout/(?P<bid>\d+)', views.breakout),
    url(r'^about', views.about),
    url(r'^buginfo', views.buginfo),
    url(r'^allrms', views.allrms),
    url(r'^allratings', views.allratings),
    url(r'^login', views.login),
    url(r'^logout', views.logout),
    url(r'^edit_home_page', views.edit_home_page),                       
    url(r'^pi/(?P<userid>\d+)', views.pi), # , name = 'pi'),
    url(r'^pi/(?P<email>\S+)', views.piEmail), # , name = 'pi'),
    url(r'^project/(?P<abstractid>\S+)', views.project, name = 'project'),
    url(r'^scope=(?P<scope>\w+)/(?P<url>.+)$', views.set_scope),
    url(r'^active=(?P<active>\d)/(?P<url>.+)$', views.set_active),
    url(r'^admin/', include(admin.site.urls)),
    (r'', include('django_browserid.urls')),
    url(r'^$', views.index, name = 'index'),
    ) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
