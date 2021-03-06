from captcha import fields as captcha_fields
from dapi import models
from django.contrib.auth import models as auth_models
from django.forms import util as formsutil
from django import forms
from django.utils import safestring
from social.apps.django_app.default import models as social_models


VERIFY_HELP_TEXT = 'Enter the {what} of this dap to verify the {why}'


class DivErrorList(formsutil.ErrorList):
    '''Make the form errors look better'''

    def __unicode__(self):
        return self.as_divs()

    def as_divs(self):
        if not self:
            return ''
        template = '''
        <div class="alert alert-danger">
          <a href="#" class="close" data-dismiss="alert">&times;</a>
          %s
        </div>
        '''
        return safestring.mark_safe(template % '\n'.join(['<p>%s</p>' % e for e in self]))


class BootstrapForm(forms.Form):
    '''A form that uses DivErrorList'''

    def __init__(self, *args, **kwargs):
        super(BootstrapForm, self).__init__(*args, **kwargs)
        self.error_class = DivErrorList
        for key in self.fields.keys():
            if key != 'file':
                self.fields[key].widget.attrs['class'] = 'form-control'


class BootstrapModelForm(forms.ModelForm):
    '''A model form that uses DivErrorList'''

    def __init__(self, *args, **kwargs):
        super(BootstrapModelForm, self).__init__(*args, **kwargs)
        self.error_class = DivErrorList
        for key in self.fields.keys():
            self.fields[key].widget.attrs['class'] = 'form-control'


class UploadDapForm(BootstrapForm):
    file = forms.FileField(label='')


class UserForm(BootstrapModelForm):

    class Meta:
        model = auth_models.User
        fields = ('username', 'email', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        if self.instance.profile.syncs.exists():
            self.fields['email'].help_text = \
                'Further fields cannot be edited, because at least one service is configured to' \
                'override those data on login. See below to disable it.'
            for field in 'email first_name last_name'.split():
                self.fields[field].widget.attrs['readonly'] = 'readonly'
                self.fields[field].widget.attrs['class'] += ' disabled'


class ProfileSyncForm(BootstrapModelForm):

    class Meta:
        model = models.Profile
        fields = ('syncs',)
        help_texts = {
            'syncs': 'Select services, that will override your name and e-mail on login.',
        }

    def __init__(self, *args, **kwargs):
        social_models.UserSocialAuth.__str__ = lambda self: self.get_backend().name
        super(ProfileSyncForm, self).__init__(*args, **kwargs)
        self.fields['syncs'].queryset = \
            social_models.UserSocialAuth.objects.filter(user=self.instance.user)


class ComaintainersForm(BootstrapModelForm):

    class Meta:
        model = models.MetaDap
        fields = ('comaintainers',)

    def __init__(self, *args, **kwargs):
        super(ComaintainersForm, self).__init__(*args, **kwargs)
        self.fields['comaintainers'].help_text = ''
        self.fields['comaintainers'].queryset = \
            auth_models.User.objects.exclude(id=self.instance.user_id)


class DeleteDapForm(BootstrapForm):
    verification = forms.CharField(
        max_length=200,
        help_text=VERIFY_HELP_TEXT.format(what='name', why='deletion'),
    )


class DeleteUserForm(BootstrapForm):
    verification = forms.CharField(
        max_length=30,
        help_text='Enter the username to confirm the deletion.',
    )


class DeleteVersionForm(BootstrapForm):
    verification_name = forms.CharField(
        max_length=200,
        help_text=VERIFY_HELP_TEXT.format(what='name', why='deletion'),
    )
    verification_version = forms.CharField(
        max_length=200,
        help_text=VERIFY_HELP_TEXT.format(what='version', why='deletion'),
    )


class ActivationDapForm(BootstrapModelForm):
    verification = forms.CharField(
        max_length=200,
        help_text=VERIFY_HELP_TEXT.format(what='name', why='(de)activation'),
    )

    class Meta:
        model = models.MetaDap
        fields = ('active',)


class TransferDapForm(BootstrapModelForm):
    verification = forms.CharField(
        max_length=200,
        help_text=VERIFY_HELP_TEXT.format(what='name', why='transfer'),
    )

    class Meta:
        model = models.MetaDap
        fields = ('user',)


class LeaveDapForm(BootstrapForm):
    verification = forms.CharField(
        max_length=200,
        help_text=VERIFY_HELP_TEXT.format(what='name', why='leaving'),
    )


class TagsForm(BootstrapModelForm):

    class Meta:
        model = models.MetaDap
        fields = ('tags',)


class ReportForm(BootstrapModelForm):

    class Meta:
        model = models.Report
        fields = ('problem', 'versions', 'message')
        help_texts = {
            'problem': 'Select the type of problem you want to report.',
            'versions': 'Where this problem occurs? If you are not sure, you can leave it blank.',
            'message': 'Describe the problem you want to report.',
        }

    def __init__(self, metadap, *args, **kwargs):
        super(ReportForm, self).__init__(*args, **kwargs)
        self.instance.metadap = metadap
        self.fields['versions'].queryset = models.Dap.objects.filter(metadap=metadap)


class ReportAnonymousForm(ReportForm):
    captcha = captcha_fields.CaptchaField()

    class Meta(ReportForm.Meta):
        fields = ReportForm.Meta.fields + ('email',)
        help_texts = ReportForm.Meta.help_texts
        help_texts['email'] = 'Optional. So we can inform you about the solution. ' \
            'We don\'t send spam or sell e-mail addresses.'
