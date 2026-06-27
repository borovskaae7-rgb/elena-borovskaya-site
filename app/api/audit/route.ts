import { NextResponse } from 'next/server';

export async function POST() {
  return NextResponse.json(
    {
      error: 'AI-аудит через внешний API отключён. Используйте Python-пайплайн vk_checker для сбора данных и экспорта кандидатов в BotHelp AI.',
    },
    { status: 410 },
  );
}
