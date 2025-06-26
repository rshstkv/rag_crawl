'use client';

import { apiClient, DocumentResponse, UploadResponse } from '@/lib/api';
import { useCallback, useEffect, useState } from 'react';

export function useDocuments(namespace?: string) {
    const [documents, setDocuments] = useState<DocumentResponse[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchDocuments = useCallback(async (ns?: string) => {
        setIsLoading(true);
        setError(null);

        try {
            const docs = await apiClient.getDocuments(ns || namespace);
            setDocuments(docs);
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Ошибка при загрузке документов';
            setError(errorMessage);
            console.error('Error fetching documents:', err);
        } finally {
            setIsLoading(false);
        }
    }, [namespace]);

    const uploadDocument = useCallback(async (
        file: File,
        targetNamespace?: string
    ): Promise<UploadResponse | null> => {
        if (!file) return null;

        setIsUploading(true);
        setError(null);

        try {
            const response = await apiClient.uploadDocument(file, targetNamespace || namespace || 'default');

            // Обновляем список документов после успешной загрузки
            await fetchDocuments(targetNamespace || namespace);

            return response;
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Ошибка при загрузке файла';
            setError(errorMessage);
            console.error('Error uploading document:', err);
            return null;
        } finally {
            setIsUploading(false);
        }
    }, [namespace, fetchDocuments]);

    const deleteDocument = useCallback(async (documentId: number): Promise<boolean> => {
        setError(null);

        try {
            await apiClient.deleteDocument(documentId);

            // Удаляем документ из локального состояния
            setDocuments(prev => prev.filter(doc => doc.id !== documentId));

            return true;
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Ошибка при удалении документа';
            setError(errorMessage);
            console.error('Error deleting document:', err);
            return false;
        }
    }, []);

    const refreshDocuments = useCallback(() => {
        fetchDocuments();
    }, [fetchDocuments]);

    // Автоматическая загрузка документов при изменении namespace
    useEffect(() => {
        fetchDocuments();
    }, [fetchDocuments]);

    return {
        documents,
        isLoading,
        isUploading,
        error,
        uploadDocument,
        deleteDocument,
        refreshDocuments,
        clearError: () => setError(null),
    };
} 