FROM nginx:alpine

# Копируем конфигурацию nginx
COPY deployment/nginx.conf /etc/nginx/nginx.conf

# Открываем порт
EXPOSE 80

# Запускаем nginx
CMD ["nginx", "-g", "daemon off;"] 