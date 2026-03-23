"""
Management command para importar a programação do São João de Caruaru 2026.
Cria: Evento, 3 Polos, todas as Atrações e Contratos com horários escalonados.
"""
import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Evento, Polo, Atracao, Contrato

# ---------------------------------------------------------------------------
# DADOS DA PROGRAMAÇÃO
# Formato: (polo_nome, data_str, [(atracao_nome, cidade, uf, tipo)])
# tipo: banda | cantor | folclorico | orquestra | danca | teatro
# ---------------------------------------------------------------------------

PROGRAMACAO = [

    # ── PÁTIO DE EVENTOS ────────────────────────────────────────────────────
    ('Pátio de Eventos', '2026-05-30', [
        ('Elba Ramalho',    'João Pessoa',  'PB', 'cantor'),
        ('Mari Fernandez',  'Fortaleza',    'CE', 'cantor'),
        ('Solange Almeida', 'Alagoinhas',   'BA', 'cantor'),
    ]),
    ('Pátio de Eventos', '2026-05-31', [
        ('Cavaleiros do Forró', 'Natal',             'RN', 'banda'),
        ('Mastruz com Leite',   'Fortaleza',          'CE', 'banda'),
        ('Limão com Mel',       'Salgueiro',          'PE', 'banda'),
        ('Jonas Esticado',      'Juazeiro do Norte',  'CE', 'cantor'),
    ]),
    ('Pátio de Eventos', '2026-06-04', [
        ('Albanita de Cássia', 'Caruaru',  'PE', 'cantor'),
        ('Willian Sanfona',    'Caruaru',  'PE', 'cantor'),
        ('Colo de Deus',       'Curitiba', 'PR', 'banda'),
    ]),
    ('Pátio de Eventos', '2026-06-05', [
        ('Renan Cruz',    'Caruaru',  'PE', 'cantor'),
        ('Priscila Senna','Recife',   'PE', 'cantor'),
        ('A Vontade',     'Caruaru',  'PE', 'banda'),
        ('Pablo',         'Candeias', 'BA', 'cantor'),
    ]),
    ('Pátio de Eventos', '2026-06-06', [
        ('Nádia Maia',      'Recife',                 'PE', 'cantor'),
        ('Raphaella',       'Caruaru',                'PE', 'cantor'),
        ('Dorgival Dantas', "Olho-d'Água do Borges",  'RN', 'cantor'),
        ('Joelma',          'Almeirim',               'PA', 'cantor'),
    ]),
    ('Pátio de Eventos', '2026-06-07', [
        ('Belo',        'São Paulo', 'SP', 'cantor'),
        ('Nattan',      'Sobral',    'CE', 'cantor'),
        ('Léo Santana', 'Salvador',  'BA', 'cantor'),
        ('Thayse Dias', 'Caruaru',   'PE', 'cantor'),
    ]),
    ('Pátio de Eventos', '2026-06-12', [
        ('Roberto Carlos', 'Cachoeiro de Itapemirim', 'ES', 'cantor'),
        ('Batista Lima',   'Serra Talhada',           'PE', 'cantor'),
    ]),
    ('Pátio de Eventos', '2026-06-13', [
        ('Zé Vaqueiro',      'Ouricuri', 'PE', 'cantor'),
        ('Bell Marques',     'Salvador', 'BA', 'cantor'),
        ('Alok',             'Goiânia',  'GO', 'cantor'),
        ('Guilherme Topado', 'Caruaru',  'PE', 'cantor'),
    ]),
    ('Pátio de Eventos', '2026-06-14', [
        ('Calango Aceso',  'Caruaru',       'PE', 'banda'),
        ('Klever Lemos',   'Caruaru',       'PE', 'cantor'),
        ('Michele Andrade','Barreiros',     'PE', 'cantor'),
        ('Sorriso Maroto', 'Rio de Janeiro','RJ', 'banda'),
    ]),
    ('Pátio de Eventos', '2026-06-19', [
        ('Taty Girl',      'Tauá',           'CE', 'cantor'),
        ('Sâmya Maia',     'Campina Grande', 'PB', 'cantor'),
        ('Wesley Safadão', 'Fortaleza',      'CE', 'cantor'),
        ('Eric Land',      'Fortaleza',      'CE', 'cantor'),
    ]),
    ('Pátio de Eventos', '2026-06-20', [
        ('Mateus Santos',  'Caruaru',  'PE', 'cantor'),
        ('Léo Foguete',    'Caruaru',  'PE', 'cantor'),
        ('Lipe Lucena',    'Recife',   'PE', 'cantor'),
        ('Matheus & Kauan','Goiânia',  'GO', 'banda'),
    ]),
    ('Pátio de Eventos', '2026-06-21', [
        ('Marquinhos Maraial', 'Maraial',       'PE', 'cantor'),
        ('Silvânia & Berg',    'Campina Grande', 'PB', 'banda'),
        ('Luan Santana',       'Campo Grande',   'MS', 'cantor'),
        ('Henry Freitas',      'Recife',         'PE', 'cantor'),
    ]),
    ('Pátio de Eventos', '2026-06-23', [
        ('Nathalia Calazans', 'Caruaru',  'PE', 'cantor'),
        ('Luana Prado',       'Goiânia',  'GO', 'cantor'),
        ('PV Calado',         'Caruaru',  'PE', 'cantor'),
        ('Léo Magalhães',     'Teófilo Otoni', 'MG', 'cantor'),
    ]),
    ('Pátio de Eventos', '2026-06-24', [
        ('Felipe Amorim',     'Fortaleza',  'CE', 'cantor'),
        ('Jorge de Altinho',  'Altinho',    'PE', 'cantor'),
        ('Márcia Fellipe',    'Manaus',     'AM', 'cantor'),
        ('João Gomes',        'Serrita',    'PE', 'cantor'),
    ]),
    ('Pátio de Eventos', '2026-06-26', [
        ('Seu Desejo',           'Caruaru',      'PE', 'banda'),
        ('Natanzinho Lima',      'Caruaru',       'PE', 'cantor'),
        ('João Bosco & Vinícius','Campo Grande',  'MS', 'banda'),
        ('Rey Vaqueiro',         'Fortaleza',     'CE', 'cantor'),
    ]),
    ('Pátio de Eventos', '2026-06-27', [
        ('Forró Gigante',  'Caruaru',            'PE', 'banda'),
        ('Thiaguinho',     'Presidente Prudente','SP', 'cantor'),
        ('Gusttavo Lima',  'Presidente Olegário','MG', 'cantor'),
        ('Xand Avião',     'Natal',              'RN', 'cantor'),
    ]),

    # ── POLO AZULÃO ─────────────────────────────────────────────────────────
    ('Polo Azulão', '2026-05-28', [
        ('Edylla & Levy', 'Caruaru',       'PE', 'banda'),
        ('Eli Soares',    'Belo Horizonte', 'MG', 'cantor'),
        ('Davi Sacer',    'Rio de Janeiro', 'RJ', 'cantor'),
    ]),
    ('Polo Azulão', '2026-06-05', [
        ('Gabriel Sá',         'Caruaru',   'PE', 'cantor'),
        ('Erisson Porto',      'Caruaru',   'PE', 'cantor'),
        ('Big Band A Nordestina','Caruaru',  'PE', 'folclorico'),
        ('Falamansa',          'São Paulo', 'SP', 'banda'),
    ]),
    ('Polo Azulão', '2026-06-06', [
        ('Amanan',      'Caruaru',    'PE', 'cantor'),
        ('Rogéria Dera','Caruaru',    'PE', 'cantor'),
        ('Almério',     'Altinho',    'PE', 'cantor'),
        ('Lucy Alves',  'João Pessoa','PB', 'cantor'),
    ]),
    ('Polo Azulão', '2026-06-12', [
        ('Ícaro Trajano', 'Caruaru', 'PE', 'cantor'),
        ('Alkymenia',     'Recife',  'PE', 'banda'),
        ('Devotos',       'Recife',  'PE', 'banda'),
        ('Nação Zumbi',   'Recife',  'PE', 'banda'),
    ]),
    ('Polo Azulão', '2026-06-13', [
        ('Riáh',                'Caruaru',    'PE', 'cantor'),
        ('Azulão & Convidados', 'Caruaru',    'PE', 'folclorico'),
        ('Mestrinho',           'Itabaiana',  'SE', 'cantor'),
    ]),
    ('Polo Azulão', '2026-06-19', [
        ('Los Cubanos', 'Caruaru', 'PE', 'banda'),
        ('Cascabulho',  'Recife',  'PE', 'banda'),
        ('Elvis Neiff', 'Caruaru', 'PE', 'cantor'),
    ]),
    ('Polo Azulão', '2026-06-20', [
        ('Maestro Spok',  'Recife',          'PE', 'orquestra'),
        ('Maestro Mozart','Caruaru',         'PE', 'orquestra'),
        ('André Rio',     'Recife',          'PE', 'cantor'),
        ('Chico César',   'Catolé do Rocha', 'PB', 'cantor'),
    ]),
    ('Polo Azulão', '2026-06-23', [
        ('Driko',        'Caruaru',  'PE', 'cantor'),
        ('Gerlane Lops', 'Recife',   'PE', 'cantor'),
        ('Colibri Brasil','Caruaru', 'PE', 'folclorico'),
        ('Ilê Aiyê',     'Salvador', 'BA', 'folclorico'),
    ]),

    # ── ALTO DO MOURA ───────────────────────────────────────────────────────
    ('Alto do Moura', '2026-06-06', [
        ('Didi Caruaru',    'Caruaru',   'PE', 'cantor'),
        ('Arreio de Ouro',  'Arcoverde', 'PE', 'banda'),
        ('Targino Gondim',  'Juazeiro',  'BA', 'cantor'),
        ('Walkyria Santos', 'Monteiro',  'PB', 'cantor'),
    ]),
    ('Alto do Moura', '2026-06-07', [
        ('Toca do Vale',     'Fortaleza', 'CE', 'banda'),
        ('Geraldinho Lins',  'Recife',    'PE', 'cantor'),
        ('Eliane',           'Campina Grande', 'PB', 'cantor'),
    ]),
    ('Alto do Moura', '2026-06-13', [
        ('Gatinha Manhosa','Caruaru',   'PE', 'cantor'),
        ('Waldonys',       'Fortaleza', 'CE', 'cantor'),
        ('Edy & Natan',    'Caruaru',   'PE', 'banda'),
    ]),
    ('Alto do Moura', '2026-06-14', [
        ('Satanna, o Cantador','Caruaru','PE', 'cantor'),
        ('Fernandinha',        'Caruaru','PE', 'cantor'),
        ('Juarez',             'Caruaru','PE', 'cantor'),
    ]),
    ('Alto do Moura', '2026-06-20', [
        ('Petrúcio Amorim', 'Caruaru',  'PE', 'cantor'),
        ('Noda de Caju',    'Aracaju',  'SE', 'banda'),
        ('Garota Safada',   'Fortaleza','CE', 'banda'),
    ]),
    ('Alto do Moura', '2026-06-21', [
        ('Matheus Vinni',      'Caruaru',  'PE', 'cantor'),
        ('Forró da Brucelose', 'Caruaru',  'PE', 'banda'),
        ('Novinho da Paraíba', 'Monteiro', 'PB', 'cantor'),
    ]),
    ('Alto do Moura', '2026-06-23', [
        ('Israel Filho',   'Campina Grande','PB', 'cantor'),
        ('Assisão',        'Serra Talhada', 'PE', 'cantor'),
        ('Vilões do Forró','Fortaleza',     'CE', 'banda'),
    ]),
    ('Alto do Moura', '2026-06-24', [
        ('Rennato Pires',     'Caruaru',  'PE', 'cantor'),
        ('Thullio Milionário','Mossoró',  'RN', 'cantor'),
        ('Cavalo de Pau',     'Fortaleza','CE', 'banda'),
    ]),
    ('Alto do Moura', '2026-06-27', [
        ('Douglas Leon', 'Caruaru','PE', 'cantor'),
        ('Baby Som',     'Caruaru','PE', 'banda'),
    ]),
]

# Zonas dos polos
POLO_ZONAS = {
    'Pátio de Eventos': 'urbana',
    'Polo Azulão':      'urbana',
    'Alto do Moura':    'rural',
}

# Capacidades estimadas
POLO_CAPACIDADES = {
    'Pátio de Eventos': 50000,
    'Polo Azulão':      20000,
    'Alto do Moura':    8000,
}


class Command(BaseCommand):
    help = 'Importa a programação do São João de Caruaru 2026'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limpar',
            action='store_true',
            help='Remove contratos existentes do evento antes de importar',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\n🎉 Importando São João de Caruaru 2026...\n'))

        # 1. Evento
        evento, criado = Evento.objects.get_or_create(
            slug='sao-joao-caruaru-2026',
            defaults={
                'nome':        'São João de Caruaru 2026',
                'tipo':        'sao_joao',
                'descricao':   'A maior festa junina do mundo — Caruaru, PE.',
                'data_inicio': datetime.date(2026, 5, 28),
                'data_fim':    datetime.date(2026, 6, 27),
                'ativo':       True,
            }
        )
        self.stdout.write(f'  {"✅ Criado" if criado else "⚠️  Já existe"}: Evento "{evento.nome}"')

        if options['limpar']:
            deleted, _ = Contrato.objects.filter(evento=evento).delete()
            self.stdout.write(f'  🗑️  {deleted} contrato(s) removido(s)')

        # 2. Polos
        polos = {}
        for nome, zona in POLO_ZONAS.items():
            polo, criado = Polo.objects.get_or_create(
                nome=nome,
                defaults={
                    'descricao':  f'Polo do São João de Caruaru — {nome}',
                    'capacidade': POLO_CAPACIDADES[nome],
                    'endereco':   f'{nome}, Caruaru – PE',
                    'zona':       zona,
                }
            )
            polos[nome] = polo
            self.stdout.write(f'  {"✅" if criado else "⚠️ "} Polo: {polo.nome}')

        # 3. Atrações + Contratos
        total_atracoes = 0
        total_contratos = 0
        conflitos = 0

        # Atrações com mesmo nome podem não existir ainda; cria ou busca
        cache_atracoes = {}

        for (polo_nome, data_str, atracao_list) in PROGRAMACAO:
            polo = polos[polo_nome]
            data = datetime.date.fromisoformat(data_str)

            # Horários escalonados partindo das 17:00 em slots de 90 min
            hora_inicio = datetime.time(17, 0)

            for (nome, cidade, uf, tipo) in atracao_list:
                # Cache para não re-criar atrações com mesmo nome
                if nome not in cache_atracoes:
                    atracao, criada = Atracao.objects.get_or_create(
                        nome=nome,
                        defaults={'tipo': tipo, 'cidade_origem': cidade, 'uf_origem': uf},
                    )
                    cache_atracoes[nome] = atracao
                    if criada:
                        total_atracoes += 1
                else:
                    atracao = cache_atracoes[nome]

                # Calcula horário fim (+90 min)
                inicio_dt = datetime.datetime.combine(datetime.date.today(), hora_inicio)
                fim_dt = inicio_dt + datetime.timedelta(minutes=90)
                hora_fim = fim_dt.time()

                # Cria contrato (skip se já existe exatamente)
                if not Contrato.objects.filter(
                    evento=evento, polo=polo, atracao=atracao, data=data
                ).exists():
                    # Tenta criar; se conflitar, adianta 15 min e tenta de novo (até 5x)
                    tentativa_inicio = hora_inicio
                    criado = False
                    for _ in range(5):
                        inicio_dt_t = datetime.datetime.combine(datetime.date.today(), tentativa_inicio)
                        fim_dt_t = inicio_dt_t + datetime.timedelta(minutes=90)
                        if fim_dt_t.day != datetime.date.today().day:
                            break  # ultrapassou meia-noite
                        try:
                            Contrato.objects.create(
                                evento=evento,
                                polo=polo,
                                atracao=atracao,
                                data=data,
                                horario_inicio=tentativa_inicio,
                                horario_fim=fim_dt_t.time(),
                                valor_cache=0,
                            )
                            total_contratos += 1
                            criado = True
                            break
                        except Exception:
                            tentativa_inicio = (inicio_dt_t + datetime.timedelta(minutes=15)).time()

                    if not criado:
                        self.stdout.write(
                            self.style.WARNING(f'  ⚠️  Não foi possível criar: {nome} em {polo_nome} {data_str}')
                        )
                        conflitos += 1

                # Avança 90 minutos para próximo artista
                hora_inicio = fim_dt.time()

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Importação concluída!\n'
            f'   🎤 {total_atracoes} atrações criadas\n'
            f'   📋 {total_contratos} contratos criados\n'
            f'   ⚠️  {conflitos} conflito(s) ignorado(s)\n'
            f'\n   ℹ️  Horários marcados como 19:00–20:30, 20:30–22:00, etc.\n'
            f'      Edite os contratos para ajustar os horários reais.'
        ))
