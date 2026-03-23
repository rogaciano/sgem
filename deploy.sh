#!/bin/bash
# deploy.sh — Atualiza o SGEM na VPS
# Uso: sudo bash deploy.sh

set -e  # Para se qualquer comando falhar

PROJETO="/var/www/caruaru-sgem"
SERVICO="sgem-caruaru"

echo "🔄 Atualizando SGEM..."

cd $PROJETO

# Permissão temporária para git pull
chown -R root:root .
git pull
chown -R www-data:www-data .

# Ativar venv e atualizar dependências (se requirements mudou)
source .venv/bin/activate
pip install -r requirements.txt -q

# Migrations e estáticos
python manage.py migrate --no-input
python manage.py collectstatic --no-input

# Reiniciar Gunicorn
systemctl restart $SERVICO

echo ""
echo "✅ Deploy concluído!"
systemctl status $SERVICO --no-pager -l
