import django_filters
from .models import Contrato, Atracao, Polo, Evento


class ContratoFilter(django_filters.FilterSet):
    data = django_filters.DateFilter(label='Data')
    data__gte = django_filters.DateFilter(field_name='data', lookup_expr='gte', label='A partir de')
    data__lte = django_filters.DateFilter(field_name='data', lookup_expr='lte', label='Até')

    class Meta:
        model = Contrato
        fields = ['evento', 'polo', 'atracao', 'data']


class AtracaoFilter(django_filters.FilterSet):
    nome = django_filters.CharFilter(lookup_expr='icontains', label='Nome')

    class Meta:
        model = Atracao
        fields = ['tipo', 'uf_origem', 'nome']


class PoloFilter(django_filters.FilterSet):
    nome = django_filters.CharFilter(lookup_expr='icontains', label='Nome')

    class Meta:
        model = Polo
        fields = ['zona', 'nome']


class EventoFilter(django_filters.FilterSet):
    nome = django_filters.CharFilter(lookup_expr='icontains', label='Nome')

    class Meta:
        model = Evento
        fields = ['tipo', 'nome']
