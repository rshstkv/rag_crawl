import { useCallback, useEffect, useState } from 'react';

interface CrawlConfig {
    url: string;
    maxDepth: number;
    maxPages: number;
    browserType: string;
    waitUntil: string;
    excludeExternalLinks: boolean;
    excludeExternalImages: boolean;
    wordCountThreshold: number;
    pageTimeout: number;
    namespace: string;
}

interface CrawlProgress {
    taskId: string;
    processed: number;
    total: number;
    currentUrl: string;
    status: string;
    pages: unknown[];
}

interface UseCrawlOptions {
    onCrawlComplete?: () => void;
}

export const useCrawl = (options?: UseCrawlOptions) => {
    const [isLoading, setIsLoading] = useState(false);
    const [progress, setProgress] = useState<CrawlProgress | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [activeTasks, setActiveTasks] = useState<string[]>([]);

    const { onCrawlComplete } = options || {};

    const startCrawl = useCallback(async (config: CrawlConfig) => {
        setIsLoading(true);
        setError(null);
        setProgress(null);

        try {
            const eventSource = new EventSource(
                `/api/crawl/start?${new URLSearchParams({
                    url: config.url,
                    max_depth: config.maxDepth.toString(),
                    max_pages: config.maxPages.toString(),
                    browser_type: config.browserType,
                    wait_until: config.waitUntil,
                    exclude_external_links: config.excludeExternalLinks.toString(),
                    exclude_external_images: config.excludeExternalImages.toString(),
                    word_count_threshold: config.wordCountThreshold.toString(),
                    page_timeout: config.pageTimeout.toString(),
                    namespace: config.namespace,
                })}`,
                {
                    withCredentials: false,
                }
            );

            eventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);

                    switch (data.type) {
                        case 'crawl_started':
                            setProgress({
                                taskId: data.task_id,
                                status: 'running',
                                processed: 0,
                                total: 0,
                                currentUrl: '',
                                pages: []
                            });
                            break;
                        case 'progress':
                            setProgress(prev => prev ? {
                                ...prev,
                                processed: data.processed || 0,
                                total: data.total || 0,
                                currentUrl: data.current_url || '',
                                status: 'running'
                            } : null);
                            break;
                        case 'page_complete':
                            setProgress(prev => prev ? {
                                ...prev,
                                pages: [...prev.pages, data.page]
                            } : null);
                            break;
                        case 'crawl_complete':
                            setIsLoading(false);
                            setProgress(prev => prev ? {
                                ...prev,
                                status: 'completed'
                            } : null);
                            eventSource.close();
                            if (onCrawlComplete) {
                                onCrawlComplete();
                            }
                            break;
                        case 'error':
                            setError(data.message || 'Произошла ошибка при кроулинге');
                            setIsLoading(false);
                            eventSource.close();
                            break;
                    }
                } catch (err) {
                    console.error('Ошибка парсинга события SSE:', err);
                }
            };

            eventSource.onerror = (err) => {
                console.error('Ошибка SSE:', err);
                setError('Ошибка соединения с сервером');
                setIsLoading(false);
                eventSource.close();
            };

            // Возвращаем функцию для закрытия соединения
            return () => {
                eventSource.close();
                setIsLoading(false);
            };

        } catch (err) {
            console.error('Ошибка при запуске кроулинга:', err);
            setError('Ошибка при запуске кроулинга');
            setIsLoading(false);
        }
    }, [onCrawlComplete]);

    const stopCrawl = useCallback(async (taskId: string) => {
        try {
            const response = await fetch(`/api/crawl/stop/${taskId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const errorData = await response.text();
                throw new Error(`Не удалось остановить задачу: ${errorData}`);
            }

            setProgress(prev => prev ? { ...prev, status: 'stopped' } : null);
            setIsLoading(false);
        } catch (err) {
            console.error('Ошибка при остановке кроулинга:', err);
            setError(err instanceof Error ? err.message : 'Ошибка при остановке кроулинга');
        }
    }, []);

    const pauseCrawl = useCallback(async (taskId: string) => {
        try {
            const response = await fetch(`/api/crawl/pause/${taskId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const errorData = await response.text();
                throw new Error(`Не удалось приостановить задачу: ${errorData}`);
            }

            setProgress(prev => prev ? { ...prev, status: 'paused' } : null);
        } catch (err) {
            console.error('Ошибка при приостановке кроулинга:', err);
            setError(err instanceof Error ? err.message : 'Ошибка при приостановке кроулинга');
        }
    }, []);

    const resumeCrawl = useCallback(async (taskId: string) => {
        try {
            const response = await fetch(`/api/crawl/resume/${taskId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const errorData = await response.text();
                throw new Error(`Не удалось возобновить задачу: ${errorData}`);
            }

            setProgress(prev => prev ? { ...prev, status: 'running' } : null);
            setIsLoading(true);
        } catch (err) {
            console.error('Ошибка при возобновлении кроулинга:', err);
            setError(err instanceof Error ? err.message : 'Ошибка при возобновлении кроулинга');
        }
    }, []);

    const stopAllCrawls = useCallback(async () => {
        try {
            const response = await fetch('/api/crawl/stop-all', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const errorData = await response.text();
                throw new Error(`Не удалось остановить все задачи: ${errorData}`);
            }

            setActiveTasks([]);
            setIsLoading(false);
            setProgress(null);
        } catch (err) {
            console.error('Ошибка при остановке всех задач:', err);
            setError(err instanceof Error ? err.message : 'Ошибка при остановке всех задач');
        }
    }, []);

    const getActiveTasks = useCallback(async () => {
        try {
            const response = await fetch('/api/crawl/active');

            if (!response.ok) {
                throw new Error('Не удалось получить список активных задач');
            }

            const data = await response.json();
            setActiveTasks(data.active_tasks || []);
        } catch (err) {
            console.error('Ошибка при получении активных задач:', err);
        }
    }, []);

    // Периодическое обновление списка активных задач
    useEffect(() => {
        getActiveTasks();
        const interval = setInterval(getActiveTasks, 5000);
        return () => clearInterval(interval);
    }, [getActiveTasks]);

    return {
        isLoading,
        progress,
        error,
        activeTasks,
        startCrawl,
        stopCrawl,
        pauseCrawl,
        resumeCrawl,
        stopAllCrawls,
        getActiveTasks,
    };
}; 