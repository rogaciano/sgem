from django.urls import path
from . import views

urlpatterns = [
    # Dashboard e Calendário
    path('', views.dashboard, name='dashboard'),
    path('calendario/', views.calendario_view, name='calendario'),
    path('programacao/', views.programacao_view, name='programacao'),
    path('api/calendario/', views.calendario_json, name='calendario_json'),
    path('api/slots-vagos/', views.api_slots_vagos, name='api_slots_vagos'),

    # Pessoas
    path('pessoas/', views.pessoa_list, name='pessoa_list'),
    path('pessoas/novo/', views.pessoa_create, name='pessoa_create'),
    path('pessoas/<int:pk>/', views.pessoa_detail, name='pessoa_detail'),
    path('pessoas/<int:pk>/editar/', views.pessoa_update, name='pessoa_update'),
    path('pessoas/<int:pk>/excluir/', views.pessoa_delete, name='pessoa_delete'),

    # Eventos
    path('eventos/', views.evento_list, name='evento_list'),
    path('eventos/novo/', views.evento_create, name='evento_create'),
    path('eventos/<int:pk>/', views.evento_detail, name='evento_detail'),
    path('eventos/<int:pk>/editar/', views.evento_update, name='evento_update'),
    path('eventos/<int:pk>/excluir/', views.evento_delete, name='evento_delete'),
    path('eventos/<int:evento_pk>/pdf/', views.contrato_pdf, name='evento_pdf'),

    # Polos
    path('polos/', views.polo_list, name='polo_list'),
    path('polos/novo/', views.polo_create, name='polo_create'),
    path('polos/<int:pk>/', views.polo_detail, name='polo_detail'),
    path('polos/<int:pk>/editar/', views.polo_update, name='polo_update'),
    path('polos/<int:pk>/excluir/', views.polo_delete, name='polo_delete'),

    # Atrações
    path('atracoes/', views.atracao_list, name='atracao_list'),
    path('atracoes/novo/', views.atracao_create, name='atracao_create'),
    path('atracoes/novo/ajax/', views.atracao_create_ajax, name='atracao_create_ajax'),
    path('atracoes/<int:pk>/', views.atracao_detail, name='atracao_detail'),
    path('atracoes/<int:pk>/editar/', views.atracao_update, name='atracao_update'),
    path('atracoes/<int:pk>/excluir/', views.atracao_delete, name='atracao_delete'),

    # Contratos
    path('contratos/', views.contrato_list, name='contrato_list'),
    path('contratos/novo/', views.contrato_create, name='contrato_create'),
    path('contratos/<int:pk>/', views.contrato_detail, name='contrato_detail'),
    path('contratos/<int:pk>/editar/', views.contrato_update, name='contrato_update'),
    path('contratos/<int:pk>/excluir/', views.contrato_delete, name='contrato_delete'),

    # Grade de Planejamento (Slots)
    path('grade/', views.grade_view, name='grade'),
    path('grade/novo/', views.slot_lote_view, name='slot_lote'),
    path('grade/<int:pk>/preencher/', views.slot_preencher_view, name='slot_preencher'),
    path('grade/<int:pk>/excluir/', views.slot_excluir_view, name='slot_excluir'),
    path('grade/<int:pk>/desvincular/', views.slot_desvincular_view, name='slot_desvincular'),

    # Gestão de Usuários (apenas superusuários)
    path('usuarios/', views.usuario_list, name='usuario_list'),
    path('usuarios/novo/', views.usuario_create, name='usuario_create'),
    path('usuarios/<int:pk>/editar/', views.usuario_edit, name='usuario_edit'),
    path('usuarios/<int:pk>/senha/', views.usuario_senha, name='usuario_senha'),
    path('usuarios/<int:pk>/excluir/', views.usuario_delete, name='usuario_delete'),
]
