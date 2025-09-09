#!/bin/sh

# Aguarda o banco de dados PostgreSQL ficar disponível
echo "Aguardando o banco de dados iniciar..."
until nc -z -v -w30 db 5432; do
  echo "Banco de dados ainda não está disponível, esperando..."
  sleep 1
done

echo "Banco de dados está de pé! Iniciando Django..."
python manage.py migrate
python manage.py runserver 0.0.0.0:8000qq
