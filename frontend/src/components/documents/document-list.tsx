'use client';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useDocuments } from '@/hooks/use-documents';
import { DocumentResponse } from '@/lib/api';
import { formatDistance } from 'date-fns';
import { ru } from 'date-fns/locale';
import { Calendar, File, Hash, RefreshCw, Trash2 } from 'lucide-react';

interface DocumentListProps {
    namespace?: string;
}

export function DocumentList({ namespace }: DocumentListProps) {
    const {
        documents,
        isLoading,
        error,
        deleteDocument,
        refreshDocuments
    } = useDocuments(namespace);

    const handleDelete = async (documentId: number) => {
        if (confirm('Вы уверены, что хотите удалить этот документ?')) {
            await deleteDocument(documentId);
        }
    };

    if (error) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-red-600">
                        <File className="w-5 h-5" />
                        Ошибка загрузки
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-red-600 mb-4">{error}</div>
                    <Button onClick={refreshDocuments} variant="outline">
                        <RefreshCw className="w-4 h-4 mr-2" />
                        Попробовать снова
                    </Button>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card>
            <CardHeader>
                <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                        <File className="w-5 h-5" />
                        Документы ({documents.length})
                    </CardTitle>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={refreshDocuments}
                        disabled={isLoading}
                    >
                        <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                    </Button>
                </div>
            </CardHeader>

            <CardContent className="p-0">
                <ScrollArea className="h-[400px]">
                    {isLoading ? (
                        <div className="flex items-center justify-center py-8">
                            <RefreshCw className="w-6 h-6 animate-spin mr-2" />
                            <span>Загружаем документы...</span>
                        </div>
                    ) : documents.length === 0 ? (
                        <div className="text-center py-8 px-6 text-muted-foreground">
                            <File className="w-12 h-12 mx-auto mb-4 opacity-50" />
                            <p>Документы не найдены</p>
                            <p className="text-sm mt-2">
                                Загрузите документы для начала работы
                            </p>
                        </div>
                    ) : (
                        <div className="space-y-2 p-6">
                            {documents.map((doc) => (
                                <DocumentItem
                                    key={doc.id}
                                    document={doc}
                                    onDelete={() => handleDelete(doc.id)}
                                />
                            ))}
                        </div>
                    )}
                </ScrollArea>
            </CardContent>
        </Card>
    );
}

interface DocumentItemProps {
    document: DocumentResponse;
    onDelete: () => void;
}

function DocumentItem({ document, onDelete }: DocumentItemProps) {
    const formatDate = (dateString: string) => {
        try {
            return formatDistance(new Date(dateString), new Date(), {
                addSuffix: true,
                locale: ru
            });
        } catch {
            return dateString;
        }
    };

    return (
        <Card className="hover:bg-muted/50 transition-colors">
            <CardContent className="p-4">
                <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                            <File className="w-4 h-4 text-blue-500 flex-shrink-0" />
                            <h3 className="font-medium truncate">{document.title}</h3>
                        </div>

                        <div className="space-y-1 text-sm text-muted-foreground">
                            <div className="flex items-center gap-1">
                                <Hash className="w-3 h-3" />
                                <span>ID: {document.id}</span>
                            </div>

                            <div className="flex items-center gap-1">
                                <Calendar className="w-3 h-3" />
                                <span>Создан: {formatDate(document.created_at)}</span>
                            </div>

                            <div className="flex items-center gap-2">
                                <Badge variant="secondary" className="text-xs">
                                    {document.source_type}
                                </Badge>
                                <Badge variant="outline" className="text-xs">
                                    {document.namespace}
                                </Badge>
                                <Badge variant="outline" className="text-xs">
                                    {document.chunks_count} чанков
                                </Badge>
                            </div>
                        </div>
                    </div>

                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={onDelete}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                        <Trash2 className="w-4 h-4" />
                    </Button>
                </div>
            </CardContent>
        </Card>
    );
} 