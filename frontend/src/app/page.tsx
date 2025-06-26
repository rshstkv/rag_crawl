'use client';

import { ChatInterface } from '@/components/chat/chat-interface';
import { DocumentList } from '@/components/documents/document-list';
import { DocumentUpload } from '@/components/documents/document-upload';
import { Separator } from '@/components/ui/separator';
import { MessageSquare, Settings } from 'lucide-react';
import { useState } from 'react';

export default function HomePage() {
  const [currentNamespace, setCurrentNamespace] = useState('default');

  const handleNamespaceChange = (namespace: string) => {
    setCurrentNamespace(namespace);
  };

  const handleUploadSuccess = () => {
    // Документы автоматически обновятся через хук useDocuments
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Заголовок */}
      <header className="bg-white border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
              <MessageSquare className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold">RAG Crawl</h1>
              <p className="text-sm text-muted-foreground">
                Чат с документами на основе векторного поиска
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Основной контент */}
      <div className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-140px)]">
          {/* Левая панель - Чат */}
          <div className="lg:col-span-2">
            <ChatInterface
              namespace={currentNamespace}
              onNamespaceChange={handleNamespaceChange}
            />
          </div>

          {/* Правая панель - Управление документами */}
          <div className="space-y-6">
            {/* Загрузка документов */}
            <DocumentUpload
              namespace={currentNamespace}
              onUploadSuccess={handleUploadSuccess}
            />

            <Separator />

            {/* Список документов */}
            <DocumentList namespace={currentNamespace} />
          </div>
        </div>
      </div>

      {/* Футер */}
      <footer className="bg-white border-t mt-auto">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <div className="flex items-center gap-4">
              <span>&copy; 2024 RAG Crawl</span>
              <span>•</span>
              <span>Powered by LlamaIndex & Azure OpenAI</span>
            </div>
            <div className="flex items-center gap-2">
              <Settings className="w-4 h-4" />
              <span>Namespace: {currentNamespace}</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
