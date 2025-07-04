'use client';

import { apiClient } from '@/lib/api';
import { useCallback, useState } from 'react';

export interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    sources?: Array<{
        document_title?: string;
        source_type?: string;
        score?: number;
        document_id?: number;
        chunk_index?: number;
        content_preview?: string;
        content?: string;
        metadata?: Record<string, unknown>;
    }>;
    debugInfo?: {
        collection_points_count?: number;
        similarity_cutoff?: number;
        search_time_ms?: number;
        namespace?: string;
        sources_found?: number;
    };
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
            const response = await apiClient.chat(content.trim(), namespace, sessionId);

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

    // sendQuery закомментирован, так как метода query нет в apiClient
    /*
    const sendQuery = useCallback(async (content: string) => {
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
            const response = await apiClient.query(content.trim(), namespace);

            const assistantMessage: Message = {
                id: Math.random().toString(36),
                role: 'assistant',
                content: response.response,
                sources: response.sources,
                debugInfo: response.debug_info,
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
    }, [namespace, isLoading]);
    */

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
        // sendQuery,
        clearChat,
        changeNamespace,
    };
} 