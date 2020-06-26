from django import forms
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError

metric_choices = [('dist', 'Distance'),
                    ('time', 'Time'),
                    ('elev', 'Elevation'),
                    ('pace', 'Pace'),
                    ('avg_hr', 'Heartrate'),
                    ('intensity', 'Intensity')]

def validate_time(value):
    if value >= 60:
        raise ValidationError(
            message=f'{value} is not less than 60',
            params={'value': value},
        )

def validate_pos(value):
    if value < 0:
        raise ValidationError(
            message=f'{value} is not positive',
            params={'value': value},
        )

class DatePicker(forms.DateInput):
    input_type='date'

class DateForm(forms.Form):
    date_start = forms.DateField(required=True,
                                 label="",
                                 widget=DatePicker(attrs={
                                         'class': "form-control",
                                         'type': "date"
                                         }))
    date_end = forms.DateField(required=True,
                               label = "",
                               widget=DatePicker(attrs={
                                         'class': "form-control",
                                         'type': "date"
                                         }))

class QuickLinks(forms.Form):
    quick_links = forms.ChoiceField(
            choices=[
                    ('this_week', 'This Week'),
                    ('this_month', 'This Month'),
                    ('this_year', 'This Year')
                    ],
            widget=forms.RadioSelect(attrs={
                    'class': 'form-control',
                    'autocomplete': 'off',
                    }),
            label="",
            required=False
            )
    quick_items = forms.ChoiceField(
            choices=[(str(i), str(i)) for i in range(0, 25)],
            widget=forms.Select(attrs={
                    'class': 'form-control',
                    'value': '0'
                    }),
            label='',
            required=False)
    unit = forms.ChoiceField(
            choices=[('weeks', 'weeks'),
                     ('months', 'months'),
                     ('years', 'years')],
            widget=forms.Select(attrs={
                    'class': 'form-control',
                    'value': 'weeks'
                    }),
            label='',
            required=False)

class HorizRadioRenderer(forms.RadioSelect):
    def render(self):
            """Outputs radios"""
            return mark_safe(u'\n'.join([u'%s\n' % w for w in self]))

class MetricPicker(forms.Form):
    metric = forms.ChoiceField(
            choices=metric_choices,
            required=False,
            widget=forms.RadioSelect(attrs={
                    'style': 'margin-left: 20px;'
                    }),
            label=""
            )

class MetricPickerDashboard(forms.Form):
    choices = metric_choices + [('schedule', 'Schedule View')]
    metric = forms.ChoiceField(
            choices=choices,
            required=False,
            widget=forms.RadioSelect(attrs={
                    'style': 'margin-left: 20px;'
                    }),
            label=''
            )
    start = forms.HiddenInput()
    end = forms.HiddenInput()

class PersonalRecord(forms.Form):
    h = forms.IntegerField(widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'type': 'number',
            'placeholder': 'hours'
            }),
                             label='',
                             validators=[validate_pos])
    m = forms.IntegerField(widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'type': 'number',
            'placeholder': 'minutes'
            }),
                             label='',
                             validators=[validate_time, validate_pos])
    s = forms.IntegerField(widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'type': 'number',
            'placeholder': 'seconds'
            }),
                             label='',
                             validators=[validate_time, validate_pos])

    distance = forms.IntegerField(widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'type': 'number',
            'value': '0'
            }),
            label='',
            validators=[validate_pos])

    unit = forms.ChoiceField(
            widget=forms.Select(attrs={
                    'class': 'form-control',
                    'value': 'meters'
                    }),
            label='',
            choices=[
                    ('m', 'meters'),
                    ('km', 'kilometers'),
                    ('mi', 'miles')
                    ]
            )

class GraphPicker(forms.Form):
    graph = forms.ChoiceField(
            choices=[
                    ('Maps', 'Maps'),
                    ('Profiles', 'Profiles'),
                    ('Laps', 'Laps'),
                    ('Zones', 'Zones')
                    ],
            required=False,
            widget=forms.RadioSelect(attrs={
                    'style': 'margin-left: 20px;'
                    }),
            label=""
            )
    stats = forms.HiddenInput()
    streams = forms.HiddenInput()
    streams_laps = forms.HiddenInput()
    map_stream = forms.HiddenInput()

class ManualActivity(forms.Form):
    name = forms.CharField(label="Name",
                           min_length=1,
                           max_length=50,
                           widget=forms.TextInput(attrs={
                                                'class': 'form-control',
                                                })
    )
    date = forms.DateField(label="Date",
                           widget=DatePicker(attrs={
                                         'class': "form-control",
                                         'type': "date"
                                         })
    )
    dist = forms.FloatField(label="Distance",
                              validators=[validate_pos]
                              )
    dist_unit = forms.ChoiceField(
                        widget=forms.Select(attrs={
                                'class': 'form-control',
                                'value': 'miles'
                                }),
                        label='',
                        choices=[
                                ('mi', 'miles'),
                                ('km', 'kilometers'),
                                ('m', 'meters'),
                    ]
            )
    h = forms.IntegerField(widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'type': 'number',
            'placeholder': 'hours'
            }),
                             label='',
                             validators=[validate_pos])
    m = forms.IntegerField(widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'type': 'number',
            'placeholder': 'minutes'
            }),
                             label='',
                             validators=[validate_time, validate_pos])
    s = forms.IntegerField(widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'type': 'number',
            'placeholder': 'seconds'
            }),
                             label='',
                             validators=[validate_time, validate_pos])
    elev = forms.IntegerField(widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'type': 'number',
            }),
                             label='Elevation',
                             validators=[validate_pos],
                             required=False)
    elev_unit = forms.ChoiceField(
                        widget=forms.Select(attrs={
                                'class': 'form-control',
                                'value': 'feet'
                                }),
                        label='',
                        required=False,
                        choices=[
                                ('ft', 'feet'),
                                ('m', 'meters')
                    ]
            )
    avg_hr = forms.IntegerField(widget=forms.NumberInput(attrs={
                                'class': 'form-control',
                                'type': 'number',
                                }),
                             label='Heartrate',
                             required=False,
                             validators=[validate_pos])