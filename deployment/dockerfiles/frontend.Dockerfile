FROM node:18-slim AS builder

WORKDIR /app

# Копируем package.json и package-lock.json
COPY frontend/package*.json ./

# Устанавливаем зависимости
RUN npm ci

# Копируем исходный код
COPY frontend/ .

# Собираем приложение
RUN npm run build

# Этап выполнения
FROM node:18-slim AS runner

WORKDIR /app

# Создаем пользователя для безопасности  
RUN groupadd --system --gid 1001 nodejs
RUN useradd --system --uid 1001 --gid nodejs nextjs

# Копируем необходимые файлы из builder
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Переключаемся на пользователя nextjs
USER nextjs

# Открываем порт
EXPOSE 3000

# Запускаем приложение
CMD ["node", "server.js"] 