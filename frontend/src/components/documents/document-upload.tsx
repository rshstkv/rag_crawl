'use client';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { useDocuments } from '@/hooks/use-documents';
import { AlertCircle, CheckCircle, File, Upload, X } from 'lucide-react';
import { useRef, useState } from 'react';

interface DocumentUploadProps {
    namespace?: string;
    onUploadSuccess?: () => void;
}

export function DocumentUpload({ namespace = 'default', onUploadSuccess }: DocumentUploadProps) {
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [uploadResult, setUploadResult] = useState<string | null>(null);
    const [isSuccess, setIsSuccess] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const { uploadDocument, isUploading, error, clearError } = useDocuments(namespace);

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            setSelectedFile(file);
            setUploadResult(null);
            setIsSuccess(false);
            clearError();
        }
    };

    const handleUpload = async () => {
        if (!selectedFile) return;

        const result = await uploadDocument(selectedFile, namespace);

        if (result) {
            setUploadResult(result.message);
            setIsSuccess(true);
            setSelectedFile(null);
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
            onUploadSuccess?.();
        } else {
            setIsSuccess(false);
        }
    };

    const clearSelection = () => {
        setSelectedFile(null);
        setUploadResult(null);
        setIsSuccess(false);
        clearError();
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const formatFileSize = (bytes: number) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Upload className="w-5 h-5" />
                    Загрузка документов
                </CardTitle>
            </CardHeader>

            <CardContent className="space-y-4">
                {/* Выбор файла */}
                <div>
                    <Input
                        ref={fileInputRef}
                        type="file"
                        accept=".txt,.pdf,.docx,.md"
                        onChange={handleFileSelect}
                        disabled={isUploading}
                        className="cursor-pointer"
                    />
                    <div className="text-xs text-muted-foreground mt-1">
                        Поддерживаются: .txt, .pdf, .docx, .md (макс. 100MB)
                    </div>
                </div>

                {/* Информация о выбранном файле */}
                {selectedFile && (
                    <Card className="bg-muted/50">
                        <CardContent className="p-3">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2 flex-1 min-w-0">
                                    <File className="w-4 h-4 text-blue-500 flex-shrink-0" />
                                    <div className="flex-1 min-w-0">
                                        <div className="font-medium truncate">{selectedFile.name}</div>
                                        <div className="text-xs text-muted-foreground">
                                            {formatFileSize(selectedFile.size)}
                                        </div>
                                    </div>
                                </div>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={clearSelection}
                                    disabled={isUploading}
                                >
                                    <X className="w-4 h-4" />
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Результат загрузки */}
                {uploadResult && (
                    <Card className={isSuccess ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}>
                        <CardContent className="p-3">
                            <div className="flex items-center gap-2">
                                {isSuccess ? (
                                    <CheckCircle className="w-4 h-4 text-green-600" />
                                ) : (
                                    <AlertCircle className="w-4 h-4 text-red-600" />
                                )}
                                <span className={`text-sm ${isSuccess ? 'text-green-800' : 'text-red-800'}`}>
                                    {uploadResult}
                                </span>
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Ошибка */}
                {error && (
                    <Card className="bg-red-50 border-red-200">
                        <CardContent className="p-3">
                            <div className="flex items-center gap-2">
                                <AlertCircle className="w-4 h-4 text-red-600" />
                                <span className="text-sm text-red-800">{error}</span>
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Кнопка загрузки */}
                <Button
                    onClick={handleUpload}
                    disabled={!selectedFile || isUploading}
                    className="w-full"
                >
                    {isUploading ? (
                        <>
                            <Upload className="w-4 h-4 mr-2 animate-pulse" />
                            Загружаем...
                        </>
                    ) : (
                        <>
                            <Upload className="w-4 h-4 mr-2" />
                            Загрузить документ
                        </>
                    )}
                </Button>

                <div className="text-xs text-muted-foreground">
                    Namespace: <code className="bg-muted px-1 py-0.5 rounded">{namespace}</code>
                </div>
            </CardContent>
        </Card>
    );
} 