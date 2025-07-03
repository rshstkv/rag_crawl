"use client";

import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogTrigger
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
    Sheet,
    SheetContent,
    SheetDescription,
    SheetHeader,
    SheetTitle
} from "@/components/ui/sheet";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow
} from "@/components/ui/table";
import {
    Tabs,
    TabsContent,
    TabsList,
    TabsTrigger
} from "@/components/ui/tabs";
import {
    Database,
    Eye,
    FileText,
    MoreHorizontal,
    RefreshCw,
    Search,
    Trash2
} from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import {
    apiClient,
    type DocumentChunk,
    type DocumentContent,
    type DocumentResponse,
    type SystemDiagnostics
} from "@/lib/api";

export default function DocumentsPage() {
    const [documents, setDocuments] = useState<DocumentResponse[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedDocuments, setSelectedDocuments] = useState<Set<number>>(new Set());
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedNamespace, setSelectedNamespace] = useState<string>("all");
    const [isReindexing, setIsReindexing] = useState(false);
    const [diagnostics, setDiagnostics] = useState<SystemDiagnostics | null>(null);
    const [documentContent, setDocumentContent] = useState<DocumentContent | null>(null);
    const [documentChunks, setDocumentChunks] = useState<DocumentChunk[]>([]);
    const [showDocumentViewer, setShowDocumentViewer] = useState(false);

    // Загрузка документов
    const loadDocuments = async () => {
        try {
            setLoading(true);
            const docs = await apiClient.getDocuments();
            setDocuments(docs);
        } catch (error) {
            console.error("Failed to load documents:", error);
            toast.error("Ошибка загрузки документов");
        } finally {
            setLoading(false);
        }
    };

    // Загрузка диагностики
    const loadDiagnostics = async () => {
        try {
            const diag = await apiClient.getSystemDiagnostics();
            setDiagnostics(diag);
        } catch (error) {
            console.error("Failed to load diagnostics:", error);
        }
    };

    useEffect(() => {
        loadDocuments();
        loadDiagnostics();
    }, []);

    // Фильтрация документов
    const filteredDocuments = documents.filter(doc => {
        const matchesSearch = doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
            doc.source_type.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesNamespace = selectedNamespace === "all" || doc.namespace === selectedNamespace;
        return matchesSearch && matchesNamespace;
    });

    // Получение уникальных namespace
    const namespaces = Array.from(new Set(documents.map(doc => doc.namespace)));

    // Выбор/снятие выбора всех документов
    const toggleAllDocuments = () => {
        if (selectedDocuments.size === filteredDocuments.length) {
            setSelectedDocuments(new Set());
        } else {
            setSelectedDocuments(new Set(filteredDocuments.map(doc => doc.id)));
        }
    };

    // Выбор/снятие выбора документа
    const toggleDocument = (documentId: number) => {
        const newSelected = new Set(selectedDocuments);
        if (newSelected.has(documentId)) {
            newSelected.delete(documentId);
        } else {
            newSelected.add(documentId);
        }
        setSelectedDocuments(newSelected);
    };

    // Переиндексация выбранных документов
    const handleBatchReindex = async () => {
        if (selectedDocuments.size === 0) return;

        try {
            setIsReindexing(true);
            const result = await apiClient.reindexBatchDocuments(Array.from(selectedDocuments));
            toast.success(`Переиндексировано ${result.documents_processed} из ${result.total_documents} документов`);
            setSelectedDocuments(new Set());
            loadDiagnostics();
        } catch (error) {
            console.error("Batch reindex failed:", error);
            toast.error("Ошибка переиндексации документов");
        } finally {
            setIsReindexing(false);
        }
    };

    // Переиндексация всех документов
    const handleReindexAll = async () => {
        try {
            setIsReindexing(true);
            const result = await apiClient.reindexAllDocuments();
            toast.success(`Переиндексировано ${result.documents_processed} документов`);
            loadDiagnostics();
        } catch (error) {
            console.error("Reindex all failed:", error);
            toast.error("Ошибка переиндексации всех документов");
        } finally {
            setIsReindexing(false);
        }
    };

    // Переиндексация одного документа
    const handleReindexDocument = async (documentId: number) => {
        try {
            await apiClient.reindexDocument(documentId);
            toast.success("Документ переиндексирован");
            loadDiagnostics();
        } catch (error) {
            console.error("Document reindex failed:", error);
            toast.error("Ошибка переиндексации документа");
        }
    };

    // Удаление документа
    const handleDeleteDocument = async (documentId: number) => {
        try {
            await apiClient.deleteDocument(documentId);
            toast.success("Документ удален");
            loadDocuments();
            loadDiagnostics();
            setSelectedDocuments(prev => {
                const newSet = new Set(prev);
                newSet.delete(documentId);
                return newSet;
            });
        } catch (error) {
            console.error("Document delete failed:", error);
            toast.error("Ошибка удаления документа");
        }
    };

    // Просмотр содержимого документа
    const handleViewDocument = async (documentId: number) => {
        try {
            const [content, chunksResponse] = await Promise.all([
                apiClient.getDocumentContent(documentId),
                apiClient.getDocumentChunks(documentId)
            ]);
            setDocumentContent(content);
            setDocumentChunks(chunksResponse.chunks);
            setShowDocumentViewer(true);
        } catch (error) {
            console.error("Failed to load document content:", error);
            toast.error("Ошибка загрузки содержимого документа");
        }
    };

    // Форматирование даты
    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('ru-RU', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    // Определение цвета бейджа по типу файла
    const getFileTypeBadgeVariant = (sourceType: string) => {
        switch (sourceType) {
            case 'pdf': return 'destructive';
            case 'txt': return 'secondary';
            case 'docx': case 'doc': return 'default';
            case 'md': return 'outline';
            default: return 'secondary';
        }
    };

    return (
        <div className="container mx-auto p-6 space-y-6">
            {/* Заголовок */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold">Управление документами</h1>
                    <p className="text-muted-foreground">
                        Просмотр, поиск и управление загруженными документами
                    </p>
                </div>
            </div>

            {/* Диагностика системы */}
            {diagnostics && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Database className="h-5 w-5" />
                            Состояние системы
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="text-center">
                                <div className="text-2xl font-bold text-blue-600">
                                    {diagnostics.postgresql.total_documents}
                                </div>
                                <div className="text-sm text-muted-foreground">
                                    Документов в PostgreSQL
                                </div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-green-600">
                                    {diagnostics.qdrant.points_count}
                                </div>
                                <div className="text-sm text-muted-foreground">
                                    Векторов в Qdrant
                                </div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-purple-600">
                                    {diagnostics.postgresql.total_chunks}
                                </div>
                                <div className="text-sm text-muted-foreground">
                                    Чанков создано
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Фильтры и поиск */}
            <Card>
                <CardContent className="pt-6">
                    <div className="flex flex-col md:flex-row gap-4">
                        <div className="flex-1">
                            <div className="relative">
                                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                <Input
                                    placeholder="Поиск по названию или типу файла..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="pl-9"
                                />
                            </div>
                        </div>
                        <div className="flex gap-2">
                            <select
                                className="px-3 py-2 border rounded-md"
                                value={selectedNamespace}
                                onChange={(e) => setSelectedNamespace(e.target.value)}
                            >
                                <option value="all">Все namespace</option>
                                {namespaces.map(ns => (
                                    <option key={ns} value={ns}>{ns}</option>
                                ))}
                            </select>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Групповые действия */}
            {selectedDocuments.size > 0 && (
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <span className="text-sm text-muted-foreground">
                                Выбрано документов: {selectedDocuments.size}
                            </span>
                            <div className="flex gap-2">
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={handleBatchReindex}
                                    disabled={isReindexing}
                                >
                                    <RefreshCw className="h-4 w-4 mr-2" />
                                    Переиндексировать выбранные
                                </Button>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => setSelectedDocuments(new Set())}
                                >
                                    Снять выделение
                                </Button>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Таблица документов */}
            <Card>
                <CardHeader>
                    <div className="flex justify-between items-center">
                        <CardTitle>Документы ({filteredDocuments.length})</CardTitle>
                        <Button
                            variant="outline"
                            onClick={handleReindexAll}
                            disabled={isReindexing || documents.length === 0}
                        >
                            <RefreshCw className="h-4 w-4 mr-2" />
                            Переиндексировать все
                        </Button>
                    </div>
                </CardHeader>
                <CardContent>
                    {loading ? (
                        <div className="text-center py-8">
                            <div className="text-muted-foreground">Загрузка документов...</div>
                        </div>
                    ) : filteredDocuments.length === 0 ? (
                        <div className="text-center py-8">
                            <FileText className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
                            <div className="text-muted-foreground">
                                {documents.length === 0 ? "Нет загруженных документов" : "Нет документов, соответствующих фильтрам"}
                            </div>
                        </div>
                    ) : (
                        <div className="rounded-md border">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead className="w-[50px]">
                                            <Checkbox
                                                checked={selectedDocuments.size === filteredDocuments.length && filteredDocuments.length > 0}
                                                onCheckedChange={toggleAllDocuments}
                                            />
                                        </TableHead>
                                        <TableHead>Название</TableHead>
                                        <TableHead>Тип</TableHead>
                                        <TableHead>Namespace</TableHead>
                                        <TableHead>Чанки</TableHead>
                                        <TableHead>Дата создания</TableHead>
                                        <TableHead className="text-right">Действия</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {filteredDocuments.map((doc) => (
                                        <TableRow key={doc.id}>
                                            <TableCell>
                                                <Checkbox
                                                    checked={selectedDocuments.has(doc.id)}
                                                    onCheckedChange={() => toggleDocument(doc.id)}
                                                />
                                            </TableCell>
                                            <TableCell className="font-medium">{doc.title}</TableCell>
                                            <TableCell>
                                                <Badge variant={getFileTypeBadgeVariant(doc.source_type)}>
                                                    {doc.source_type}
                                                </Badge>
                                            </TableCell>
                                            <TableCell>
                                                <Badge variant="outline">{doc.namespace}</Badge>
                                            </TableCell>
                                            <TableCell>{doc.chunks_count}</TableCell>
                                            <TableCell className="text-muted-foreground">
                                                {formatDate(doc.created_at)}
                                            </TableCell>
                                            <TableCell className="text-right">
                                                <DropdownMenu>
                                                    <DropdownMenuTrigger asChild>
                                                        <Button variant="ghost" className="h-8 w-8 p-0">
                                                            <MoreHorizontal className="h-4 w-4" />
                                                        </Button>
                                                    </DropdownMenuTrigger>
                                                    <DropdownMenuContent align="end">
                                                        <DropdownMenuItem onClick={() => handleViewDocument(doc.id)}>
                                                            <Eye className="h-4 w-4 mr-2" />
                                                            Просмотр
                                                        </DropdownMenuItem>
                                                        <DropdownMenuItem onClick={() => handleReindexDocument(doc.id)}>
                                                            <RefreshCw className="h-4 w-4 mr-2" />
                                                            Переиндексировать
                                                        </DropdownMenuItem>
                                                        <AlertDialog>
                                                            <AlertDialogTrigger asChild>
                                                                <DropdownMenuItem onSelect={(e) => e.preventDefault()}>
                                                                    <Trash2 className="h-4 w-4 mr-2" />
                                                                    Удалить
                                                                </DropdownMenuItem>
                                                            </AlertDialogTrigger>
                                                            <AlertDialogContent>
                                                                <AlertDialogHeader>
                                                                    <AlertDialogTitle>Подтвердите удаление</AlertDialogTitle>
                                                                    <AlertDialogDescription>
                                                                        Вы уверены, что хотите удалить документ "{doc.title}"?
                                                                        Это действие нельзя отменить.
                                                                    </AlertDialogDescription>
                                                                </AlertDialogHeader>
                                                                <AlertDialogFooter>
                                                                    <AlertDialogCancel>Отмена</AlertDialogCancel>
                                                                    <AlertDialogAction
                                                                        onClick={() => handleDeleteDocument(doc.id)}
                                                                        className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                                                                    >
                                                                        Удалить
                                                                    </AlertDialogAction>
                                                                </AlertDialogFooter>
                                                            </AlertDialogContent>
                                                        </AlertDialog>
                                                    </DropdownMenuContent>
                                                </DropdownMenu>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Просмотр документа */}
            <Sheet open={showDocumentViewer} onOpenChange={setShowDocumentViewer}>
                <SheetContent className="sm:max-w-[800px] w-full">
                    {documentContent && (
                        <>
                            <SheetHeader>
                                <SheetTitle>{documentContent.document.title}</SheetTitle>
                                <SheetDescription>
                                    {documentContent.document.source_type} • {documentContent.document.namespace} •
                                    {documentContent.document.chunks_count} чанков
                                </SheetDescription>
                            </SheetHeader>
                            <Tabs defaultValue="content" className="w-full mt-6">
                                <TabsList>
                                    <TabsTrigger value="content">Содержимое</TabsTrigger>
                                    <TabsTrigger value="chunks">Чанки ({documentChunks.length})</TabsTrigger>
                                    <TabsTrigger value="metadata">Метаданные</TabsTrigger>
                                </TabsList>
                                <TabsContent value="content">
                                    <ScrollArea className="h-[600px] w-full border rounded-md p-4">
                                        <pre className="whitespace-pre-wrap text-sm">
                                            {documentContent.full_text}
                                        </pre>
                                    </ScrollArea>
                                </TabsContent>
                                <TabsContent value="chunks">
                                    <ScrollArea className="h-[600px] w-full">
                                        <div className="space-y-4">
                                            {documentChunks.map((chunk, index) => (
                                                <Card key={chunk.id}>
                                                    <CardHeader className="pb-2">
                                                        <CardTitle className="text-sm">
                                                            Чанк {chunk.chunk_index + 1}
                                                        </CardTitle>
                                                        <CardDescription className="text-xs">
                                                            ID: {chunk.vector_id}
                                                        </CardDescription>
                                                    </CardHeader>
                                                    <CardContent>
                                                        <pre className="whitespace-pre-wrap text-sm">
                                                            {chunk.content}
                                                        </pre>
                                                    </CardContent>
                                                </Card>
                                            ))}
                                        </div>
                                    </ScrollArea>
                                </TabsContent>
                                <TabsContent value="metadata">
                                    <ScrollArea className="h-[600px] w-full">
                                        <div className="space-y-4">
                                            <Card>
                                                <CardHeader>
                                                    <CardTitle className="text-sm">Информация о документе</CardTitle>
                                                </CardHeader>
                                                <CardContent className="space-y-2">
                                                    <div className="grid grid-cols-2 gap-2 text-sm">
                                                        <div className="font-medium">ID:</div>
                                                        <div>{documentContent.document.id}</div>
                                                        <div className="font-medium">Тип:</div>
                                                        <div>{documentContent.document.source_type}</div>
                                                        <div className="font-medium">Namespace:</div>
                                                        <div>{documentContent.document.namespace}</div>
                                                        <div className="font-medium">Создано:</div>
                                                        <div>{formatDate(documentContent.document.created_at)}</div>
                                                        <div className="font-medium">Чанков:</div>
                                                        <div>{documentContent.document.chunks_count}</div>
                                                    </div>
                                                </CardContent>
                                            </Card>
                                            <Card>
                                                <CardHeader>
                                                    <CardTitle className="text-sm">Метаданные</CardTitle>
                                                </CardHeader>
                                                <CardContent>
                                                    <pre className="text-xs">
                                                        {JSON.stringify(documentContent.document.metadata, null, 2)}
                                                    </pre>
                                                </CardContent>
                                            </Card>
                                        </div>
                                    </ScrollArea>
                                </TabsContent>
                            </Tabs>
                        </>
                    )}
                </SheetContent>
            </Sheet>
        </div>
    );
} 