import React, { useState, useEffect, useRef } from 'react';
import {
  ShieldCheck,
  LogOut,
  Upload,
  FileText,
  CheckCircle2,
  User,
  Loader2,
  AlertCircle,
  HardDrive,
  Download,
  Trash2,
  Eye,
  X,
  FileQuestion
} from 'lucide-react';
import {
  uploadFileApi,
  getFilesApi,
  downloadFileApi,
  deleteFileApi,
  getFileBlobApi
} from '../services/api';

export const Dashboard = ({ user, onLogout }) => {
  const [files, setFiles] = useState([]);
  const [isLoadingFiles, setIsLoadingFiles] = useState(true);
  const [fetchError, setFetchError] = useState(null);

  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(null);

  const [downloadingFileId, setDownloadingFileId] = useState(null);
  const [deletingFileId, setDeletingFileId] = useState(null);
  const [actionError, setActionError] = useState(null);
  const [actionSuccess, setActionSuccess] = useState(null);

  // File preview state
  const [previewFile, setPreviewFile] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState(null);
  const [previewData, setPreviewData] = useState(null);

  const fileInputRef = useRef(null);

  const fetchFiles = async () => {
    setIsLoadingFiles(true);
    setFetchError(null);
    const res = await getFilesApi();
    if (res.success && res.data?.files) {
      setFiles(res.data.files);
    } else {
      setFetchError(res.error?.message || 'Failed to load files.');
    }
    setIsLoadingFiles(false);
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  const handleFileChange = (e) => {
    setUploadError(null);
    setUploadSuccess(null);
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleChooseClick = () => {
    fileInputRef.current?.click();
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setUploadError('Please select a file to upload.');
      return;
    }

    setIsUploading(true);
    setUploadError(null);
    setUploadSuccess(null);
    setActionError(null);
    setActionSuccess(null);

    const res = await uploadFileApi(selectedFile);
    setIsUploading(false);

    if (res.success && res.data?.file) {
      setUploadSuccess(`"${selectedFile.name}" uploaded successfully!`);
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      fetchFiles();
    } else {
      setUploadError(res.error?.message || 'Upload failed. Please check server logs.');
    }
  };

  const handleDownload = async (file) => {
    setDownloadingFileId(file.id);
    setActionError(null);
    setActionSuccess(null);

    const res = await downloadFileApi(file.id, file.original_name);
    setDownloadingFileId(null);

    if (!res.success) {
      setActionError(res.error?.message || `Failed to download "${file.original_name}".`);
    }
  };

  const handleDelete = async (file) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${file.original_name}"?\nThis action will remove the file from storage and database permanently.`
    );
    if (!confirmed) return;

    setDeletingFileId(file.id);
    setActionError(null);
    setActionSuccess(null);

    const res = await deleteFileApi(file.id);
    setDeletingFileId(null);

    if (res.success) {
      setActionSuccess(`"${file.original_name}" was deleted successfully.`);
      fetchFiles();
    } else {
      setActionError(res.error?.message || `Failed to delete "${file.original_name}".`);
    }
  };

  const isSupportedPreview = (file) => {
    if (!file) return false;
    const name = (file.original_name || '').toLowerCase();
    const mime = (file.content_type || '').toLowerCase();

    // PDF documents
    if (mime === 'application/pdf' || name.endsWith('.pdf')) return true;

    // Image formats
    if (
      mime.startsWith('image/') ||
      name.endsWith('.png') ||
      name.endsWith('.jpg') ||
      name.endsWith('.jpeg') ||
      name.endsWith('.gif') ||
      name.endsWith('.webp') ||
      name.endsWith('.svg') ||
      name.endsWith('.bmp') ||
      name.endsWith('.ico')
    ) {
      return true;
    }

    // Plain text and code files
    if (
      mime.startsWith('text/') ||
      mime === 'application/json' ||
      name.endsWith('.txt') ||
      name.endsWith('.log') ||
      name.endsWith('.csv') ||
      name.endsWith('.json') ||
      name.endsWith('.md') ||
      name.endsWith('.py') ||
      name.endsWith('.js') ||
      name.endsWith('.jsx') ||
      name.endsWith('.ts') ||
      name.endsWith('.tsx') ||
      name.endsWith('.html') ||
      name.endsWith('.css') ||
      name.endsWith('.xml') ||
      name.endsWith('.yaml') ||
      name.endsWith('.yml') ||
      name.endsWith('.sh') ||
      name.endsWith('.sql')
    ) {
      return true;
    }

    return false;
  };

  const closePreview = () => {
    if (previewData?.url) {
      window.URL.revokeObjectURL(previewData.url);
    }
    setPreviewFile(null);
    setPreviewData(null);
    setPreviewError(null);
    setPreviewLoading(false);
  };

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && previewFile) {
        closePreview();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [previewFile, previewData]);

  const handlePreview = async (file) => {
    if (previewData?.url) {
      window.URL.revokeObjectURL(previewData.url);
    }
    setPreviewFile(file);
    setPreviewData(null);
    setPreviewError(null);

    if (!isSupportedPreview(file)) {
      setPreviewLoading(false);
      return;
    }

    setPreviewLoading(true);
    const res = await getFileBlobApi(file.id);
    setPreviewLoading(false);

    if (!res.success) {
      setPreviewError(res.error?.message || 'Failed to load file preview.');
      return;
    }

    const name = (file.original_name || '').toLowerCase();
    const mime = (res.contentType || file.content_type || '').toLowerCase();

    if (mime === 'application/pdf' || name.endsWith('.pdf')) {
      const pdfBlob = new Blob([res.blob], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(pdfBlob);
      setPreviewData({ type: 'pdf', url });
    } else if (
      mime.startsWith('image/') ||
      name.endsWith('.png') ||
      name.endsWith('.jpg') ||
      name.endsWith('.jpeg') ||
      name.endsWith('.gif') ||
      name.endsWith('.webp') ||
      name.endsWith('.svg') ||
      name.endsWith('.bmp') ||
      name.endsWith('.ico')
    ) {
      const imgBlob = new Blob([res.blob], { type: mime || 'image/png' });
      const url = window.URL.createObjectURL(imgBlob);
      setPreviewData({ type: 'image', url });
    } else {
      try {
        const text = await res.blob.text();
        setPreviewData({ type: 'text', text });
      } catch (err) {
        setPreviewError('Failed to decode text content.');
      }
    }
  };

  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Unknown';
    try {
      return new Date(dateStr).toLocaleString();
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="max-w-3xl w-full mx-auto px-4 py-8">
      {/* Top Header Card */}
      <header className="flex items-center justify-between pb-6 mb-8 border-b border-slate-800">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-gradient-to-br from-teal-500 to-emerald-600 rounded-xl shadow-lg shadow-teal-500/20">
            <ShieldCheck className="w-6 h-6 text-slate-950 font-bold" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white">IntelliVault</h1>
            <p className="text-xs text-slate-400">Secure Cloud Storage with Document AI</p>
          </div>
        </div>

        <button
          onClick={onLogout}
          className="flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700/80 transition-all shadow-sm active:scale-95"
        >
          <LogOut className="w-3.5 h-3.5 text-red-400" />
          <span>Logout</span>
        </button>
      </header>

      {/* User Welcome Card */}
      <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60 shadow-xl backdrop-blur-sm mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 rounded-lg bg-teal-500/10 border border-teal-500/30 text-teal-400">
            <User className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">
              Welcome, {user?.name || 'User'}
            </h2>
            <span className="text-xs text-slate-400">Authenticated Session</span>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t border-slate-800/80 text-sm">
          <div>
            <span className="block text-xs font-mono text-slate-400 uppercase tracking-wider mb-1">
              Email
            </span>
            <span className="font-mono text-slate-200">{user?.email}</span>
          </div>

          <div>
            <span className="block text-xs font-mono text-slate-400 uppercase tracking-wider mb-1">
              Account Status
            </span>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              <CheckCircle2 className="w-3 h-3" />
              {user?.status ? user.status.charAt(0).toUpperCase() + user.status.slice(1) : 'Active'}
            </span>
          </div>
        </div>
      </div>

      {/* File Upload Form Card */}
      <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60 shadow-xl backdrop-blur-sm mb-8">
        <div className="flex items-center gap-2 mb-4">
          <Upload className="w-4 h-4 text-teal-400" />
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">
            Upload File
          </h3>
        </div>

        {uploadError && (
          <div className="p-3 mb-4 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-400 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{uploadError}</span>
          </div>
        )}

        {uploadSuccess && (
          <div className="p-3 mb-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-400 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{uploadSuccess}</span>
          </div>
        )}

        <form onSubmit={handleUpload} className="flex flex-col sm:flex-row items-center gap-3">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            className="hidden"
          />

          <button
            type="button"
            onClick={handleChooseClick}
            disabled={isUploading}
            className="w-full sm:w-auto px-4 py-2.5 rounded-xl text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition shadow-sm active:scale-95 disabled:opacity-50"
          >
            Choose File
          </button>

          <div className="flex-1 text-xs text-slate-400 truncate w-full sm:w-auto text-center sm:text-left px-2">
            {selectedFile ? (
              <span className="text-slate-200 font-medium">
                {selectedFile.name}{' '}
                <span className="text-slate-400 font-normal">
                  ({formatBytes(selectedFile.size)})
                </span>
              </span>
            ) : (
              'No file chosen'
            )}
          </div>

          <button
            type="submit"
            disabled={!selectedFile || isUploading}
            className="w-full sm:w-auto flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold bg-gradient-to-r from-teal-500 to-emerald-600 hover:from-teal-400 hover:to-emerald-500 text-slate-950 transition-all shadow-md shadow-teal-500/20 active:scale-95 disabled:opacity-50 disabled:pointer-events-none"
          >
            {isUploading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Uploading...</span>
              </>
            ) : (
              <>
                <Upload className="w-3.5 h-3.5" />
                <span>Upload</span>
              </>
            )}
          </button>
        </form>
      </div>

      {/* My Files Section */}
      <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/40 shadow-xl">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <HardDrive className="w-4 h-4 text-teal-400" />
            <h3 className="text-base font-bold text-white tracking-tight">
              My Files ({files.length})
            </h3>
          </div>
          <button
            onClick={fetchFiles}
            disabled={isLoadingFiles}
            className="text-xs text-slate-400 hover:text-teal-400 transition"
          >
            Refresh
          </button>
        </div>

        {actionError && (
          <div className="p-3 mb-4 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-400 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{actionError}</span>
          </div>
        )}

        {actionSuccess && (
          <div className="p-3 mb-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-400 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{actionSuccess}</span>
          </div>
        )}

        {fetchError && (
          <div className="p-3 mb-4 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-400 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{fetchError}</span>
          </div>
        )}

        {isLoadingFiles ? (
          <div className="py-12 flex flex-col items-center justify-center text-center">
            <Loader2 className="w-6 h-6 animate-spin text-teal-400 mb-2" />
            <span className="text-xs text-slate-400">Loading your files...</span>
          </div>
        ) : files.length === 0 ? (
          /* Empty State */
          <div className="py-12 border-2 border-dashed border-slate-800/90 rounded-xl flex flex-col items-center justify-center text-center p-6">
            <div className="p-3 bg-slate-800/50 rounded-2xl mb-3 text-slate-500">
              <FileText className="w-8 h-8" />
            </div>
            <p className="text-sm font-medium text-slate-300">No files yet.</p>
            <p className="text-xs text-slate-500 max-w-sm mt-1">
              Select a file above and click Upload to store your documents in secure cloud storage.
            </p>
          </div>
        ) : (
          /* Files List */
          <div className="divide-y divide-slate-800/80">
            {files.map((file) => (
              <div
                key={file.id}
                className="py-3.5 px-2 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-800/20 rounded-xl transition"
              >
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  <div className="p-2 rounded-lg bg-teal-500/10 border border-teal-500/20 text-teal-400 shrink-0">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-slate-200 truncate" title={file.original_name}>
                      {file.original_name}
                    </p>
                    <div className="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
                      <span className="font-mono">{formatBytes(file.size)}</span>
                      <span>•</span>
                      <span className="truncate max-w-[140px] sm:max-w-[200px]">{file.content_type}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 sm:self-center shrink-0">
                  <span className="text-xs text-slate-400 hidden lg:inline mr-2">
                    {formatDate(file.created_at)}
                  </span>

                  <button
                    type="button"
                    onClick={() => handlePreview(file)}
                    disabled={downloadingFileId === file.id || deletingFileId === file.id}
                    title="Preview file"
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-teal-500/10 hover:bg-teal-500/20 text-teal-400 hover:text-teal-300 border border-teal-500/30 transition active:scale-95 disabled:opacity-50"
                  >
                    <Eye className="w-3.5 h-3.5 text-teal-400" />
                    <span>Preview</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleDownload(file)}
                    disabled={downloadingFileId === file.id || deletingFileId === file.id}
                    title="Download file"
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white border border-slate-700/80 transition active:scale-95 disabled:opacity-50"
                  >
                    {downloadingFileId === file.id ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin text-teal-400" />
                    ) : (
                      <Download className="w-3.5 h-3.5 text-teal-400" />
                    )}
                    <span>Download</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleDelete(file)}
                    disabled={downloadingFileId === file.id || deletingFileId === file.id}
                    title="Delete file"
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-red-500/10 hover:bg-red-500/20 text-red-400 hover:text-red-300 border border-red-500/30 transition active:scale-95 disabled:opacity-50"
                  >
                    {deletingFileId === file.id ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin text-red-400" />
                    ) : (
                      <Trash2 className="w-3.5 h-3.5" />
                    )}
                    <span>Delete</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* File Preview Modal */}
      {previewFile && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="relative w-full max-w-4xl max-h-[92vh] flex flex-col rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="flex items-center justify-between px-5 py-3.5 border-b border-slate-800 bg-slate-900/90">
              <div className="flex items-center gap-3 min-w-0">
                <div className="p-2 rounded-lg bg-teal-500/10 border border-teal-500/20 text-teal-400 shrink-0">
                  <Eye className="w-4 h-4" />
                </div>
                <div className="min-w-0">
                  <h3 className="text-sm font-semibold text-slate-100 truncate max-w-[200px] sm:max-w-md" title={previewFile.original_name}>
                    {previewFile.original_name}
                  </h3>
                  <div className="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
                    <span className="font-mono">{formatBytes(previewFile.size)}</span>
                    <span>•</span>
                    <span className="truncate max-w-[120px] sm:max-w-xs">{previewFile.content_type}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <button
                  type="button"
                  onClick={() => handleDownload(previewFile)}
                  className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white border border-slate-700/80 transition"
                  title="Download file"
                >
                  <Download className="w-3.5 h-3.5 text-teal-400" />
                  <span>Download</span>
                </button>
                <button
                  type="button"
                  onClick={closePreview}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 border border-transparent hover:border-slate-700 transition"
                  title="Close preview (Esc)"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Modal Body */}
            <div className="flex-1 p-4 sm:p-6 overflow-auto min-h-[320px] flex items-center justify-center bg-slate-950/60">
              {previewLoading ? (
                <div className="flex flex-col items-center justify-center py-16 gap-3 text-slate-400">
                  <Loader2 className="w-8 h-8 animate-spin text-teal-400" />
                  <p className="text-sm">Loading preview...</p>
                </div>
              ) : previewError ? (
                <div className="flex flex-col items-center justify-center py-10 text-center p-6 max-w-md">
                  <div className="p-3 bg-red-500/10 rounded-2xl mb-3 text-red-400 border border-red-500/20">
                    <AlertCircle className="w-8 h-8" />
                  </div>
                  <p className="text-sm font-medium text-red-300">Failed to load preview</p>
                  <p className="text-xs text-slate-400 mt-1 mb-4">{previewError}</p>
                  <button
                    type="button"
                    onClick={() => handleDownload(previewFile)}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-teal-500 hover:bg-teal-400 text-slate-950 transition shadow-lg shadow-teal-500/20"
                  >
                    <Download className="w-4 h-4" />
                    <span>Download File Instead</span>
                  </button>
                </div>
              ) : !isSupportedPreview(previewFile) ? (
                <div className="flex flex-col items-center justify-center py-10 text-center p-6 max-w-md">
                  <div className="p-3 bg-slate-800/80 rounded-2xl mb-3 text-slate-400 border border-slate-700">
                    <FileQuestion className="w-8 h-8 text-teal-400" />
                  </div>
                  <p className="text-sm font-semibold text-slate-200">
                    Preview not available for this file type.
                  </p>
                  <p className="text-xs text-slate-400 mt-1.5 mb-5 leading-relaxed">
                    This file format cannot be displayed in the browser. You can download the file to view it locally.
                  </p>
                  <button
                    type="button"
                    onClick={() => handleDownload(previewFile)}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-teal-500 hover:bg-teal-400 text-slate-950 transition shadow-lg shadow-teal-500/20"
                  >
                    <Download className="w-4 h-4" />
                    <span>Download File</span>
                  </button>
                </div>
              ) : previewData?.type === 'pdf' ? (
                <div className="w-full h-[70vh]">
                  <iframe
                    src={previewData.url}
                    title={previewFile.original_name}
                    className="w-full h-full rounded-xl border border-slate-800 bg-slate-950"
                  />
                </div>
              ) : previewData?.type === 'image' ? (
                <div className="flex items-center justify-center w-full max-h-[70vh]">
                  <img
                    src={previewData.url}
                    alt={previewFile.original_name}
                    className="max-h-[68vh] max-w-full object-contain rounded-xl shadow-lg border border-slate-800"
                  />
                </div>
              ) : previewData?.type === 'text' ? (
                <div className="w-full h-[70vh] flex flex-col">
                  <pre className="flex-1 p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-slate-200 overflow-auto whitespace-pre-wrap select-text leading-relaxed">
                    {previewData.text}
                  </pre>
                </div>
              ) : null}
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-between px-5 py-3 border-t border-slate-800 bg-slate-900/90">
              <div className="text-xs text-slate-500">
                IntelliVault Document Viewer
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => handleDownload(previewFile)}
                  className="flex sm:hidden items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white border border-slate-700/80 transition"
                >
                  <Download className="w-3.5 h-3.5 text-teal-400" />
                  <span>Download</span>
                </button>
                <button
                  type="button"
                  onClick={closePreview}
                  className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/80 transition"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
