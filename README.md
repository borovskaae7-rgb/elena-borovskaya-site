# AI-аудит сообществ ВКонтакте

Next.js-приложение на TypeScript и Tailwind CSS для экспресс-аудита упаковки сообщества ВКонтакте по скриншотам через OpenRouter API.

## Запуск

```bash
npm install
OPENROUTER_API_KEY=your_key npm run dev
```

Приложение использует endpoint `https://openrouter.ai/api/v1/chat/completions` и модель `openai/gpt-4o-mini` через OpenRouter.

Откройте `http://localhost:3000`.
