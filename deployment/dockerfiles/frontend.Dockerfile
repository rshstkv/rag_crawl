FROM node:18-slim AS builder

WORKDIR /app

# Устанавливаем системные зависимости для сборки
RUN apt-get update && apt-get install -y \
    python3 \
    make \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Копируем package.json и package-lock.json
COPY frontend/package*.json ./

# Очищаем кэш и устанавливаем зависимости
RUN npm cache clean --force
RUN npm ci --no-optional

# Копируем исходный код
COPY frontend/ .

# Собираем приложение с правильными настройками
ENV NODE_OPTIONS="--max-old-space-size=4096 --openssl-legacy-provider"
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production
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