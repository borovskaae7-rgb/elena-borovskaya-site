'use client';

import { ChangeEvent, FormEvent, useMemo, useState } from 'react';

type AuditItem = { criterion: string; score: number; problem: string; recommendation: string };
type AuditResult = {
  criteria: AuditItem[];
  topMistakes: string[];
  quickWins: string[];
  conclusion: string;
  adsLaunchProbability: string;
};

type AppError = {
  title: string;
  message: string;
  instruction?: string;
  variant: 'warning' | 'error';
};

const criteria = [
  'первое впечатление', 'читаемость обложки', 'качество аватара', 'наличие и качество оффера',
  'наличие призыва к действию', 'наличие социального доказательства', 'качество контента',
  'оформление постов', 'наличие лид-магнита', 'готовность сообщества к рекламе'
];

export default function Home() {
  const [vkUrl, setVkUrl] = useState('');
  const [name, setName] = useState('');
  const [telegram, setTelegram] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [result, setResult] = useState<AuditResult | null>(null);
  const [error, setError] = useState<AppError | null>(null);
  const [loading, setLoading] = useState(false);

  const previews = useMemo(() => files.map((file) => ({ name: file.name, size: Math.round(file.size / 1024) })), [files]);

  const onFiles = (event: ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(event.target.files ?? []);
    const images = selected.filter((file) => ['image/png', 'image/jpeg'].includes(file.type)).slice(0, 10);
    setFiles(images);
    if (selected.length > images.length) {
      setError({
        title: 'Проверьте файлы',
        message: 'Можно загрузить до 10 файлов только в формате PNG или JPG.',
        variant: 'error'
      });
    } else {
      setError(null);
    }
  };

  const submitAudit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setResult(null);
    if (!files.length) {
      setError({
        title: 'Добавьте скриншоты',
        message: 'Загрузите хотя бы один скриншот сообщества, чтобы GPT смог оценить оформление и контент.',
        variant: 'error'
      });
      return;
    }
    setLoading(true);
    const formData = new FormData();
    formData.append('vkUrl', vkUrl);
    formData.append('name', name);
    formData.append('telegram', telegram);
    files.forEach((file) => formData.append('images', file));

    try {
      const response = await fetch('/api/audit', { method: 'POST', body: formData });
      const data = await response.json();
      if (!response.ok) {
        if (data.code === 'OPENAI_API_KEY_MISSING') {
          setError({
            title: 'Аудит временно недоступен',
            message: data.error ?? 'На сервере не настроен OpenAI API Key.',
            instruction: data.adminInstruction ?? 'Администратору нужно добавить переменную окружения OPENAI_API_KEY и перезапустить приложение.',
            variant: 'warning'
          });
          return;
        }

        throw new Error(data.error ?? 'Не удалось провести аудит.');
      }
      setResult(data.audit);
    } catch (err) {
      setError({
        title: 'Не удалось провести аудит',
        message: err instanceof Error ? err.message : 'Попробуйте ещё раз или напишите администратору.',
        variant: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen overflow-hidden bg-[radial-gradient(circle_at_top_left,#ffffff_0,#f7f4ee_42%,#efe7dc_100%)]">
      <section className="mx-auto grid w-full max-w-7xl gap-10 px-5 py-8 md:grid-cols-[1fr_0.9fr] md:px-8 lg:py-14">
        <div className="flex flex-col justify-center">
          <div className="mb-8 inline-flex w-fit rounded-full border border-sage/20 bg-white/70 px-4 py-2 text-sm font-semibold text-sage shadow-sm">
            AI-аудит упаковки · VK · рекомендации для рекламы
          </div>
          <h1 className="max-w-4xl text-4xl font-black leading-tight tracking-[-0.05em] text-ink sm:text-6xl lg:text-7xl">
            Получите аудит вашего сообщества ВКонтакте за 5 минут
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-ink/70">
            Загрузите ссылку и до 10 скриншотов сообщества. GPT проанализирует оформление, оффер, контент и готовность к запуску рекламы, а затем соберёт понятный план улучшений.
          </p>
          <div className="mt-8 grid gap-3 sm:grid-cols-3">
            {['10 критериев оценки', 'Карточки с проблемами', 'Быстрые улучшения'].map((item) => (
              <div key={item} className="rounded-3xl border border-white/70 bg-white/55 p-4 text-sm font-bold text-ink shadow-sm backdrop-blur">{item}</div>
            ))}
          </div>
        </div>

        <form onSubmit={submitAudit} className="rounded-[2rem] border border-white/70 bg-white/80 p-5 shadow-soft backdrop-blur md:p-7">
          <h2 className="text-2xl font-black tracking-tight">Данные для аудита</h2>
          <div className="mt-6 space-y-4">
            <label className="block text-sm font-bold">Ссылка на сообщество ВК
              <input required type="url" value={vkUrl} onChange={(e) => setVkUrl(e.target.value)} placeholder="https://vk.com/club..." className="mt-2 w-full rounded-2xl border border-ink/10 bg-cream px-4 py-3 outline-none ring-clay/30 focus:ring-4" />
            </label>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block text-sm font-bold">Имя
                <input required value={name} onChange={(e) => setName(e.target.value)} className="mt-2 w-full rounded-2xl border border-ink/10 bg-cream px-4 py-3 outline-none ring-clay/30 focus:ring-4" />
              </label>
              <label className="block text-sm font-bold">Telegram
                <input required value={telegram} onChange={(e) => setTelegram(e.target.value)} placeholder="@username" className="mt-2 w-full rounded-2xl border border-ink/10 bg-cream px-4 py-3 outline-none ring-clay/30 focus:ring-4" />
              </label>
            </div>
            <label className="block rounded-3xl border-2 border-dashed border-sage/30 bg-sage/5 p-5 text-center text-sm font-bold text-sage">
              Загрузить до 10 изображений PNG/JPG
              <input type="file" accept="image/png,image/jpeg" multiple onChange={onFiles} className="sr-only" />
            </label>
            {!!previews.length && <div className="grid gap-2 text-xs text-ink/65">{previews.map((file) => <span key={file.name} className="rounded-xl bg-cream px-3 py-2">{file.name} · {file.size} КБ</span>)}</div>}
            {error && <ErrorNotice error={error} />}
            <button disabled={loading} className="w-full rounded-full bg-ink px-6 py-4 text-sm font-black uppercase tracking-wider text-white transition hover:bg-sage disabled:cursor-wait disabled:opacity-60">
              {loading ? 'Анализируем...' : 'Получить аудит'}
            </button>
          </div>
        </form>
      </section>

      <section className="mx-auto max-w-7xl px-5 pb-16 md:px-8">
        {result ? <AuditCards audit={result} /> : <CriteriaPreview />}
      </section>
    </main>
  );
}


function ErrorNotice({ error }: { error: AppError }) {
  const isWarning = error.variant === 'warning';

  return (
    <div className={`rounded-3xl border p-4 text-left shadow-sm ${isWarning ? 'border-amber-200 bg-amber-50 text-amber-950' : 'border-red-100 bg-red-50 text-red-950'}`} role="alert">
      <div className="flex gap-3">
        <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-lg ${isWarning ? 'bg-amber-200/70' : 'bg-red-100'}`}>
          {isWarning ? '⚙️' : '!' }
        </span>
        <div>
          <p className="font-black">{error.title}</p>
          <p className="mt-1 text-sm leading-6 opacity-80">{error.message}</p>
          {error.instruction && (
            <div className="mt-3 rounded-2xl bg-white/70 p-3 text-sm leading-6">
              <span className="font-black">Инструкция для администратора: </span>
              {error.instruction}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function CriteriaPreview() {
  return <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">{criteria.map((item) => <div key={item} className="rounded-3xl border border-ink/10 bg-white/55 p-5 text-sm font-bold capitalize text-ink/75">{item}</div>)}</div>;
}

function AuditCards({ audit }: { audit: AuditResult }) {
  return (
    <div id="audit" className="space-y-8">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {audit.criteria.map((item) => (
          <article key={item.criterion} className="rounded-[1.7rem] border border-white/80 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between gap-4"><h3 className="text-lg font-black capitalize">{item.criterion}</h3><span className="rounded-full bg-clay/10 px-3 py-1 font-black text-clay">{item.score}/10</span></div>
            <p className="mt-4 text-sm font-bold text-ink/70">Проблема</p><p className="mt-1 text-sm leading-6 text-ink/70">{item.problem}</p>
            <p className="mt-4 text-sm font-bold text-ink/70">Рекомендация</p><p className="mt-1 text-sm leading-6 text-ink/70">{item.recommendation}</p>
          </article>
        ))}
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <ListCard title="5 главных ошибок" items={audit.topMistakes} />
        <ListCard title="5 быстрых улучшений" items={audit.quickWins} />
      </div>
      <div className="rounded-[2rem] bg-ink p-6 text-white md:p-8"><h3 className="text-2xl font-black">Общий вывод</h3><p className="mt-3 text-white/75">{audit.conclusion}</p><p className="mt-5 font-black text-clay">Вероятность успешного запуска рекламы: {audit.adsLaunchProbability}</p></div>
      <div className="rounded-[2rem] border border-sage/15 bg-white p-6 md:p-8"><h3 className="text-2xl font-black">Хочу внедрить рекомендации</h3><form className="mt-5 grid gap-3 md:grid-cols-[1fr_1fr_auto]"><input placeholder="Имя" className="rounded-2xl bg-cream px-4 py-3" /><input placeholder="Telegram" className="rounded-2xl bg-cream px-4 py-3" /><button className="rounded-full bg-clay px-6 py-3 font-black text-white">Отправить заявку</button></form></div>
    </div>
  );
}

function ListCard({ title, items }: { title: string; items: string[] }) {
  return <article className="rounded-[2rem] bg-white p-6 shadow-sm"><h3 className="text-2xl font-black">{title}</h3><ol className="mt-4 space-y-3">{items.map((item) => <li key={item} className="flex gap-3 text-sm leading-6 text-ink/70"><span className="font-black text-clay">•</span>{item}</li>)}</ol></article>;
}
