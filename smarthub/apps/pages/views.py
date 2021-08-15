from django.shortcuts import render
from django.views.generic import TemplateView

# Create your views here.
class Home(TemplateView):
    template_name = "pages/index.html"


class About(TemplateView):
    template_name = "pages/about.html"


class Help(TemplateView):
    template_name = "pages/help.html"
