import { Button } from "@/components/ui/button";
import { Toaster } from "@/components/ui/sonner";
import { Database, FileText, MessageCircle } from "lucide-react";
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "RAG Crawl - Документооборот с ИИ",
  description: "Система поиска и работы с документами на основе искусственного интеллекта",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <div className="min-h-screen bg-background">
          {/* Навигация */}
          <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="container mx-auto px-4">
              <div className="flex h-16 items-center justify-between">
                <div className="flex items-center space-x-6">
                  <Link href="/" className="flex items-center space-x-2">
                    <Database className="h-6 w-6" />
                    <span className="text-xl font-bold">RAG Crawl</span>
                  </Link>
                  <nav className="flex items-center space-x-4">
                    <Link href="/">
                      <Button variant="ghost" size="sm" className="flex items-center gap-2">
                        <MessageCircle className="h-4 w-4" />
                        Чат
                      </Button>
                    </Link>
                    <Link href="/documents">
                      <Button variant="ghost" size="sm" className="flex items-center gap-2">
                        <FileText className="h-4 w-4" />
                        Документы
                      </Button>
                    </Link>
                  </nav>
                </div>
              </div>
            </div>
          </header>

          {/* Основное содержимое */}
          <main className="flex-1">
            {children}
          </main>
        </div>

        {/* Toaster для уведомлений */}
        <Toaster />
      </body>
    </html>
  );
}
