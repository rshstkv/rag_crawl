/**
 * API Client and type definitions for interacting with the RAG Crawl backend.
 */

// #region Type Definitions

export interface DocumentResponse {
    id: number;
    title: string;
    source_type: string;
    namespace: string;
    created_at: string;
    chunks_count: number;
}

export interface UploadResponse {
    id: number;
    title: string;
    namespace: string;
    message: string;
}

export interface DocumentChunk {
    id: number;
    document_id: number;
    content: string;
    vector_id: string;
    metadata?: Record<string, unknown>;
}

export interface DocumentContent {
    id: number;
    title: string;
    source_url?: string;
    source_type: string;
    content_hash: string;
    namespace: string;
    created_at: string;
    updated_at: string;
    chunks: DocumentChunk[];
}

export interface SystemDiagnostics {
    qdrant_info: {
        collection_name: string;
        points_count: number;
        vectors_count: number;
        status: string;
        config: {
            distance: string;
            size: number;
        };
    };
    db_info: {
        total_documents: number;
        total_chunks: number;
    };
    settings: Record<string, unknown>;
}

export interface ChatResponse {
    response: string;
    sources: Array<{
        document_title?: string;
        score?: number;
        content?: string;
        metadata?: Record<string, unknown>;
    }>;
    session_id?: string;
}

// #endregion

class ApiClient {
    private readonly baseUrl: string;

    constructor() {
        this.baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
    }

    private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
        const url = `${this.baseUrl}${endpoint}`;
        const headers = {
            ...options.headers,
        };

        try {
            const response = await fetch(url, { ...options, headers });

            if (!response.ok) {
                let errorData;
                try {
                    errorData = await response.json();
                } catch {
                    errorData = { detail: response.statusText };
                }
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API request failed: ${error}`);
            throw error;
        }
    }

    // Document Endpoints
    async getDocuments(namespace?: string): Promise<DocumentResponse[]> {
        const endpoint = namespace ? `/documents/?namespace=${namespace}` : "/documents/";
        return this.request<DocumentResponse[]>(endpoint);
    }

    async uploadDocument(file: File, namespace: string = "default"): Promise<UploadResponse> {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("namespace", namespace);

        return this.request<UploadResponse>("/documents/upload", {
            method: "POST",
            body: formData,
        });
    }

    async deleteDocument(documentId: number): Promise<{ message: string }> {
        return this.request<{ message: string }>(`/documents/${documentId}`, {
            method: "DELETE",
        });
    }

    async getDocumentContent(documentId: number): Promise<DocumentContent> {
        return this.request<DocumentContent>(`/documents/${documentId}/content`);
    }

    // Chat Endpoints
    async chat(message: string, namespace: string = "default", session_id?: string): Promise<ChatResponse> {
        return this.request<ChatResponse>('/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message, namespace, session_id }),
        });
    }


    // System Endpoints
    async getSystemDiagnostics(): Promise<SystemDiagnostics> {
        return this.request<SystemDiagnostics>("/documents/diagnostics");
    }
}

export const apiClient = new ApiClient(); 