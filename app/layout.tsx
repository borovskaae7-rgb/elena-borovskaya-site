import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Аудит сообщества ВКонтакте за 5 минут',
  description: 'Загрузите ссылку и скриншоты сообщества ВКонтакте, чтобы получить маркетинговый аудит с рекомендациями.'
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}
