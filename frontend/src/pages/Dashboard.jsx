import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import UploadDialog from "@/components/UploadDialog";
import { toast } from "sonner";
import {
    Plus,
    MagnifyingGlass,
    FileText,
    FilePdf,
    FileDoc,
    FileXls,
    FilePpt,
    Image as ImageIcon,
    CheckCircle,
    Clock,
    XCircle,
    Trash,
    ChatCircle,
    ArrowClockwise,
} from "@phosphor-icons/react";

const IconForFile = ({ filename }) => {
    const ext = (filename || "").split(".").pop().toLowerCase();
    if (ext === "pdf") return <FilePdf size={22} weight="duotone" className="text-destructive" />;
    if (ext === "docx") return <FileDoc size={22} weight="duotone" className="text-brand-primary" />;
    if (ext === "pptx") return <FilePpt size={22} weight="duotone" className="text-confidence-medium" />;
    if (ext === "xlsx" || ext === "csv") return <FileXls size={22} weight="duotone" className="text-confidence-high" />;
    if (["png", "jpg", "jpeg"].includes(ext)) return <ImageIcon size={22} weight="duotone" className="text-brand-accent" />;
    return <FileText size={22} weight="duotone" className="text-muted-foreground" />;
};

const StatusBadge = ({ status }) => {
    if (status === "ready") return <span className="inline-flex items-center gap-1 text-xs font-mono text-confidence-high"><CheckCircle size={14} weight="fill" /> READY</span>;
    if (status === "failed") return <span className="inline-flex items-center gap-1 text-xs font-mono text-confidence-low"><XCircle size={14} weight="fill" /> FAILED</span>;
    return <span className="inline-flex items-center gap-1 text-xs font-mono text-confidence-medium"><Clock size={14} weight="fill" /> {String(status).toUpperCase()}</span>;
};

export default function Dashboard() {
    const [docs, setDocs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [q, setQ] = useState("");
    const [uploadOpen, setUploadOpen] = useState(false);
    const [selected, setSelected] = useState([]);

    const load = async () => {
        try {
            const r = await api.get("/v2/documents", { params: q ? { q } : {} });
            setDocs(r.data);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { load(); }, []);
    useEffect(() => {
        const id = setTimeout(load, 200);
        return () => clearTimeout(id);
    }, [q]);

    // Poll processing docs
    useEffect(() => {
        const processing = docs.filter((d) => d.status !== "ready" && d.status !== "failed");
        if (processing.length === 0) return;
        const id = setInterval(async () => {
            try {
                const updates = await Promise.all(
                    processing.map((d) => api.get(`/v2/documents/${d.id}/processing-status`).then((r) => ({ id: d.id, ...r.data })).catch(() => null))
                );
                setDocs((cur) =>
                    cur.map((d) => {
                        const u = updates.find((x) => x?.id === d.id);
                        return u ? { ...d, status: u.status, progress: u.progress, chunk_count: u.chunk_count, error: u.error } : d;
                    })
                );
            } catch {}
        }, 2500);
        return () => clearInterval(id);
    }, [docs]);

    const toggle = (id) => setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));

    const del = async (d) => {
        if (!window.confirm(`Delete "${d.filename}"? This removes the file and all embeddings.`)) return;
        try {
            await api.delete(`/v2/documents/${d.id}`);
            toast.success("Document deleted");
            setDocs((c) => c.filter((x) => x.id !== d.id));
        } catch (e) {
            toast.error(e?.response?.data?.detail || "Delete failed");
        }
    };

    const retry = async (d) => {
        try {
            await api.post(`/v2/documents/${d.id}/reprocess`);
            toast.success(`Retrying "${d.filename}"…`);
            setDocs((c) => c.map((x) => x.id === d.id ? { ...x, status: "queued", progress: 5, error: null } : x));
        } catch (e) {
            toast.error(e?.response?.data?.detail || "Retry failed");
        }
    };

    const chatSelected = () => {
        const ready = docs.filter((d) => selected.includes(d.id) && d.status === "ready");
        if (!ready.length) { toast.error("Select at least one ready document"); return; }
        const params = new URLSearchParams({ docs: ready.map((r) => r.id).join(",") });
        window.location.href = `/app/chat?${params}`;
    };

    return (
        <div>
            <header className="h-16 border-b border-border px-8 flex items-center justify-between sticky top-0 bg-background z-10">
                <div>
                    <div className="dc-overline">Workspace</div>
                    <h1 className="font-heading font-bold text-lg">Documents</h1>
                </div>
                <div className="flex items-center gap-3">
                    {selected.length > 0 && (
                        <>
                            <span className="text-sm text-muted-foreground" data-testid="selection-count">{selected.length} selected</span>
                            <Button variant="outline" onClick={chatSelected} data-testid="chat-selected-button">
                                <ChatCircle size={16} /> Chat with selected
                            </Button>
                        </>
                    )}
                    <Button onClick={() => setUploadOpen(true)} data-testid="upload-open-button">
                        <Plus size={16} /> Upload
                    </Button>
                </div>
            </header>

            <div className="p-8 max-w-7xl">
                <div className="flex items-center gap-3 mb-6">
                    <div className="relative flex-1 max-w-md">
                        <MagnifyingGlass size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                        <Input
                            placeholder="Search documents…"
                            className="pl-9 h-10"
                            value={q}
                            onChange={(e) => setQ(e.target.value)}
                            data-testid="document-search-input"
                        />
                    </div>
                    <Link to="/app/chat">
                        <Button variant="ghost" data-testid="chat-all-button">
                            <ChatCircle size={16} /> Chat with all
                        </Button>
                    </Link>
                </div>

                {loading && <div className="text-sm text-muted-foreground">Loading documents…</div>}

                {!loading && docs.length === 0 && (
                    <div className="border border-dashed border-border p-16 text-center" data-testid="empty-documents">
                        <FileText size={40} weight="duotone" className="mx-auto text-muted-foreground" />
                        <h2 className="font-heading font-bold text-xl mt-4">No documents yet</h2>
                        <p className="text-sm text-muted-foreground mt-2 max-w-md mx-auto">
                            Upload a PDF, DOCX, PPTX, XLSX, CSV, image, or text file to start chatting with it.
                        </p>
                        <Button className="mt-6" onClick={() => setUploadOpen(true)} data-testid="empty-upload-button">
                            <Plus size={16} /> Upload document
                        </Button>
                    </div>
                )}

                {!loading && docs.length > 0 && (
                    <div className="border border-border">
                        <div className="hidden md:grid grid-cols-[36px_1fr_200px_110px_100px_80px_40px] gap-4 px-4 py-3 bg-secondary/50 border-b border-border text-xs font-mono uppercase tracking-wider text-muted-foreground">
                            <div></div>
                            <div>File</div>
                            <div>Status</div>
                            <div>Pages / Chunks</div>
                            <div>Tags</div>
                            <div>Size</div>
                            <div></div>
                        </div>
                        {docs.map((d) => (
                            <div
                                key={d.id}
                                className="md:grid md:grid-cols-[36px_1fr_200px_110px_100px_80px_40px] gap-4 px-4 py-3 border-b border-border last:border-b-0 hover:bg-secondary/30 transition-colors items-center"
                                data-testid={`document-row-${d.id}`}
                            >
                                <input
                                    type="checkbox"
                                    checked={selected.includes(d.id)}
                                    onChange={() => toggle(d.id)}
                                    className="w-4 h-4 accent-brand-primary cursor-pointer"
                                    disabled={d.status !== "ready"}
                                    data-testid={`document-checkbox-${d.id}`}
                                />
                                <div className="flex items-center gap-3 min-w-0">
                                    <IconForFile filename={d.filename} />
                                    <div className="min-w-0">
                                        <div className="font-medium truncate">{d.filename}</div>
                                        <div className="text-xs text-muted-foreground">{new Date(d.created_at).toLocaleDateString()}</div>
                                    </div>
                                </div>
                            <div className="flex items-center gap-2 min-w-0">
                                    <div>
                                        <StatusBadge status={d.status} />
                                        {d.status !== "ready" && d.status !== "failed" && (
                                            <Progress value={d.progress || 0} className="h-1 mt-1 w-28" />
                                        )}
                                        {d.status === "failed" && d.error && (
                                            <div className="text-[10px] text-confidence-low mt-0.5 truncate max-w-[180px]" title={d.error}>
                                                {d.error.length > 50 ? d.error.slice(0, 50) + "…" : d.error}
                                            </div>
                                        )}
                                    </div>
                                    {d.status === "failed" && (
                                        <Button
                                            size="icon"
                                            variant="ghost"
                                            className="h-7 w-7 shrink-0"
                                            onClick={() => retry(d)}
                                            title="Retry ingestion"
                                        >
                                            <ArrowClockwise size={14} className="text-confidence-medium" />
                                        </Button>
                                    )}
                                </div>
                                <div className="text-sm font-mono">
                                    {d.page_count || 0} / {d.chunk_count || 0}
                                </div>
                                <div className="flex flex-wrap gap-1">
                                    {(d.tags || []).slice(0, 2).map((t) => (
                                        <Badge key={t} variant="outline" className="text-[10px] font-mono uppercase">{t}</Badge>
                                    ))}
                                </div>
                                <div className="text-xs font-mono text-muted-foreground">{(d.size / 1024).toFixed(0)}KB</div>
                                <Button variant="ghost" size="icon" onClick={() => del(d)} data-testid={`document-delete-${d.id}`}>
                                    <Trash size={16} />
                                </Button>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            <UploadDialog open={uploadOpen} onOpenChange={setUploadOpen} onUploaded={load} />
        </div>
    );
}
