'use client';

import { ChatInterface } from '@/components/chat/chat-interface';
import { CrawlTaskManager } from '@/components/crawl/crawl-task-manager';
import { WebsiteCrawler } from '@/components/crawl/website-crawler';
import { DocumentUpload } from '@/components/documents/document-upload';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { apiClient, SystemDiagnostics } from '@/lib/api';
import { Database, RefreshCw } from 'lucide-react';
import { useEffect, useState } from 'react';

export default function HomePage() {
  const [currentNamespace, setCurrentNamespace] = useState('default');
  const [diagnostics, setDiagnostics] = useState<SystemDiagnostics | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleNamespaceChange = (namespace: string) => {
    setCurrentNamespace(namespace);
  };

  const handleUploadSuccess = () => {
    // Обновляем диагностику после успешной загрузки документа
    loadDiagnostics();
  };

  const loadDiagnostics = async () => {
    try {
      const diag = await apiClient.getSystemDiagnostics();
      setDiagnostics(diag);
    } catch (error) {
      console.error("Failed to load diagnostics:", error);
    }
  };

  const handleRefreshDiagnostics = async () => {
    setIsRefreshing(true);
    await loadDiagnostics();
    setIsRefreshing(false);
  };

  const handleCrawlComplete = () => {
    // Обновляем диагностику после завершения кроулинга
    loadDiagnostics();
  };

  useEffect(() => {
    loadDiagnostics();
  }, []);

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
            {/* Диагностика системы */}
            {diagnostics && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Database className="h-5 w-5" />
                      Состояние системы
                    </div>
                    <button
                      onClick={handleRefreshDiagnostics}
                      disabled={isRefreshing}
                      className="p-1 hover:bg-gray-100 rounded"
                    >
                      <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                    </button>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 gap-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Документов</span>
                      <Badge variant="secondary">{diagnostics.postgresql.total_documents}</Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Векторов</span>
                      <Badge variant="secondary">{diagnostics.qdrant.points_count}</Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Чанков</span>
                      <Badge variant="secondary">{diagnostics.postgresql.total_chunks}</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

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
                <WebsiteCrawler onCrawlComplete={handleCrawlComplete} />
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
