'use client';

import { ChatInterface } from '@/components/chat/chat-interface';
import { DocumentUpload } from '@/components/documents/document-upload';
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

          {/* Правая панель - Загрузка документов */}
          <div className="space-y-6">
            <DocumentUpload
              namespace={currentNamespace}
              onUploadSuccess={handleUploadSuccess}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
