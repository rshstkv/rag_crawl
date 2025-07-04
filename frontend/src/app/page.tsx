'use client';

import { ChatInterface } from '@/components/chat/chat-interface';
import { CrawlTaskManager } from '@/components/crawl/crawl-task-manager';
import { WebsiteCrawler } from '@/components/crawl/website-crawler';
import { DocumentUpload } from '@/components/documents/document-upload';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useState } from 'react';

export default function HomePage() {
  const [currentNamespace, setCurrentNamespace] = useState('default');

  const handleNamespaceChange = (namespace: string) => {
    setCurrentNamespace(namespace);
  };

  const handleUploadSuccess = () => {
    // Документы автоматически обновятся, но здесь можно добавить дополнительную логику
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Основной контент */}
      <div className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[calc(100vh-140px)]">
          {/* Левая панель - Чат */}
          <div className="lg:col-span-3">
            <ChatInterface
              namespace={currentNamespace}
              onNamespaceChange={handleNamespaceChange}
            />
          </div>

          {/* Правая панель - Загрузка документов и кроулинг */}
          <div className="space-y-6">
            <Tabs defaultValue="upload" className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="upload">Документы</TabsTrigger>
                <TabsTrigger value="crawl">Кроулинг</TabsTrigger>
                <TabsTrigger value="tasks">Задачи</TabsTrigger>
              </TabsList>

              <TabsContent value="upload" className="mt-6">
                <DocumentUpload
                  namespace={currentNamespace}
                  onUploadSuccess={handleUploadSuccess}
                />
              </TabsContent>

              <TabsContent value="crawl" className="mt-6">
                <WebsiteCrawler />
              </TabsContent>

              <TabsContent value="tasks" className="mt-6">
                <CrawlTaskManager />
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
    </div>
  );
}
