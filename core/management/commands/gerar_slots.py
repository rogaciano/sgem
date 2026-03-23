"""
Gera Slots de Programação a partir dos Contratos já cadastrados.
Cada contrato → 1 slot preenchido (evento, polo, data, horário + vinculação).
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Contrato, SlotProgramacao


class Command(BaseCommand):
    help = 'Cria SlotProgramacao a partir dos contratos existentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limpar',
            action='store_true',
            help='Remove todos os slots existentes antes de recriar',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['limpar']:
            deleted, _ = SlotProgramacao.objects.all().delete()
            self.stdout.write(f'  Removidos {deleted} slot(s) existente(s)')

        criados = ignorados = 0

        for c in Contrato.objects.select_related('evento', 'polo', 'atracao'):
            slot, created = SlotProgramacao.objects.get_or_create(
                evento=c.evento,
                polo=c.polo,
                data=c.data,
                horario_inicio=c.horario_inicio,
                defaults={
                    'horario_fim': c.horario_fim,
                    'contrato': c,
                }
            )
            if created:
                criados += 1
            else:
                # Slot já existia — vincula o contrato se ainda não vinculado
                if not slot.contrato_id:
                    slot.contrato = c
                    slot.horario_fim = c.horario_fim
                    slot.save(update_fields=['contrato', 'horario_fim'])
                    criados += 1
                else:
                    ignorados += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nSlots criados/atualizados: {criados}'
            f'\nJa existiam (ignorados): {ignorados}'
        ))
