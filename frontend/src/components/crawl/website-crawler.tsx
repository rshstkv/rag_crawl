"use client";

import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { useCrawl } from '@/hooks/use-crawl';
import { AlertCircle, CheckCircle, Loader2, Pause, Play, RotateCcw, Square } from 'lucide-react';
import { useState } from 'react';

interface CrawlConfig {
    url: string;
    maxDepth: number;
    maxPages: number;
    browserType: 'chromium' | 'firefox' | 'webkit';
    waitUntil: 'networkidle' | 'domcontentloaded' | 'load';
    excludeExternalLinks: boolean;
    excludeExternalImages: boolean;
    wordCountThreshold: number;
    pageTimeout: number;
    namespace: string;
}

interface WebsiteCrawlerProps {
    onCrawlComplete?: () => void;
}

export function WebsiteCrawler({ onCrawlComplete }: WebsiteCrawlerProps) {
    const [config, setConfig] = useState<CrawlConfig>({
        url: '',
        maxDepth: 3,
        maxPages: 50,
        browserType: 'chromium',
        waitUntil: 'networkidle',
        excludeExternalLinks: false,
        excludeExternalImages: false,
        wordCountThreshold: 5,
        pageTimeout: 60000,
        namespace: 'default'
    });

    const [errors, setErrors] = useState<Record<string, string>>({});

    const {
        isLoading,
        progress,
        error,
        activeTasks,
        startCrawl,
        stopCrawl,
        pauseCrawl,
        resumeCrawl,
        stopAllCrawls
    } = useCrawl({ onCrawlComplete });

    const validateUrl = (url: string): boolean => {
        try {
            new URL(url);
            return url.startsWith('http://') || url.startsWith('https://');
        } catch {
            return false;
        }
    };

    const validateConfig = (): boolean => {
        const newErrors: Record<string, string> = {};

        if (!config.url) {
            newErrors.url = 'URL обязателен';
        } else if (!validateUrl(config.url)) {
            newErrors.url = 'Введите корректный URL (http:// или https://)';
        }

        if (config.maxDepth < 1 || config.maxDepth > 10) {
            newErrors.maxDepth = 'Глубина должна быть от 1 до 10';
        }

        if (config.maxPages < 1 || config.maxPages > 5000) {
            newErrors.maxPages = 'Количество страниц должно быть от 1 до 5000';
        }

        if (!config.namespace.trim()) {
            newErrors.namespace = 'Namespace обязателен';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleStartCrawl = async () => {
        if (!validateConfig()) return;

        try {
            await startCrawl(config);
        } catch (err) {
            console.error('Ошибка запуска кроулинга:', err);
        }
    };

    const handleStopCrawl = async () => {
        if (progress?.taskId) {
            try {
                await stopCrawl(progress.taskId);
            } catch (err) {
                console.error('Ошибка остановки кроулинга:', err);
            }
        }
    };

    const handlePauseCrawl = async () => {
        if (progress?.taskId) {
            try {
                await pauseCrawl(progress.taskId);
            } catch (err) {
                console.error('Ошибка приостановки кроулинга:', err);
            }
        }
    };

    const handleResumeCrawl = async () => {
        if (progress?.taskId) {
            try {
                await resumeCrawl(progress.taskId);
            } catch (err) {
                console.error('Ошибка возобновления кроулинга:', err);
            }
        }
    };

    const getStatusIcon = () => {
        if (isLoading) {
            return <Loader2 className="h-4 w-4 animate-spin" />;
        }
        if (progress?.status === 'completed') {
            return <CheckCircle className="h-4 w-4 text-green-500" />;
        }
        if (progress?.status === 'error' || error) {
            return <AlertCircle className="h-4 w-4 text-red-500" />;
        }
        return null;
    };

    const getStatusText = () => {
        if (isLoading && progress?.status === 'running') {
            return `Обрабатывается: ${progress.processed || 0}/${progress.total || 0} страниц`;
        }
        if (progress?.status === 'paused') {
            return 'Приостановлено';
        }
        if (progress?.status === 'completed') {
            return `Завершено: обработано ${progress.processed || 0} страниц`;
        }
        if (progress?.status === 'error' || error) {
            return 'Ошибка';
        }
        return 'Готов к запуску';
    };

    const progressPercentage = progress && progress.total > 0
        ? Math.round((progress.processed / progress.total) * 100)
        : 0;

    return (
        <div className="space-y-6">
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        {getStatusIcon()}
                        Парсинг веб-сайта
                    </CardTitle>
                    <CardDescription>
                        Настройте параметры для автоматического парсинга веб-сайта и индексации контента
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    {/* URL и Namespace */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <label className="text-sm font-medium">URL сайта *</label>
                            <Input
                                placeholder="https://example.com"
                                value={config.url}
                                onChange={(e) => setConfig({ ...config, url: e.target.value })}
                                className={errors.url ? "border-red-500" : ""}
                            />
                            {errors.url && (
                                <p className="text-sm text-red-500">{errors.url}</p>
                            )}
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Namespace</label>
                            <Input
                                placeholder="default"
                                value={config.namespace}
                                onChange={(e) => setConfig({ ...config, namespace: e.target.value })}
                                className={errors.namespace ? "border-red-500" : ""}
                            />
                            {errors.namespace && (
                                <p className="text-sm text-red-500">{errors.namespace}</p>
                            )}
                        </div>
                    </div>

                    <Separator />

                    {/* Основные параметры */}
                    <div className="space-y-4">
                        <h3 className="text-lg font-medium">Параметры парсинга</h3>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Глубина парсинга</label>
                                <Select
                                    value={config.maxDepth.toString()}
                                    onValueChange={(value) => setConfig({ ...config, maxDepth: parseInt(value) })}
                                >
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((depth) => (
                                            <SelectItem key={depth} value={depth.toString()}>
                                                {depth} уровень{depth > 1 && depth < 5 ? 'я' : depth === 1 ? '' : 'ей'}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                {errors.maxDepth && (
                                    <p className="text-sm text-red-500">{errors.maxDepth}</p>
                                )}
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-medium">Максимум страниц</label>
                                <Input
                                    type="number"
                                    min="1"
                                    max="5000"
                                    value={config.maxPages}
                                    onChange={(e) => setConfig({ ...config, maxPages: parseInt(e.target.value) || 50 })}
                                    className={errors.maxPages ? "border-red-500" : ""}
                                />
                                {errors.maxPages && (
                                    <p className="text-sm text-red-500">{errors.maxPages}</p>
                                )}
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-medium">Браузер</label>
                                <Select
                                    value={config.browserType}
                                    onValueChange={(value: 'chromium' | 'firefox' | 'webkit') =>
                                        setConfig({ ...config, browserType: value })
                                    }
                                >
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="chromium">Chromium</SelectItem>
                                        <SelectItem value="firefox">Firefox</SelectItem>
                                        <SelectItem value="webkit">WebKit</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                    </div>

                    <Separator />

                    {/* Дополнительные настройки */}
                    <div className="space-y-4">
                        <h3 className="text-lg font-medium">Дополнительные настройки</h3>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Ожидание загрузки</label>
                                <Select
                                    value={config.waitUntil}
                                    onValueChange={(value: 'networkidle' | 'domcontentloaded' | 'load') =>
                                        setConfig({ ...config, waitUntil: value })
                                    }
                                >
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="networkidle">Сеть простаивает</SelectItem>
                                        <SelectItem value="domcontentloaded">DOM загружен</SelectItem>
                                        <SelectItem value="load">Полная загрузка</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-medium">Таймаут страницы (мс)</label>
                                <Input
                                    type="number"
                                    min="10000"
                                    max="300000"
                                    step="1000"
                                    value={config.pageTimeout}
                                    onChange={(e) => setConfig({ ...config, pageTimeout: parseInt(e.target.value) || 60000 })}
                                />
                            </div>
                        </div>

                        <div className="space-y-3">
                            <div className="flex items-center space-x-2">
                                <Checkbox
                                    id="exclude-external-links"
                                    checked={config.excludeExternalLinks}
                                    onCheckedChange={(checked) =>
                                        setConfig({ ...config, excludeExternalLinks: !!checked })
                                    }
                                />
                                <label htmlFor="exclude-external-links" className="text-sm">
                                    Исключить внешние ссылки
                                </label>
                            </div>

                            <div className="flex items-center space-x-2">
                                <Checkbox
                                    id="exclude-external-images"
                                    checked={config.excludeExternalImages}
                                    onCheckedChange={(checked) =>
                                        setConfig({ ...config, excludeExternalImages: !!checked })
                                    }
                                />
                                <label htmlFor="exclude-external-images" className="text-sm">
                                    Исключить внешние изображения
                                </label>
                            </div>
                        </div>
                    </div>

                    <Separator />

                    {/* Кнопки управления */}
                    <div className="flex flex-wrap gap-2">
                        {!isLoading && !progress?.taskId && (
                            <Button onClick={handleStartCrawl} className="flex items-center gap-2">
                                <Play className="h-4 w-4" />
                                Начать парсинг
                            </Button>
                        )}

                        {isLoading && progress?.status === 'running' && (
                            <>
                                <Button variant="destructive" onClick={handleStopCrawl} className="flex items-center gap-2">
                                    <Square className="h-4 w-4" />
                                    Остановить
                                </Button>
                                <Button variant="outline" onClick={handlePauseCrawl} className="flex items-center gap-2">
                                    <Pause className="h-4 w-4" />
                                    Пауза
                                </Button>
                            </>
                        )}

                        {progress?.status === 'paused' && (
                            <>
                                <Button onClick={handleResumeCrawl} className="flex items-center gap-2">
                                    <RotateCcw className="h-4 w-4" />
                                    Продолжить
                                </Button>
                                <Button variant="destructive" onClick={handleStopCrawl} className="flex items-center gap-2">
                                    <Square className="h-4 w-4" />
                                    Остановить
                                </Button>
                            </>
                        )}

                        {activeTasks.length > 0 && (
                            <Button variant="outline" onClick={stopAllCrawls} className="flex items-center gap-2">
                                <Square className="h-4 w-4" />
                                Остановить все ({activeTasks.length})
                            </Button>
                        )}
                    </div>

                    {/* Прогресс */}
                    {(isLoading || progress) && (
                        <div className="space-y-3">
                            <div className="flex items-center justify-between">
                                <span className="text-sm font-medium">{getStatusText()}</span>
                                {progress && progress.total > 0 && (
                                    <Badge variant="outline">{progressPercentage}%</Badge>
                                )}
                            </div>

                            {progress && progress.total > 0 && (
                                <Progress value={progressPercentage} className="w-full" />
                            )}

                            {progress?.currentUrl && (
                                <p className="text-xs text-muted-foreground truncate">
                                    Текущая страница: {progress.currentUrl}
                                </p>
                            )}
                        </div>
                    )}

                    {/* Ошибки */}
                    {error && (
                        <Alert className="border-red-200 bg-red-50">
                            <AlertCircle className="h-4 w-4 text-red-500" />
                            <AlertDescription className="text-red-700">
                                {error}
                            </AlertDescription>
                        </Alert>
                    )}

                    {/* Статус завершения */}
                    {progress?.status === 'completed' && (
                        <Alert className="border-green-200 bg-green-50">
                            <CheckCircle className="h-4 w-4 text-green-500" />
                            <AlertDescription className="text-green-700">
                                Парсинг завершен успешно! Обработано {progress.processed} страниц.
                                {progress.pages && progress.pages.length > 0 && (
                                    <span> Документы добавлены в namespace &quot;{config.namespace}&quot;.</span>
                                )}
                            </AlertDescription>
                        </Alert>
                    )}
                </CardContent>
            </Card>
        </div>
    );
} 