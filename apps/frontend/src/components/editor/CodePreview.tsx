import type { FileContentResponse } from '@/types/chat';

interface CodePreviewProps {
  file?: FileContentResponse | null;
  loading: boolean;
}

export function CodePreview({ file, loading }: CodePreviewProps) {
  return (
    <div className="code-preview">
      <div className="code-preview__body">
        {loading ? (
          <p>加载中...</p>
        ) : file ? (
          <pre>
            <code>{file.content}</code>
          </pre>
        ) : (
          <p>请选择文件查看内容。</p>
        )}
      </div>
    </div>
  );
}
