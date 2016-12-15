import pkg_resources
from django import forms
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.http import require_http_methods

import importer.tasks


class RequiresForm(forms.Form):
    requirements = forms.CharField(widget=forms.Textarea,
            help_text='Paste your requirements.txt')
    recursive = forms.BooleanField(required=False, initial=True,
            help_text="Recurse through requirements' requirements, etc.")

    def clean_requirements(self):
        requirements = self.cleaned_data['requirements']
        for line in requirements.splitlines():
            if line.strip().startswith('['):
                raise forms.ValidationError("Sections aren't supported")

        try:
            list(pkg_resources.parse_requirements(requirements))
        except ValueError, e:
            raise forms.ValidationError(u' '.join(e))

        return requirements


@require_http_methods(['HEAD', 'GET', 'POST'])
def index(request):
    if request.method == 'POST':
        form = RequiresForm(request.POST)
        if form.is_valid():
            importer.tasks.ensure_requirements.delay(
                    form.cleaned_data['requirements'],
                    form.cleaned_data['recursive'])
            return HttpResponseRedirect('/')
    else:
        form = RequiresForm()

    return render_to_response('importer/index.html', {
        'title': 'Import packages from PyPI',
        'form': form,
    }, context_instance=RequestContext(request))
