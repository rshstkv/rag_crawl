'use client';

import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Message } from '@/hooks/use-chat';
import { formatDistance } from 'date-fns';
import { ru } from 'date-fns/locale';
import {
    Bot,
    ChevronDown,
    ChevronRight,
    Clock,
    Database,
    ExternalLink,
    FileText,
    User
} from 'lucide-react';
import { useState } from 'react';

interface MessageItemProps {
    message: Message;
}

export function MessageItem({ message }: MessageItemProps) {
    const [showDebugInfo, setShowDebugInfo] = useState(false);
    const [showSources, setShowSources] = useState(true);

    const isUser = message.role === 'user';
    const timestamp = formatDistance(message.timestamp, new Date(), {
        addSuffix: true,
        locale: ru
    });

    // Извлекаем debug информацию из ответа
    const debugInfo = message.debugInfo;
    const hasDebugInfo = debugInfo && Object.keys(debugInfo).length > 0;

    return (
        <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
            <Avatar className="w-8 h-8 flex-shrink-0">
                <AvatarFallback className={isUser ? 'bg-blue-500 text-white' : 'bg-gray-100'}>
                    {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </AvatarFallback>
            </Avatar>

            <div className={`flex flex-col gap-1 max-w-[80%] ${isUser ? 'items-end' : 'items-start'}`}>
                <div className="text-xs text-muted-foreground">
                    {isUser ? 'Вы' : 'Assistant'} • {timestamp}
                </div>

                <Card className={`${isUser ? 'bg-blue-500 text-white' : 'bg-muted'}`}>
                    <CardContent className="p-3">
                        <div className="whitespace-pre-wrap break-words">
                            {message.content}
                        </div>

                        {/* Быстрая статистика для ассистента */}
                        {!isUser && ((message.sources && message.sources.length > 0) || hasDebugInfo) && (
                            <div className="mt-3 pt-3 border-t border-border/50">
                                <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
                                    {message.sources && message.sources.length > 0 && (
                                        <Badge variant="outline" className="text-xs">
                                            <FileText className="w-3 h-3 mr-1" />
                                            {message.sources.length} источников
                                        </Badge>
                                    )}
                                    {debugInfo?.search_time_ms && (
                                        <Badge variant="outline" className="text-xs">
                                            <Clock className="w-3 h-3 mr-1" />
                                            {debugInfo.search_time_ms.toFixed(0)}ms
                                        </Badge>
                                    )}
                                    {debugInfo?.collection_points_count && (
                                        <Badge variant="outline" className="text-xs">
                                            <Database className="w-3 h-3 mr-1" />
                                            {debugInfo.collection_points_count} документов
                                        </Badge>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Источники для ответов ассистента */}
                        {!isUser && message.sources && message.sources.length > 0 && (
                            <Collapsible open={showSources} onOpenChange={setShowSources}>
                                <CollapsibleTrigger asChild>
                                    <Button variant="ghost" size="sm" className="w-full justify-between p-0 h-auto">
                                        <span className="text-xs font-medium text-muted-foreground">
                                            📚 Источники ({message.sources.length})
                                        </span>
                                        {showSources ? (
                                            <ChevronDown className="w-3 h-3" />
                                        ) : (
                                            <ChevronRight className="w-3 h-3" />
                                        )}
                                    </Button>
                                </CollapsibleTrigger>
                                <CollapsibleContent className="mt-2">
                                    <div className="space-y-2">
                                        {message.sources.map((source, index) => (
                                            <div key={index} className="text-xs bg-background/50 rounded p-2">
                                                <div className="flex items-center gap-1 mb-1">
                                                    <ExternalLink className="w-3 h-3 flex-shrink-0" />
                                                    <span className="font-medium">
                                                        {source.document_title || 'Документ'}
                                                    </span>
                                                    {source.source_type && (
                                                        <Badge variant="secondary" className="text-xs h-4">
                                                            {source.source_type}
                                                        </Badge>
                                                    )}
                                                </div>
                                                {source.score && (
                                                    <div className="text-muted-foreground mb-1">
                                                        Релевантность: {(source.score * 100).toFixed(1)}%
                                                    </div>
                                                )}
                                                {source.content_preview && (
                                                    <div className="text-muted-foreground text-xs italic">
                                                        "{source.content_preview}"
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </CollapsibleContent>
                            </Collapsible>
                        )}

                        {/* Debug информация */}
                        {!isUser && hasDebugInfo && (
                            <Collapsible open={showDebugInfo} onOpenChange={setShowDebugInfo}>
                                <CollapsibleTrigger asChild>
                                    <Button variant="ghost" size="sm" className="w-full justify-between p-0 h-auto mt-2">
                                        <span className="text-xs font-medium text-muted-foreground">
                                            🔍 Подробности поиска
                                        </span>
                                        {showDebugInfo ? (
                                            <ChevronDown className="w-3 h-3" />
                                        ) : (
                                            <ChevronRight className="w-3 h-3" />
                                        )}
                                    </Button>
                                </CollapsibleTrigger>
                                <CollapsibleContent className="mt-2">
                                    <div className="text-xs bg-background/50 rounded p-2 space-y-1">
                                        {debugInfo.namespace && (
                                            <div className="flex justify-between">
                                                <span className="text-muted-foreground">Namespace:</span>
                                                <span>{debugInfo.namespace}</span>
                                            </div>
                                        )}
                                        {debugInfo.collection_points_count && (
                                            <div className="flex justify-between">
                                                <span className="text-muted-foreground">Всего документов:</span>
                                                <span>{debugInfo.collection_points_count}</span>
                                            </div>
                                        )}
                                        {debugInfo.sources_found !== undefined && (
                                            <div className="flex justify-between">
                                                <span className="text-muted-foreground">Найдено источников:</span>
                                                <span>{debugInfo.sources_found}</span>
                                            </div>
                                        )}
                                        {debugInfo.similarity_cutoff && (
                                            <div className="flex justify-between">
                                                <span className="text-muted-foreground">Порог релевантности:</span>
                                                <span>{debugInfo.similarity_cutoff}</span>
                                            </div>
                                        )}
                                        {debugInfo.search_time_ms && (
                                            <div className="flex justify-between">
                                                <span className="text-muted-foreground">Время поиска:</span>
                                                <span>{debugInfo.search_time_ms.toFixed(2)}ms</span>
                                            </div>
                                        )}
                                    </div>
                                </CollapsibleContent>
                            </Collapsible>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
} 