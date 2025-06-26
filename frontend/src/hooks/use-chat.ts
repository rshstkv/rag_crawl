'use client';

import { apiClient, ChatRequest, ChatResponse } from '@/lib/api';
import { useCallback, useState } from 'react';

export interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    sources?: ChatResponse['sources'];
    timestamp: Date;
}

export function useChat(initialNamespace?: string) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [namespace, setNamespace] = useState(initialNamespace || 'default');
    const [sessionId] = useState(() =>
        typeof window !== 'undefined'
            ? window.crypto.randomUUID()
            : Math.random().toString(36)
    );

    const sendMessage = useCallback(async (content: string) => {
        if (!content.trim() || isLoading) return;

        const userMessage: Message = {
            id: Math.random().toString(36),
            role: 'user',
            content: content.trim(),
            timestamp: new Date(),
        };

        setMessages(prev => [...prev, userMessage]);
        setIsLoading(true);
        setError(null);

        try {
            const request: ChatRequest = {
                message: content.trim(),
                namespace,
                session_id: sessionId,
            };

            const response = await apiClient.chat(request);

            const assistantMessage: Message = {
                id: Math.random().toString(36),
                role: 'assistant',
                content: response.response,
                sources: response.sources,
                timestamp: new Date(),
            };

            setMessages(prev => [...prev, assistantMessage]);
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Произошла ошибка';
            setError(errorMessage);

            const errorAssistantMessage: Message = {
                id: Math.random().toString(36),
                role: 'assistant',
                content: `❌ Ошибка: ${errorMessage}`,
                timestamp: new Date(),
            };

            setMessages(prev => [...prev, errorAssistantMessage]);
        } finally {
            setIsLoading(false);
        }
    }, [namespace, sessionId, isLoading]);

    const clearChat = useCallback(() => {
        setMessages([]);
        setError(null);
    }, []);

    const changeNamespace = useCallback((newNamespace: string) => {
        setNamespace(newNamespace);
        setMessages([]);
        setError(null);
    }, []);

    return {
        messages,
        isLoading,
        error,
        namespace,
        sessionId,
        sendMessage,
        clearChat,
        changeNamespace,
    };
} 