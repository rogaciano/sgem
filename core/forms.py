from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Field
from .models import Pessoa, Evento, Polo, Atracao, Contrato


class BaseForm(forms.ModelForm):
    """Mixin base para todos os formulários com helper Crispy."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'space-y-4'
        self.helper.label_class = 'block text-sm font-medium text-gray-700'
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full rounded-lg border-gray-300 shadow-sm '
                         'focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm py-2 px-3'
            })


class PessoaForm(BaseForm):
    class Meta:
        model = Pessoa
        fields = '__all__'


class EventoForm(BaseForm):
    class Meta:
        model = Evento
        exclude = ['slug']
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'type': 'date'}),
            'descricao': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['data_inicio'].widget.attrs.update({'type': 'date'})
        self.fields['data_fim'].widget.attrs.update({'type': 'date'})


class PoloForm(BaseForm):
    class Meta:
        model = Polo
        fields = '__all__'
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
        }


class AtracaoForm(BaseForm):
    class Meta:
        model = Atracao
        fields = '__all__'
        widgets = {
            'uf_origem': forms.TextInput(attrs={'maxlength': 2, 'style': 'text-transform:uppercase'}),
        }


class ContratoForm(BaseForm):
    class Meta:
        model = Contrato
        fields = '__all__'
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}),
            'horario_inicio': forms.TimeInput(attrs={'type': 'time'}),
            'horario_fim': forms.TimeInput(attrs={'type': 'time'}),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['data'].widget.attrs.update({'type': 'date'})
        self.fields['horario_inicio'].widget.attrs.update({'type': 'time'})
        self.fields['horario_fim'].widget.attrs.update({'type': 'time'})

        # Filtra apenas eventos ativos no select
        eventos_ativos = Evento.objects.filter(ativo=True)
        self.fields['evento'].queryset = eventos_ativos

        # Pré-seleciona automaticamente se só houver um evento ativo
        if eventos_ativos.count() == 1 and not self.instance.pk:
            self.fields['evento'].initial = eventos_ativos.first()


# ---------------------------------------------------------------------------
# Slots de Programação
# ---------------------------------------------------------------------------

from .models import SlotProgramacao


class SlotEmLoteForm(forms.Form):
    """Gera slots em lote para uma grade de programação."""
    evento = forms.ModelChoiceField(
        queryset=Evento.objects.filter(ativo=True),
        label='Evento',
        widget=forms.Select(),
    )
    polo = forms.ModelChoiceField(
        queryset=Polo.objects.all(),
        label='Polo',
        widget=forms.Select(),
    )
    data_inicio = forms.DateField(
        label='Data Inicial', widget=forms.DateInput(attrs={'type': 'date'})
    )
    data_fim = forms.DateField(
        label='Data Final', widget=forms.DateInput(attrs={'type': 'date'})
    )
    dias_semana = forms.MultipleChoiceField(
        choices=[
            ('0', 'Segunda'), ('1', 'Terça'), ('2', 'Quarta'),
            ('3', 'Quinta'), ('4', 'Sexta'), ('5', 'Sábado'), ('6', 'Domingo'),
        ],
        label='Dias da Semana',
        widget=forms.CheckboxSelectMultiple(),
        initial=['4', '5', '6'],  # Sex, Sáb, Dom
        required=False,
        help_text='Deixe em branco para incluir todos os dias',
    )
    horario_inicio_1 = forms.TimeField(
        label='1º Slot — Início', widget=forms.TimeInput(attrs={'type': 'time'}),
        initial='19:00',
    )
    duracao_minutos = forms.IntegerField(
        label='Duração de cada slot (min)', initial=90, min_value=15, max_value=480,
    )
    num_slots_por_dia = forms.IntegerField(
        label='Qtd. de slots por dia', initial=3, min_value=1, max_value=10,
    )
    observacao = forms.CharField(
        label='Observação (opcional)', required=False, max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'Ex: Slot para atrações principais'}),
    )

    def clean(self):
        cd = super().clean()
        if cd.get('data_inicio') and cd.get('data_fim'):
            if cd['data_fim'] < cd['data_inicio']:
                raise forms.ValidationError('Data Final deve ser posterior à Data Inicial.')
        return cd


class SlotPreencherForm(forms.Form):
    """Associa uma atração (via criação de contrato) a um slot vago."""
    atracao = forms.ModelChoiceField(
        queryset=Atracao.objects.all(),
        label='Atração',
        widget=forms.Select(),
    )
    valor_cache = forms.DecimalField(
        label='Valor do Cachê (R$)', max_digits=12, decimal_places=2,
        initial=0, min_value=0,
    )
    observacoes = forms.CharField(
        label='Observações', required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
    )
