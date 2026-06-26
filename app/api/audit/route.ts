import OpenAI from 'openai';
import { NextResponse } from 'next/server';

export const runtime = 'nodejs';

const prompt = `Ты опытный маркетолог по продвижению бизнеса ВКонтакте.

Проанализируй сообщество по следующим критериям:

- первое впечатление;
- читаемость обложки;
- качество аватара;
- наличие и качество оффера;
- наличие призыва к действию;
- наличие социального доказательства;
- качество контента;
- оформление постов;
- наличие лид-магнита;
- готовность сообщества к рекламе.

Для каждого пункта:

1. Поставь оценку от 1 до 10.
2. Опиши проблему.
3. Дай конкретную рекомендацию.

В конце сформируй:

- 5 главных ошибок;
- 5 быстрых улучшений;
- общий вывод;
- вероятность успешного запуска рекламы.

Верни только JSON по схеме: {"criteria":[{"criterion":"","score":1,"problem":"","recommendation":""}],"topMistakes":[""],"quickWins":[""],"conclusion":"","adsLaunchProbability":""}.`;

async function fileToDataUrl(file: File) {
  const buffer = Buffer.from(await file.arrayBuffer());
  return `data:${file.type};base64,${buffer.toString('base64')}`;
}

export async function POST(request: Request) {
  if (!process.env.OPENAI_API_KEY) {
    return NextResponse.json(
      {
        code: 'OPENAI_API_KEY_MISSING',
        error: 'Сервис аудита сейчас не может связаться с OpenAI, потому что на сервере не настроен API Key.',
        adminInstruction: 'Добавьте переменную окружения OPENAI_API_KEY в настройках хостинга или в .env.local, затем перезапустите приложение.'
      },
      { status: 503 }
    );
  }

  const formData = await request.formData();
  const vkUrl = String(formData.get('vkUrl') ?? '').trim();
  const name = String(formData.get('name') ?? '').trim();
  const telegram = String(formData.get('telegram') ?? '').trim();
  const images = formData.getAll('images').filter((item): item is File => item instanceof File);

  if (!vkUrl || !name || !telegram || images.length === 0) {
    return NextResponse.json({ error: 'Заполните ссылку, имя, Telegram и загрузите изображения.' }, { status: 400 });
  }

  const safeImages = images.filter((file) => ['image/png', 'image/jpeg'].includes(file.type)).slice(0, 10);
  if (safeImages.length !== images.length || safeImages.length > 10) {
    return NextResponse.json({ error: 'Можно загрузить до 10 изображений в формате PNG или JPG.' }, { status: 400 });
  }

  const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
  const imageParts = await Promise.all(safeImages.map(async (file) => ({ type: 'input_image' as const, image_url: await fileToDataUrl(file) })));

  const response = await client.responses.create({
    model: process.env.OPENAI_AUDIT_MODEL ?? 'gpt-4.1-mini',
    input: [{
      role: 'user',
      content: [
        { type: 'input_text', text: `${prompt}\n\nСсылка на сообщество: ${vkUrl}\nИмя клиента: ${name}\nTelegram: ${telegram}` },
        ...imageParts
      ]
    }],
    text: { format: { type: 'json_object' } }
  });

  const raw = response.output_text;
  try {
    return NextResponse.json({ audit: JSON.parse(raw) });
  } catch {
    return NextResponse.json({ error: 'OpenAI вернул ответ в неожиданном формате.', raw }, { status: 502 });
  }
}
