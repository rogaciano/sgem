from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from django.utils import timezone

from .models import Pessoa, Evento, Polo, Atracao, Contrato, SlotProgramacao
from .forms import PessoaForm, EventoForm, PoloForm, AtracaoForm, ContratoForm, SlotEmLoteForm, SlotPreencherForm
from .filters import ContratoFilter, AtracaoFilter, PoloFilter, EventoFilter


# ---------------------------------------------------------------------------
# API: Calendário
# ---------------------------------------------------------------------------

@login_required
def calendario_json(request):
    """Retorna contratos no formato FullCalendar — cores por polo."""
    import json
    # Cores fixas por id de polo (serão geradas dinamicamente)
    CORES_TIPO = {
        'banda':      '#ea580c',
        'cantor':     '#7c3aed',
        'folclorico': '#0891b2',
        'orquestra':  '#059669',
        'danca':      '#db2777',
        'teatro':     '#ca8a04',
    }
    contratos = Contrato.objects.select_related('atracao', 'polo', 'evento').all()
    eventos_cal = []
    for c in contratos:
        inicio = c.horario_inicio.strftime('%H:%M')
        fim    = c.horario_fim.strftime('%H:%M')
        eventos_cal.append({
            'id':    c.pk,
            'title': c.atracao.nome,
            'start': f'{c.data}T{c.horario_inicio}',
            'end':   f'{c.data}T{c.horario_fim}',
            'color': CORES_TIPO.get(c.atracao.tipo, '#6b7280'),
            'extendedProps': {
                'polo_id': c.polo_id,
                'polo':    c.polo.nome,
                'evento':  c.evento.nome,
                'atracao': c.atracao.nome,
                'cache':   float(c.valor_cache),
                'tipo':    c.atracao.get_tipo_display(),
                'inicio':  inicio,
                'fim':     fim,
                'url_detalhe': f'/contratos/{c.pk}/',
            },
        })
    return JsonResponse(eventos_cal, safe=False)


@login_required
def calendario_view(request):
    """Página dedicada do calendário com filtros por polo."""
    import json
    POLO_CORES = ['#ea580c', '#7c3aed', '#0891b2', '#059669', '#db2777', '#ca8a04']
    polos_qs = Polo.objects.all()
    polos = []
    polo_cores_map = {}
    for i, polo in enumerate(polos_qs):
        cor = POLO_CORES[i % len(POLO_CORES)]
        polos.append({'id': polo.pk, 'nome': polo.nome, 'cor': cor})
        polo_cores_map[str(polo.pk)] = cor

    # Data inicial = primeiro contrato futuro ou hoje
    from django.utils import timezone
    primeiro = Contrato.objects.filter(
        data__gte=timezone.localdate()
    ).order_by('data').values_list('data', flat=True).first()
    if not primeiro:
        primeiro = Contrato.objects.order_by('data').values_list('data', flat=True).first()
    initial_date = str(primeiro) if primeiro else str(timezone.localdate())

    return render(request, 'core/calendario.html', {
        'polos': polos,
        'polo_cores_json': json.dumps(polo_cores_map),
        'initial_date': initial_date,
    })


@login_required
def programacao_view(request):
    """Visão de programação agrupada por data — cada data mostra suas atrações com gauge visual."""
    from collections import defaultdict

    # Permite filtrar por evento via ?evento=pk
    evento_id = request.GET.get('evento')
    qs = Contrato.objects.select_related('atracao', 'polo', 'evento').order_by('data', 'polo__nome', 'horario_inicio')
    if evento_id:
        qs = qs.filter(evento_id=evento_id)

    # Agrupa por data → polo → [contratos]
    por_data = defaultdict(lambda: defaultdict(list))
    for c in qs:
        por_data[c.data][c.polo].append(c)

    # Máximo de contratos em um único dia (para escalar o gauge)
    max_dia = max((sum(len(v) for v in polos.values()) for polos in por_data.values()), default=1)

    # Estrutura final ordenada
    dias = []
    for data in sorted(por_data.keys()):
        polos_dia = por_data[data]
        total_dia = sum(len(v) for v in polos_dia.values())
        pct = int(total_dia / max_dia * 100)
        dias.append({
            'data': data,
            'polos': dict(polos_dia),
            'total': total_dia,
            'pct': pct,
            'dia_semana': data.strftime('%A'),
        })

    return render(request, 'core/programacao.html', {
        'dias': dias,
        'max_dia': max_dia,
        'eventos': Evento.objects.all(),
        'evento_selecionado': int(evento_id) if evento_id else None,
    })


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@login_required
def dashboard(request):
    import json
    total_eventos = Evento.objects.count()
    total_polos = Polo.objects.count()
    total_atracoes = Atracao.objects.count()
    total_contratos = Contrato.objects.count()
    total_cache = Contrato.objects.aggregate(t=Sum('valor_cache'))['t'] or 0

    hoje = timezone.localdate()
    eventos_ativos = Evento.objects.filter(data_inicio__lte=hoje, data_fim__gte=hoje)

    # Últimos contratos
    ultimos_contratos = Contrato.objects.select_related(
        'evento', 'polo', 'atracao'
    ).order_by('-data', '-horario_inicio')[:8]

    # Dados por evento para barras de progresso
    eventos_resumo = []
    max_c = 1
    for ev in Evento.objects.all():
        c = ev.contrato_set.count()
        tc = ev.total_cache
        eventos_resumo.append({'evento': ev, 'contratos': c, 'cache': tc})
        if c > max_c:
            max_c = c
    for item in eventos_resumo:
        item['pct'] = int(item['contratos'] / max_c * 100)

    # ── Gauge: Contratos e Cachê por Polo ─────────────────────────────────
    POLO_CORES = ['#ea580c', '#7c3aed', '#0891b2', '#059669', '#db2777', '#ca8a04']
    gauges_polos = []
    for i, polo in enumerate(Polo.objects.annotate(
        n_contratos=Count('contrato'), total=Sum('contrato__valor_cache')
    ).order_by('-n_contratos')):
        gauges_polos.append({
            'nome': polo.nome,
            'contratos': polo.n_contratos,
            'cache': float(polo.total or 0),
            'cor': POLO_CORES[i % len(POLO_CORES)],
        })

    # ── Gauge: Distribuição por Tipo de Atração ────────────────────────────
    TIPO_CORES = {
        'banda':      '#ea580c',
        'cantor':     '#7c3aed',
        'folclorico': '#0891b2',
        'orquestra':  '#059669',
        'danca':      '#db2777',
        'teatro':     '#ca8a04',
    }
    TIPO_LABELS = dict(Atracao.TIPO_CHOICES) if hasattr(Atracao, 'TIPO_CHOICES') else {
        'banda':'Banda','cantor':'Cantor Solo','folclorico':'Folclórico',
        'orquestra':'Orquestra','danca':'Dança','teatro':'Teatro',
    }
    from django.db.models import Count as DCount
    tipo_counts = (
        Contrato.objects.values('atracao__tipo')
        .annotate(total=DCount('id'))
        .order_by('-total')
    )
    chart_labels = [TIPO_LABELS.get(t['atracao__tipo'], t['atracao__tipo']) for t in tipo_counts]
    chart_data   = [t['total'] for t in tipo_counts]
    chart_cores  = [TIPO_CORES.get(t['atracao__tipo'], '#6b7280') for t in tipo_counts]

    context = {
        'total_eventos':   total_eventos,
        'total_polos':     total_polos,
        'total_atracoes':  total_atracoes,
        'total_contratos': total_contratos,
        'total_cache':     total_cache,
        'eventos_ativos':  eventos_ativos,
        'ultimos_contratos': ultimos_contratos,
        'eventos_resumo':  eventos_resumo,
        'gauges_polos':    gauges_polos,
        # JSON para Chart.js
        'chart_tipo_labels': json.dumps(chart_labels),
        'chart_tipo_data':   json.dumps(chart_data),
        'chart_tipo_cores':  json.dumps(chart_cores),
        'chart_polos_labels': json.dumps([g['nome'] for g in gauges_polos]),
        'chart_polos_data':   json.dumps([g['contratos'] for g in gauges_polos]),
        'chart_polos_cores':  json.dumps([g['cor'] for g in gauges_polos]),
    }
    return render(request, 'core/dashboard.html', context)


# ---------------------------------------------------------------------------
# Pessoa
# ---------------------------------------------------------------------------

@login_required
def pessoa_list(request):
    qs = Pessoa.objects.all()
    q = request.GET.get('q', '')
    if q:
        qs = qs.filter(nome__icontains=q)
    return render(request, 'core/pessoa/list.html', {'pessoas': qs, 'q': q})


@login_required
def pessoa_create(request):
    form = PessoaForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Pessoa cadastrada com sucesso!')
        return redirect('pessoa_list')
    return render(request, 'core/pessoa/form.html', {'form': form, 'titulo': 'Nova Pessoa'})


@login_required
def pessoa_detail(request, pk):
    obj = get_object_or_404(Pessoa, pk=pk)
    return render(request, 'core/pessoa/detail.html', {'obj': obj})


@login_required
def pessoa_update(request, pk):
    obj = get_object_or_404(Pessoa, pk=pk)
    form = PessoaForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Pessoa atualizada com sucesso!')
        return redirect('pessoa_list')
    return render(request, 'core/pessoa/form.html', {'form': form, 'titulo': 'Editar Pessoa', 'obj': obj})


@login_required
def pessoa_delete(request, pk):
    obj = get_object_or_404(Pessoa, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Pessoa excluída.')
        return redirect('pessoa_list')
    return redirect('pessoa_list')


# ---------------------------------------------------------------------------
# Evento
# ---------------------------------------------------------------------------

@login_required
def evento_list(request):
    qs = Evento.objects.all()
    filtro = EventoFilter(request.GET, queryset=qs)
    total_cache = Contrato.objects.filter(
        evento__in=filtro.qs
    ).aggregate(t=Sum('valor_cache'))['t'] or 0
    return render(request, 'core/evento/list.html', {
        'filter': filtro,
        'total_cache': total_cache,
    })


@login_required
def evento_create(request):
    form = EventoForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Evento criado com sucesso!')
        return redirect('evento_list')
    return render(request, 'core/evento/form.html', {'form': form, 'titulo': 'Novo Evento'})


@login_required
def evento_detail(request, pk):
    obj = get_object_or_404(Evento, pk=pk)
    contratos = obj.contrato_set.select_related('polo', 'atracao').order_by('data', 'horario_inicio')
    # Agrupar por data para visualização de cronograma
    from itertools import groupby
    from operator import attrgetter
    contratos_por_data = {}
    for c in contratos:
        contratos_por_data.setdefault(c.data, []).append(c)
    return render(request, 'core/evento/detail.html', {
        'obj': obj, 'contratos_por_data': contratos_por_data,
    })


@login_required
def evento_update(request, pk):
    obj = get_object_or_404(Evento, pk=pk)
    form = EventoForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Evento atualizado!')
        return redirect('evento_list')
    return render(request, 'core/evento/form.html', {'form': form, 'titulo': 'Editar Evento', 'obj': obj})


@login_required
def evento_delete(request, pk):
    obj = get_object_or_404(Evento, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Evento excluído.')
        return redirect('evento_list')
    return redirect('evento_list')


# ---------------------------------------------------------------------------
# Polo
# ---------------------------------------------------------------------------

@login_required
def polo_list(request):
    qs = Polo.objects.select_related('responsavel')
    filtro = PoloFilter(request.GET, queryset=qs)
    return render(request, 'core/polo/list.html', {'filter': filtro})


@login_required
def polo_create(request):
    form = PoloForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Polo criado com sucesso!')
        return redirect('polo_list')
    return render(request, 'core/polo/form.html', {'form': form, 'titulo': 'Novo Polo'})


@login_required
def polo_detail(request, pk):
    obj = get_object_or_404(Polo, pk=pk)
    contratos = obj.contrato_set.select_related('evento', 'atracao').order_by('data', 'horario_inicio')
    return render(request, 'core/polo/detail.html', {'obj': obj, 'contratos': contratos})


@login_required
def polo_update(request, pk):
    obj = get_object_or_404(Polo, pk=pk)
    form = PoloForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Polo atualizado!')
        return redirect('polo_list')
    return render(request, 'core/polo/form.html', {'form': form, 'titulo': 'Editar Polo', 'obj': obj})


@login_required
def polo_delete(request, pk):
    obj = get_object_or_404(Polo, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Polo excluído.')
        return redirect('polo_list')
    return redirect('polo_list')


# ---------------------------------------------------------------------------
# Atração
# ---------------------------------------------------------------------------

@login_required
def atracao_list(request):
    qs = Atracao.objects.all()
    filtro = AtracaoFilter(request.GET, queryset=qs)
    total_cache = Contrato.objects.filter(
        atracao__in=filtro.qs
    ).aggregate(t=Sum('valor_cache'))['t'] or 0
    return render(request, 'core/atracao/list.html', {
        'filter': filtro, 'total_cache': total_cache,
    })


@login_required
def atracao_create(request):
    form = AtracaoForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Atração cadastrada com sucesso!')
        return redirect('atracao_list')
    return render(request, 'core/atracao/form.html', {'form': form, 'titulo': 'Nova Atração'})


@login_required
def atracao_detail(request, pk):
    obj = get_object_or_404(Atracao, pk=pk)
    contratos = obj.contrato_set.select_related('evento', 'polo').order_by('data', 'horario_inicio')
    return render(request, 'core/atracao/detail.html', {'obj': obj, 'contratos': contratos})


@login_required
def atracao_update(request, pk):
    obj = get_object_or_404(Atracao, pk=pk)
    form = AtracaoForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Atração atualizada!')
        return redirect('atracao_list')
    return render(request, 'core/atracao/form.html', {'form': form, 'titulo': 'Editar Atração', 'obj': obj})


@login_required
def atracao_delete(request, pk):
    obj = get_object_or_404(Atracao, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Atração excluída.')
        return redirect('atracao_list')
    return redirect('atracao_list')


@login_required
def atracao_create_ajax(request):
    """Endpoint para cadastro rápido de Atração via modal no formulário de Contrato.
    Retorna JSON {id, text} em caso de sucesso, ou {errors} em caso de erro."""
    from django.http import JsonResponse
    from .forms import AtracaoForm

    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    form = AtracaoForm(request.POST)
    if form.is_valid():
        obj = form.save()
        return JsonResponse({'id': obj.pk, 'text': str(obj)})
    else:
        errors = {field: list(errs) for field, errs in form.errors.items()}
        return JsonResponse({'errors': errors}, status=400)


# ---------------------------------------------------------------------------
# Contrato
# ---------------------------------------------------------------------------

@login_required
def contrato_list(request):
    qs = Contrato.objects.select_related('evento', 'polo', 'atracao')
    filtro = ContratoFilter(request.GET, queryset=qs)
    total_cache = filtro.qs.aggregate(t=Sum('valor_cache'))['t'] or 0
    qtd = filtro.qs.count()
    return render(request, 'core/contrato/list.html', {
        'filter': filtro, 'total_cache': total_cache, 'qtd': qtd,
    })


@login_required
def contrato_create(request):
    form = ContratoForm(request.POST or None)
    if form.is_valid():
        try:
            contrato = form.save()
            # Vincula o slot vago correspondente (se existir) ao novo contrato
            slot = SlotProgramacao.objects.filter(
                evento=contrato.evento,
                polo=contrato.polo,
                data=contrato.data,
                horario_inicio=contrato.horario_inicio,
                horario_fim=contrato.horario_fim,
                contrato__isnull=True,
            ).first()
            if slot:
                slot.contrato = contrato
                slot.save(update_fields=['contrato'])
            messages.success(request, 'Contrato criado com sucesso!')
            return redirect('contrato_list')
        except Exception as e:
            messages.error(request, f'Erro ao salvar: {e}')
    return render(request, 'core/contrato/form.html', {'form': form, 'titulo': 'Novo Contrato'})


@login_required
def contrato_detail(request, pk):
    obj = get_object_or_404(Contrato, pk=pk)
    return render(request, 'core/contrato/detail.html', {'obj': obj})


@login_required
def contrato_update(request, pk):
    obj = get_object_or_404(Contrato, pk=pk)
    form = ContratoForm(request.POST or None, instance=obj)
    if form.is_valid():
        try:
            form.save()
            messages.success(request, 'Contrato atualizado!')
            return redirect('contrato_list')
        except Exception as e:
            messages.error(request, f'Erro ao salvar: {e}')
    return render(request, 'core/contrato/form.html', {'form': form, 'titulo': 'Editar Contrato', 'obj': obj})


@login_required
def contrato_delete(request, pk):
    obj = get_object_or_404(Contrato, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Contrato excluído.')
        return redirect('contrato_list')
    return redirect('contrato_list')


# ---------------------------------------------------------------------------
# Exportação PDF
# ---------------------------------------------------------------------------

@login_required
def contrato_pdf(request, evento_pk):
    try:
        from weasyprint import HTML  # lazy import - evita erro de DLL no Windows
    except OSError as e:
        return HttpResponse(
            f'<h2>PDF indisponível</h2><p>WeasyPrint requer GTK no Windows. Erro: {e}</p>'
            '<p>Instale o <a href="https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer">GTK for Windows</a> e reinicie.</p>',
            content_type='text/html', status=503
        )

    evento = get_object_or_404(Evento, pk=evento_pk)
    contratos = evento.contrato_set.select_related('polo', 'atracao').order_by('data', 'polo__nome', 'horario_inicio')

    # Agrupa por data e polo
    cronograma = {}
    for c in contratos:
        cronograma.setdefault(c.data, {}).setdefault(c.polo, []).append(c)

    total_cache = contratos.aggregate(t=Sum('valor_cache'))['t'] or 0

    template = get_template('core/pdf/cronograma.html')
    html_string = template.render({
        'evento': evento,
        'cronograma': cronograma,
        'total_cache': total_cache,
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="cronograma-{evento.slug}.pdf"'
    HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(response)
    return response


# ---------------------------------------------------------------------------
# API: Slots Vagos (para formulário de contrato)
# ---------------------------------------------------------------------------

@login_required
def api_slots_vagos(request):
    """Retorna slots vagos de um evento+polo — usado no form de novo contrato."""
    evento_id = request.GET.get('evento')
    polo_id   = request.GET.get('polo')

    if not evento_id or not polo_id:
        return JsonResponse([], safe=False)

    slots = SlotProgramacao.objects.filter(
        evento_id=evento_id,
        polo_id=polo_id,
        contrato__isnull=True,           # apenas vagos
    ).order_by('data', 'horario_inicio')

    data = [
        {
            'id':             s.pk,
            'data':           str(s.data),                          # YYYY-MM-DD
            'data_display':   s.data.strftime('%d/%m/%Y (%A)'),
            'inicio':         s.horario_inicio.strftime('%H:%M'),
            'fim':            s.horario_fim.strftime('%H:%M'),
            'duracao':        s.duracao_minutos,
            'label':          f"{s.data.strftime('%d/%m/%Y')} — {s.horario_inicio.strftime('%H:%M')} às {s.horario_fim.strftime('%H:%M')} ({s.duracao_minutos} min)",
        }
        for s in slots
    ]
    return JsonResponse(data, safe=False)


# ---------------------------------------------------------------------------
# Grade de Planejamento (Slots)
# ---------------------------------------------------------------------------

@login_required
def grade_view(request):
    """Grade de planejamento: exibe slots agrupados por data e polo."""
    from collections import defaultdict

    evento_id = request.GET.get('evento')
    polo_id   = request.GET.get('polo')

    qs = SlotProgramacao.objects.select_related(
        'polo', 'evento', 'contrato__atracao'
    ).order_by('data', 'polo__nome', 'horario_inicio')

    if evento_id:
        qs = qs.filter(evento_id=evento_id)
    if polo_id:
        qs = qs.filter(polo_id=polo_id)

    # Agrupa: data → polo → [slots]
    por_data = defaultdict(lambda: defaultdict(list))
    for slot in qs:
        por_data[slot.data][slot.polo].append(slot)

    # Estatísticas globais
    total = qs.count()
    preenchidos = qs.filter(contrato__isnull=False).count()
    vagos = total - preenchidos

    dias = []
    for data in sorted(por_data.keys()):
        polos_dia = por_data[data]
        total_dia = sum(len(v) for v in polos_dia.values())
        preench_dia = sum(1 for slots in polos_dia.values() for s in slots if s.preenchido)
        dias.append({
            'data': data,
            'polos': dict(polos_dia),
            'total': total_dia,
            'preenchidos': preench_dia,
            'vagos': total_dia - preench_dia,
        })

    return render(request, 'core/grade.html', {
        'dias': dias,
        'eventos': Evento.objects.all(),
        'polos': Polo.objects.all(),
        'evento_selecionado': int(evento_id) if evento_id else None,
        'polo_selecionado': int(polo_id) if polo_id else None,
        'total': total,
        'preenchidos': preenchidos,
        'vagos': vagos,
        'pct': int(preenchidos / total * 100) if total else 0,
    })


@login_required
def slot_lote_view(request):
    """Cria múltiplos slots em lote para uma data/polo/horário."""
    import datetime

    if request.method == 'POST':
        form = SlotEmLoteForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            evento  = cd['evento']
            polo    = cd['polo']
            duracao = cd['duracao_minutos']
            n_slots = cd['num_slots_por_dia']
            dias_semana = [int(d) for d in cd.get('dias_semana', [])]
            obs = cd.get('observacao', '')

            # Itera nos dias do período
            criados = 0
            ignorados = 0
            data_atual = cd['data_inicio']
            while data_atual <= cd['data_fim']:
                # Filtra por dia da semana se informado
                if not dias_semana or data_atual.weekday() in dias_semana:
                    hora = cd['horario_inicio_1']
                    for _ in range(n_slots):
                        ini_dt = datetime.datetime.combine(data_atual, hora)
                        fim_dt = ini_dt + datetime.timedelta(minutes=duracao)
                        if fim_dt.day != data_atual.day:
                            break  # passa meia-noite
                        _, created = SlotProgramacao.objects.get_or_create(
                            evento=evento,
                            polo=polo,
                            data=data_atual,
                            horario_inicio=hora,
                            defaults={
                                'horario_fim': fim_dt.time(),
                                'observacao': obs,
                            }
                        )
                        if created:
                            criados += 1
                        else:
                            ignorados += 1
                        hora = fim_dt.time()

                data_atual += datetime.timedelta(days=1)
            msg = f'{criados} slot(s) criado(s)'
            if ignorados:
                msg += f', {ignorados} já existia(m)'
            messages.success(request, msg)
            return redirect(f'{request.path_info[:-len("novo/")]}?evento={evento.pk}')
    else:
        form = SlotEmLoteForm()

    return render(request, 'core/slot_lote.html', {'form': form})


@login_required
def slot_preencher_view(request, pk):
    """Preenche um slot vago com uma atração, criando o contrato."""
    slot = get_object_or_404(SlotProgramacao, pk=pk, contrato__isnull=True)

    if request.method == 'POST':
        form = SlotPreencherForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            atracao = cd['atracao']

            # Verifica conflitos antes de criar
            conflito_polo = Contrato.objects.filter(
                polo=slot.polo, data=slot.data,
                horario_inicio__lt=slot.horario_fim,
                horario_fim__gt=slot.horario_inicio,
            ).first()
            conflito_atracao = Contrato.objects.filter(
                atracao=atracao, data=slot.data,
                horario_inicio__lt=slot.horario_fim,
                horario_fim__gt=slot.horario_inicio,
            ).first()

            erros = []
            if conflito_polo:
                erros.append(
                    f'O polo "{slot.polo}" já tem "{conflito_polo.atracao}" das '
                    f'{conflito_polo.horario_inicio:%H:%M} às {conflito_polo.horario_fim:%H:%M} nesta data.'
                )
            if conflito_atracao:
                erros.append(
                    f'"{atracao}" já tem apresentação das '
                    f'{conflito_atracao.horario_inicio:%H:%M} às {conflito_atracao.horario_fim:%H:%M} neste dia.'
                )
            if erros:
                for e in erros:
                    messages.error(request, e)
                return render(request, 'core/slot_preencher.html', {'slot': slot, 'form': form})

            try:
                contrato = Contrato(
                    evento=slot.evento, polo=slot.polo, atracao=atracao,
                    data=slot.data, horario_inicio=slot.horario_inicio,
                    horario_fim=slot.horario_fim, valor_cache=cd['valor_cache'],
                    observacoes=cd.get('observacoes', ''),
                )
                contrato.save()
                slot.contrato = contrato
                slot.save(update_fields=['contrato'])
                messages.success(request, f'✅ {atracao} adicionado(a) ao slot!')
            except Exception as e:
                messages.error(request, f'Erro inesperado: {e}')
            return redirect('grade')
    else:
        form = SlotPreencherForm()

    return render(request, 'core/slot_preencher.html', {'slot': slot, 'form': form})


@login_required
def slot_excluir_view(request, pk):
    """Remove um slot da grade (POST). Se tiver contrato, só exclui o slot (não o contrato)."""
    slot = get_object_or_404(SlotProgramacao, pk=pk)
    if request.method == 'POST':
        # Desvincula o contrato do slot antes de excluir (preserva o contrato)
        if slot.contrato_id:
            slot.contrato = None
            slot.save(update_fields=['contrato'])
        slot.delete()
        messages.success(request, 'Slot removido da grade.')
    return redirect('grade')


@login_required
def slot_desvincular_view(request, pk):
    """Remove a atração do slot e exclui o contrato associado. O slot fica vago."""
    slot = get_object_or_404(SlotProgramacao, pk=pk)
    if request.method == 'POST' and slot.contrato_id:
        contrato = slot.contrato
        nome = contrato.atracao.nome
        slot.contrato = None
        slot.save(update_fields=['contrato'])
        contrato.delete()
        messages.success(request, f'Atração "{nome}" e contrato removidos. Slot vago.')
    return redirect('grade')


# ---------------------------------------------------------------------------
# Gestão de Usuários (apenas superusuários)
# ---------------------------------------------------------------------------

from django.contrib.auth.models import User
from .forms_usuarios import UsuarioCreateForm, UsuarioEditForm, UsuarioSenhaForm


def _superuser_required(view_func):
    """Decorator: exige login + superuser."""
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.shortcuts import redirect as _redirect
            return _redirect(f'/login/?next={request.path}')
        if not request.user.is_superuser:
            messages.error(request, 'Acesso restrito a superusuários.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@_superuser_required
def usuario_list(request):
    usuarios = User.objects.all().order_by('username')
    return render(request, 'core/usuarios/list.html', {'usuarios': usuarios})


@_superuser_required
def usuario_create(request):
    form = UsuarioCreateForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Usuário criado com sucesso!')
        return redirect('usuario_list')
    return render(request, 'core/usuarios/form.html', {'form': form, 'titulo': 'Novo Usuário'})


@_superuser_required
def usuario_edit(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    form = UsuarioEditForm(request.POST or None, instance=usuario)
    if form.is_valid():
        form.save()
        messages.success(request, f'Usuário "{usuario.username}" atualizado!')
        return redirect('usuario_list')
    return render(request, 'core/usuarios/form.html', {
        'form': form, 'titulo': f'Editar: {usuario.username}', 'usuario': usuario,
    })


@_superuser_required
def usuario_senha(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    form = UsuarioSenhaForm(user=usuario, data=request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, f'Senha de "{usuario.username}" alterada!')
        return redirect('usuario_list')
    return render(request, 'core/usuarios/senha.html', {'form': form, 'usuario': usuario})


@_superuser_required
def usuario_delete(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        if usuario == request.user:
            messages.error(request, 'Você não pode excluir sua própria conta.')
        else:
            nome = usuario.username
            usuario.delete()
            messages.success(request, f'Usuário "{nome}" excluído.')
    return redirect('usuario_list')

