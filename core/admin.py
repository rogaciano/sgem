from django.contrib import admin
from django.utils.html import format_html
from .models import Pessoa, Evento, Polo, Atracao, Contrato


@admin.register(Pessoa)
class PessoaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'funcao', 'contato']
    search_fields = ['nome', 'contato']
    list_filter = ['funcao']


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo', 'data_inicio', 'data_fim', 'ativo', 'duracao_dias', 'total_contratos']
    list_filter = ['tipo', 'ativo']
    search_fields = ['nome']
    prepopulated_fields = {'slug': ('nome',)}
    readonly_fields = ['total_cache', 'total_contratos']
    list_editable = ['ativo']

    def duracao_dias(self, obj):
        return f'{obj.duracao_dias} dias'
    duracao_dias.short_description = 'Duração'

    def total_contratos(self, obj):
        return obj.total_contratos
    total_contratos.short_description = 'Contratos'


@admin.register(Polo)
class PoloAdmin(admin.ModelAdmin):
    list_display = ['nome', 'zona', 'capacidade', 'responsavel', 'endereco']
    list_filter = ['zona']
    search_fields = ['nome', 'endereco']
    autocomplete_fields = ['responsavel']


@admin.register(Atracao)
class AtracaoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo', 'cidade_origem', 'uf_origem', 'total_contratos']
    list_filter = ['tipo', 'uf_origem']
    search_fields = ['nome', 'cidade_origem']

    def total_contratos(self, obj):
        return obj.total_contratos
    total_contratos.short_description = 'Contratos'


class ContratoInline(admin.TabularInline):
    model = Contrato
    extra = 0
    fields = ['evento', 'polo', 'atracao', 'data', 'horario_inicio', 'horario_fim', 'valor_cache']


@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = ['atracao', 'polo', 'evento', 'data', 'horario_inicio', 'horario_fim', 'valor_cache_fmt']
    list_filter = ['evento', 'polo', 'data']
    search_fields = ['atracao__nome', 'polo__nome', 'evento__nome']
    autocomplete_fields = ['evento', 'polo', 'atracao']
    date_hierarchy = 'data'

    def valor_cache_fmt(self, obj):
        return format_html('R$ {:,.2f}', obj.valor_cache)
    valor_cache_fmt.short_description = 'Cachê'
    valor_cache_fmt.admin_order_field = 'valor_cache'
