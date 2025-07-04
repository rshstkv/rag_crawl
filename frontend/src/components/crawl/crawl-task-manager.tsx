"use client";

import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { useCrawl } from '@/hooks/use-crawl';
import {
    AlertCircle,
    CheckCircle,
    Clock,
    FileText,
    Globe,
    Loader2,
    Pause,
    Play,
    Square,
    Trash2
} from 'lucide-react';
import { useEffect, useState } from 'react';

interface CrawlTask {
    taskId: string;
    url: string;
    status: 'running' | 'paused' | 'completed' | 'error' | 'stopped';
    processed: number;
    total: number;
    currentUrl?: string;
    startTime: string;
    endTime?: string;
    namespace: string;
    error?: string;
}

export function CrawlTaskManager() {
    const [tasks, setTasks] = useState<CrawlTask[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const {
        stopCrawl,
        pauseCrawl,
        resumeCrawl,
        stopAllCrawls
    } = useCrawl();

    const fetchTasks = async () => {
        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch('/api/crawl/active');
            if (!response.ok) {
                throw new Error('Не удалось получить список задач');
            }

            const data = await response.json();
            setTasks(data.task_details || []);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Ошибка загрузки задач');
            console.error('Ошибка при загрузке задач:', err);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchTasks();
        const interval = setInterval(fetchTasks, 3000);
        return () => clearInterval(interval);
    }, []);

    const handleStopTask = async (taskId: string) => {
        try {
            await stopCrawl(taskId);
            await fetchTasks();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Ошибка остановки задачи');
        }
    };

    const handlePauseTask = async (taskId: string) => {
        try {
            await pauseCrawl(taskId);
            await fetchTasks();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Ошибка приостановки задачи');
        }
    };

    const handleResumeTask = async (taskId: string) => {
        try {
            await resumeCrawl(taskId);
            await fetchTasks();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Ошибка возобновления задачи');
        }
    };

    const handleStopAllTasks = async () => {
        try {
            await stopAllCrawls();
            await fetchTasks();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Ошибка остановки всех задач');
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'running':
                return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
            case 'paused':
                return <Pause className="h-4 w-4 text-yellow-500" />;
            case 'completed':
                return <CheckCircle className="h-4 w-4 text-green-500" />;
            case 'error':
                return <AlertCircle className="h-4 w-4 text-red-500" />;
            case 'stopped':
                return <Square className="h-4 w-4 text-gray-500" />;
            default:
                return <Clock className="h-4 w-4 text-gray-400" />;
        }
    };

    const getStatusBadge = (status: string) => {
        const statusMap = {
            running: { text: 'Выполняется', variant: 'default' as const },
            paused: { text: 'Приостановлено', variant: 'secondary' as const },
            completed: { text: 'Завершено', variant: 'default' as const },
            error: { text: 'Ошибка', variant: 'destructive' as const },
            stopped: { text: 'Остановлено', variant: 'outline' as const }
        };

        const statusInfo = statusMap[status as keyof typeof statusMap] || { text: status, variant: 'outline' as const };
        return <Badge variant={statusInfo.variant}>{statusInfo.text}</Badge>;
    };

    const getProgressPercentage = (task: CrawlTask) => {
        return task.total > 0 ? Math.round((task.processed / task.total) * 100) : 0;
    };

    const formatDuration = (startTime: string, endTime?: string) => {
        const start = new Date(startTime);
        const end = endTime ? new Date(endTime) : new Date();
        const duration = Math.floor((end.getTime() - start.getTime()) / 1000);

        if (duration < 60) {
            return `${duration}с`;
        } else if (duration < 3600) {
            return `${Math.floor(duration / 60)}мин ${duration % 60}с`;
        } else {
            const hours = Math.floor(duration / 3600);
            const minutes = Math.floor((duration % 3600) / 60);
            return `${hours}ч ${minutes}мин`;
        }
    };

    if (isLoading && tasks.length === 0) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle>Активные задачи</CardTitle>
                    <CardDescription>Загрузка...</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center justify-center py-8">
                        <Loader2 className="h-6 w-6 animate-spin" />
                    </div>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card>
            <CardHeader>
                <div className="flex items-center justify-between">
                    <div>
                        <CardTitle className="flex items-center gap-2">
                            <Globe className="h-5 w-5" />
                            Активные задачи
                        </CardTitle>
                        <CardDescription>
                            Текущие задачи кроулинга и их статус
                        </CardDescription>
                    </div>
                    {tasks.length > 0 && (
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={handleStopAllTasks}
                            className="flex items-center gap-2"
                        >
                            <Trash2 className="h-4 w-4" />
                            Остановить все
                        </Button>
                    )}
                </div>
            </CardHeader>
            <CardContent>
                {error && (
                    <Alert className="mb-4 border-red-200 bg-red-50">
                        <AlertCircle className="h-4 w-4 text-red-500" />
                        <AlertDescription className="text-red-700">
                            {error}
                        </AlertDescription>
                    </Alert>
                )}

                {tasks.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                        <Globe className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>Нет активных задач кроулинга</p>
                        <p className="text-sm">Запустите новую задачу на вкладке &quot;Парсинг веб-сайта&quot;</p>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {tasks.map((task, index) => (
                            <div key={task.taskId} className="border rounded-lg p-4 space-y-4">
                                <div className="flex items-start justify-between">
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 mb-2">
                                            {getStatusIcon(task.status)}
                                            <span className="font-medium text-sm truncate">{task.url}</span>
                                            {getStatusBadge(task.status)}
                                        </div>

                                        <div className="grid grid-cols-2 gap-4 text-sm text-muted-foreground">
                                            <div className="flex items-center gap-2">
                                                <FileText className="h-4 w-4" />
                                                <span>Namespace: {task.namespace}</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <Clock className="h-4 w-4" />
                                                <span>Время: {formatDuration(task.startTime, task.endTime)}</span>
                                            </div>
                                        </div>

                                        {task.currentUrl && task.status === 'running' && (
                                            <div className="mt-2 text-xs text-muted-foreground truncate">
                                                Текущая страница: {task.currentUrl}
                                            </div>
                                        )}

                                        {task.error && (
                                            <div className="mt-2 text-sm text-red-600 bg-red-50 p-2 rounded">
                                                {task.error}
                                            </div>
                                        )}
                                    </div>

                                    <div className="flex gap-2 ml-4">
                                        {task.status === 'running' && (
                                            <>
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={() => handlePauseTask(task.taskId)}
                                                    className="flex items-center gap-1"
                                                >
                                                    <Pause className="h-3 w-3" />
                                                    Пауза
                                                </Button>
                                                <Button
                                                    variant="destructive"
                                                    size="sm"
                                                    onClick={() => handleStopTask(task.taskId)}
                                                    className="flex items-center gap-1"
                                                >
                                                    <Square className="h-3 w-3" />
                                                    Стоп
                                                </Button>
                                            </>
                                        )}

                                        {task.status === 'paused' && (
                                            <>
                                                <Button
                                                    variant="default"
                                                    size="sm"
                                                    onClick={() => handleResumeTask(task.taskId)}
                                                    className="flex items-center gap-1"
                                                >
                                                    <Play className="h-3 w-3" />
                                                    Продолжить
                                                </Button>
                                                <Button
                                                    variant="destructive"
                                                    size="sm"
                                                    onClick={() => handleStopTask(task.taskId)}
                                                    className="flex items-center gap-1"
                                                >
                                                    <Square className="h-3 w-3" />
                                                    Стоп
                                                </Button>
                                            </>
                                        )}
                                    </div>
                                </div>

                                {/* Прогресс */}
                                {task.total > 0 && (
                                    <div className="space-y-2">
                                        <div className="flex justify-between text-sm">
                                            <span>Прогресс: {task.processed}/{task.total} страниц</span>
                                            <span>{getProgressPercentage(task)}%</span>
                                        </div>
                                        <Progress value={getProgressPercentage(task)} className="h-2" />
                                    </div>
                                )}

                                {index < tasks.length - 1 && <Separator className="mt-4" />}
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    );
} 