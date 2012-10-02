import djang.forms


class PackageForm(djang.forms.ModelForm):
    class Meta(object):
        model = Package
        exclude = ['name']
