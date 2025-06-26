'use client';

import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Card, CardContent } from '@/components/ui/card';
import { Message } from '@/hooks/use-chat';
import { formatDistance } from 'date-fns';
import { ru } from 'date-fns/locale';
import { Bot, ExternalLink, User } from 'lucide-react';

interface MessageItemProps {
    message: Message;
}

export function MessageItem({ message }: MessageItemProps) {
    const isUser = message.role === 'user';
    const timestamp = formatDistance(message.timestamp, new Date(), {
        addSuffix: true,
        locale: ru
    });

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

                        {/* Источники для ответов ассистента */}
                        {!isUser && message.sources && message.sources.length > 0 && (
                            <div className="mt-3 pt-3 border-t border-border/50">
                                <div className="text-xs font-medium mb-2 text-muted-foreground">
                                    📚 Источники:
                                </div>
                                <div className="space-y-1">
                                    {message.sources.map((source, index) => (
                                        <div key={index} className="text-xs flex items-center gap-1">
                                            <ExternalLink className="w-3 h-3 flex-shrink-0" />
                                            <span className="flex-1">
                                                {source.document_title || 'Документ'}
                                                {source.score && (
                                                    <span className="ml-1 text-muted-foreground">
                                                        (релевантность: {(source.score * 100).toFixed(1)}%)
                                                    </span>
                                                )}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
} 