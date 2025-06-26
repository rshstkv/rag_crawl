'use client';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { useChat } from '@/hooks/use-chat';
import { Bot, RefreshCw, Send, Trash2 } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { MessageItem } from './message-item';

interface ChatInterfaceProps {
    namespace?: string;
    onNamespaceChange?: (namespace: string) => void;
}

export function ChatInterface({ namespace = 'default', onNamespaceChange }: ChatInterfaceProps) {
    const [inputValue, setInputValue] = useState('');
    const {
        messages,
        isLoading,
        error,
        sendMessage,
        clearChat,
        changeNamespace
    } = useChat(namespace);

    const scrollAreaRef = useRef<HTMLDivElement>(null);

    // Автоскролл к последнему сообщению
    useEffect(() => {
        if (scrollAreaRef.current) {
            const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
            if (scrollContainer) {
                scrollContainer.scrollTop = scrollContainer.scrollHeight;
            }
        }
    }, [messages]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!inputValue.trim() || isLoading) return;

        await sendMessage(inputValue);
        setInputValue('');
    };

    const handleNamespaceChange = (newNamespace: string) => {
        changeNamespace(newNamespace);
        onNamespaceChange?.(newNamespace);
    };

    return (
        <Card className="flex flex-col h-full">
            <CardHeader className="pb-4">
                <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                        <Bot className="w-5 h-5" />
                        RAG Crawl Chat
                    </CardTitle>
                    <div className="flex items-center gap-2">
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={clearChat}
                            disabled={messages.length === 0}
                        >
                            <Trash2 className="w-4 h-4" />
                            Очистить
                        </Button>
                    </div>
                </div>

                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <span>Namespace:</span>
                    <Input
                        value={namespace}
                        onChange={(e) => handleNamespaceChange(e.target.value)}
                        className="w-32 h-7"
                        placeholder="default"
                    />
                </div>

                {error && (
                    <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
                        {error}
                    </div>
                )}
            </CardHeader>

            <CardContent className="flex-1 flex flex-col gap-4 p-0">
                <ScrollArea
                    ref={scrollAreaRef}
                    className="flex-1 px-6"
                >
                    <div className="space-y-4 pb-4">
                        {messages.length === 0 ? (
                            <div className="text-center text-muted-foreground py-8">
                                <Bot className="w-12 h-12 mx-auto mb-4 opacity-50" />
                                <p>Начните диалог с вашими документами</p>
                                <p className="text-sm mt-2">
                                    Задайте вопрос, и я найду ответ в загруженных документах
                                </p>
                            </div>
                        ) : (
                            messages.map((message) => (
                                <MessageItem key={message.id} message={message} />
                            ))
                        )}

                        {isLoading && (
                            <div className="flex items-center gap-2 text-muted-foreground">
                                <RefreshCw className="w-4 h-4 animate-spin" />
                                <span>Обрабатываю запрос...</span>
                            </div>
                        )}
                    </div>
                </ScrollArea>

                <Separator />

                <form onSubmit={handleSubmit} className="px-6 pb-6">
                    <div className="flex gap-2">
                        <Input
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            placeholder="Задайте вопрос по документам..."
                            disabled={isLoading}
                            className="flex-1"
                        />
                        <Button
                            type="submit"
                            disabled={!inputValue.trim() || isLoading}
                            size="sm"
                        >
                            <Send className="w-4 h-4" />
                        </Button>
                    </div>
                </form>
            </CardContent>
        </Card>
    );
} 