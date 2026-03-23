from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify


class Pessoa(models.Model):
    FUNCAO_CHOICES = [
        ('coordenador', 'Coordenador'),
        ('tecnico_som', 'Técnico de Som'),
        ('tecnico_palco', 'Técnico de Palco'),
        ('apoio', 'Apoio'),
        ('seguranca', 'Segurança'),
        ('outro', 'Outro'),
    ]
    nome = models.CharField(max_length=200, verbose_name='Nome')
    funcao = models.CharField(max_length=20, choices=FUNCAO_CHOICES, verbose_name='Função')
    contato = models.CharField(max_length=100, verbose_name='Contato')

    class Meta:
        verbose_name = 'Pessoa'
        verbose_name_plural = 'Pessoas'
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} ({self.get_funcao_display()})'


class Evento(models.Model):
    TIPO_CHOICES = [
        ('sao_joao', 'São João'),
        ('natal', 'Natal'),
        ('carnaval', 'Carnaval'),
        ('inverno', 'Festival de Inverno'),
        ('aniversario', 'Aniversário da Cidade'),
        ('outro', 'Outro'),
    ]
    nome = models.CharField(max_length=200, verbose_name='Nome')
    slug = models.SlugField(unique=True, blank=True, verbose_name='Slug')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name='Tipo')
    descricao = models.TextField(blank=True, verbose_name='Descrição')
    data_inicio = models.DateField(verbose_name='Início')
    data_fim = models.DateField(verbose_name='Término')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta:
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'
        ordering = ['-data_inicio']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.nome)
            slug = base_slug
            n = 1
            while Evento.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{n}'
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.nome} ({self.data_inicio.year})'

    @property
    def duracao_dias(self):
        return (self.data_fim - self.data_inicio).days + 1

    @property
    def total_cache(self):
        return self.contrato_set.aggregate(
            total=models.Sum('valor_cache')
        )['total'] or 0

    @property
    def total_contratos(self):
        return self.contrato_set.count()


class Polo(models.Model):
    ZONA_CHOICES = [
        ('urbana', 'Urbana'),
        ('rural', 'Rural'),
    ]
    nome = models.CharField(max_length=200, verbose_name='Nome')
    descricao = models.TextField(blank=True, verbose_name='Descrição')
    capacidade = models.IntegerField(verbose_name='Capacidade (pessoas)')
    endereco = models.CharField(max_length=300, verbose_name='Endereço')
    zona = models.CharField(max_length=10, choices=ZONA_CHOICES, verbose_name='Zona')
    responsavel = models.ForeignKey(
        Pessoa, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Responsável', related_name='polos'
    )

    class Meta:
        verbose_name = 'Polo'
        verbose_name_plural = 'Polos'
        ordering = ['nome']

    def __str__(self):
        return self.nome

    @property
    def total_contratos(self):
        return self.contrato_set.count()


class Atracao(models.Model):
    TIPO_CHOICES = [
        ('banda', 'Banda'),
        ('cantor', 'Cantor Solo'),
        ('folclorico', 'Grupo Folclórico'),
        ('orquestra', 'Orquestra'),
        ('danca', 'Grupo de Dança'),
        ('teatro', 'Teatro'),
    ]
    nome = models.CharField(max_length=200, verbose_name='Nome')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name='Tipo')
    cidade_origem = models.CharField(max_length=100, verbose_name='Cidade de Origem')
    uf_origem = models.CharField(max_length=2, verbose_name='UF')

    class Meta:
        verbose_name = 'Atração'
        verbose_name_plural = 'Atrações'
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} ({self.get_tipo_display()})'

    @property
    def total_contratos(self):
        return self.contrato_set.count()

    @property
    def total_cache(self):
        return self.contrato_set.aggregate(
            total=models.Sum('valor_cache')
        )['total'] or 0


class Contrato(models.Model):
    evento = models.ForeignKey(
        Evento, on_delete=models.CASCADE, verbose_name='Evento'
    )
    polo = models.ForeignKey(
        Polo, on_delete=models.CASCADE, verbose_name='Polo'
    )
    atracao = models.ForeignKey(
        Atracao, on_delete=models.CASCADE, verbose_name='Atração'
    )
    data = models.DateField(verbose_name='Data')
    horario_inicio = models.TimeField(verbose_name='Horário de Início')
    horario_fim = models.TimeField(verbose_name='Horário de Fim')
    valor_cache = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name='Valor do Cachê (R$)'
    )
    observacoes = models.TextField(blank=True, verbose_name='Observações')

    class Meta:
        verbose_name = 'Contrato'
        verbose_name_plural = 'Contratos'
        ordering = ['data', 'horario_inicio']

    def __str__(self):
        return f'{self.atracao} | {self.polo} | {self.data} {self.horario_inicio:%H:%M}–{self.horario_fim:%H:%M}'

    def clean(self):
        """
        Regras de negócio:
        1. Atração não pode ter contratos com intervalos sobrepostos no mesmo dia.
        2. Polo não pode ter contratos com intervalos sobrepostos no mesmo dia.
        """
        errors = {}

        if not self.horario_inicio or not self.horario_fim:
            return

        if self.horario_fim <= self.horario_inicio:
            errors['horario_fim'] = 'O horário de fim deve ser posterior ao horário de início.'
            raise ValidationError(errors)

        qs = Contrato.objects.filter(data=self.data).exclude(pk=self.pk)

        def sobrepoe(qs_filtrado):
            return qs_filtrado.filter(
                horario_inicio__lt=self.horario_fim,
                horario_fim__gt=self.horario_inicio,
            ).first()

        conflito_atracao = sobrepoe(qs.filter(atracao=self.atracao))
        if conflito_atracao:
            errors['horario_inicio'] = (
                f'Esta atração já tem apresentação das {conflito_atracao.horario_inicio:%H:%M} '
                f'às {conflito_atracao.horario_fim:%H:%M} no polo "{conflito_atracao.polo}" nesta data.'
            )

        conflito_polo = sobrepoe(qs.filter(polo=self.polo))
        if conflito_polo:
            errors['polo'] = (
                f'Este polo já possui "{conflito_polo.atracao}" '
                f'das {conflito_polo.horario_inicio:%H:%M} às {conflito_polo.horario_fim:%H:%M} nesta data.'
            )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# Grade de Planejamento
# ---------------------------------------------------------------------------

class SlotProgramacao(models.Model):
    """
    Encaixe disponível na grade de programação de um evento.
    Pode estar vago (contrato=None) ou preenchido com uma atração.
    """
    evento = models.ForeignKey(
        Evento, on_delete=models.CASCADE, verbose_name='Evento',
        related_name='slots',
    )
    polo = models.ForeignKey(
        Polo, on_delete=models.CASCADE, verbose_name='Polo',
        related_name='slots',
    )
    data = models.DateField(verbose_name='Data')
    horario_inicio = models.TimeField(verbose_name='Horário de Início')
    horario_fim = models.TimeField(verbose_name='Horário de Fim')
    contrato = models.OneToOneField(
        Contrato, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='slot',
        verbose_name='Contrato (Atração)',
    )
    observacao = models.CharField(
        max_length=200, blank=True, verbose_name='Observação',
        help_text='Ex: "Reservado para headliner", "Abertura"',
    )

    class Meta:
        verbose_name = 'Slot de Programação'
        verbose_name_plural = 'Slots de Programação'
        ordering = ['data', 'polo__nome', 'horario_inicio']
        unique_together = [['evento', 'polo', 'data', 'horario_inicio']]

    def __str__(self):
        status = self.contrato.atracao.nome if self.contrato_id else 'Vago'
        return f'{self.data} {self.horario_inicio:%H:%M} | {self.polo} — {status}'

    @property
    def preenchido(self):
        return self.contrato_id is not None

    @property
    def duracao_minutos(self):
        import datetime
        ini = datetime.datetime.combine(self.data, self.horario_inicio)
        fim = datetime.datetime.combine(self.data, self.horario_fim)
        return int((fim - ini).total_seconds() / 60)
